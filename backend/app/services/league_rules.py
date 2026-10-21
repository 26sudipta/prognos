"""Growth Points: the pure rules behind the weekly classroom league.

No database, no I/O, no clock reads. Everything here is a function of its inputs,
so every rule in docs/classroom_v2_plan.md §5 has a unit test. The DB side lives in
`app.workers.league_sync`; the read side in `app.services.league`.

Changing any constant below changes scores, so bump SCORING_VERSION with it. Each
weekly row stores the version that produced it.
"""

from __future__ import annotations

import functools
import math
from collections.abc import Iterable
from dataclasses import dataclass, field
from datetime import UTC, date, datetime, time, timedelta
from zoneinfo import ZoneInfo, available_timezones

SCORING_VERSION = 1

# ── Reference level (§5.1) ────────────────────────────────────────────────────
LEVEL_FLOOR = 800  # CF problem ratings start at 800
PEAK_WINDOW = timedelta(days=180)
PEAK_DISCOUNT = 150  # r = max(current, recent peak - 150)
UNRATED_WINDOW = timedelta(days=90)
UNRATED_MIN_SOLVES = 10
UNRATED_PERCENTILE = 0.70

# ── Bands (§5.2): (name, lowest Δ in band, points); checked from the top down ──
BANDS: tuple[tuple[str, int, int], ...] = (
    ("reach", 300, 12),
    ("stretch", 100, 10),
    ("at_level", -100, 6),
    ("practice", -300, 3),
)
WARMUP = ("warmup", 1)  # Δ < -300
UNRATED = ("unrated", 2)  # no CF rating (gym, or not rated yet)
WARMUP_WEEKLY_CAP = 10
STRETCH_BANDS = frozenset({"stretch", "reach"})

# ── Bonuses (§5.3) ────────────────────────────────────────────────────────────
LIVE_TYPES = frozenset({"CONTESTANT", "OUT_OF_COMPETITION"})
VIRTUAL_TYPE = "VIRTUAL"
PRACTICE_TYPES = frozenset({"PRACTICE", "UNKNOWN"})  # UNKNOWN scores like practice
LIVE_MULTIPLIER = 1.5  # applied to non-warm-up band points, rounded up
RATED_CONTEST_BONUS = 8
OTHER_CONTEST_BONUS = 5  # unrated, out-of-competition, gym or virtual
OTHER_CONTEST_WEEKLY_MAX = 2
UPSOLVE_BONUS = 4
UPSOLVE_WINDOW = timedelta(days=14)
SOLVE_DAY_BONUS = 2
SOLVE_DAY_MAX = 5  # two rest days a week cost nothing
SOLVE_DAY_MIN_DELTA = -300  # a warm-up-only day doesn't count

# ── Weeks and brackets (§5.5) ─────────────────────────────────────────────────
FINALIZE_GRACE = timedelta(hours=48)  # late syncs and late CF problem ratings land
SINGLE_BRACKET_MAX = 20
BRACKET_TARGET_SIZE = 12


# ═════════════════════════════════════════════════════════════════════════════
# Reference level
# ═════════════════════════════════════════════════════════════════════════════


def reference_level(
    rating_points: Iterable[tuple[datetime, int]],
    recent_solve_ratings: Iterable[int],
    as_of: datetime,
) -> int:
    """A student's level `r` as of `as_of` (the week's start, in UTC).

    rating_points: (time, rating after that contest) from the rating history.
    recent_solve_ratings: CF ratings of distinct problems first solved in the 90 days
    before `as_of`. Only used for students with no rating yet.
    """
    history = sorted((t, r) for t, r in rating_points if t < as_of)
    if history:
        current = history[-1][1]
        recent = [r for t, r in history if t >= as_of - PEAK_WINDOW]
        level = max(current, max(recent) - PEAK_DISCOUNT) if recent else current
        return max(LEVEL_FLOOR, level)

    solves = sorted(recent_solve_ratings)
    if len(solves) >= UNRATED_MIN_SOLVES:
        idx = math.ceil(UNRATED_PERCENTILE * len(solves)) - 1  # nearest-rank percentile
        return max(LEVEL_FLOOR, solves[idx])
    return LEVEL_FLOOR


# ═════════════════════════════════════════════════════════════════════════════
# Bands
# ═════════════════════════════════════════════════════════════════════════════


def band_for(problem_rating: int | None, level: int) -> tuple[str, int]:
    """(band name, base points) for one solve."""
    if problem_rating is None:
        return UNRATED
    delta = problem_rating - level
    for name, lowest, points in BANDS:
        if delta >= lowest:
            return name, points
    return WARMUP


# ═════════════════════════════════════════════════════════════════════════════
# Weeks
# ═════════════════════════════════════════════════════════════════════════════


@functools.cache
def _known_zones() -> frozenset[str]:
    return frozenset(available_timezones())


def is_valid_timezone(tz: str) -> bool:
    """True for IANA zone names the server can actually load (needs tzdata)."""
    return tz in _known_zones()


def week_start_for(moment: datetime, tz: str, week_starts_on: int) -> date:
    """Local date the week containing `moment` starts on, in the class's zone."""
    local_day = moment.astimezone(ZoneInfo(tz)).date()
    return local_day - timedelta(days=(local_day.weekday() - week_starts_on) % 7)


def week_window(week_start: date, tz: str) -> tuple[datetime, datetime]:
    """UTC [start, end) for a local week. Built from local midnights, so DST weeks
    come out 167 or 169 hours long, exactly as the class experiences them."""
    zone = ZoneInfo(tz)
    start = datetime.combine(week_start, time.min, tzinfo=zone)
    end = datetime.combine(week_start + timedelta(days=7), time.min, tzinfo=zone)
    return start.astimezone(UTC), end.astimezone(UTC)


# ═════════════════════════════════════════════════════════════════════════════
# Scoring one student's week
# ═════════════════════════════════════════════════════════════════════════════


@dataclass(frozen=True)
class Solve:
    """A first-ever individual AC on a problem (team ACs never reach here)."""

    problem_key: str
    rating: int | None
    participant_type: str
    contest_id: int | None
    solved_at: datetime


@dataclass(frozen=True)
class Participation:
    """A contest the student took part in: any live or virtual submission in it."""

    contest_id: int
    participant_type: str
    first_at: datetime
    last_at: datetime


@dataclass
class WeekScore:
    growth_points: int = 0
    stretch_solves: int = 0
    breakdown: dict[str, int] = field(default_factory=dict)


def score_week(
    *,
    level: int,
    solves: Iterable[Solve],
    participations: Iterable[Participation],
    rated_contest_ids: set[int],
    window: tuple[datetime, datetime],
    tz: str,
) -> WeekScore:
    """Growth Points for one student's week.

    solves: first-ever individual ACs whose time falls inside `window`.
    participations: contests with live/virtual submissions from `window[0] - 14 days`
        to `window[1]` (the earlier ones only matter for upsolves).
    rated_contest_ids: every contest in the student's rating history.
    """
    start, end = window
    zone = ZoneInfo(tz)
    parts = list(participations)
    pts: dict[str, int] = {
        "warmup": 0,
        "practice": 0,
        "at_level": 0,
        "stretch": 0,
        "reach": 0,
        "unrated": 0,
        "live_bonus": 0,
        "contests": 0,
        "upsolves": 0,
        "solve_days": 0,
    }
    counts = {
        "solves": 0,
        "stretch_solves": 0,
        "rated_contests": 0,
        "other_contests": 0,
        "upsolve_count": 0,
        "solve_day_count": 0,
    }
    solve_days: set[date] = set()

    for solve in sorted(solves, key=lambda s: s.solved_at):
        if not (start <= solve.solved_at < end):
            continue
        band, base = band_for(solve.rating, level)
        counts["solves"] += 1
        if band in STRETCH_BANDS:
            counts["stretch_solves"] += 1

        if band == "warmup":
            pts["warmup"] = min(WARMUP_WEEKLY_CAP, pts["warmup"] + base)
        else:
            pts[band] += base
            if solve.participant_type in LIVE_TYPES:
                pts["live_bonus"] += math.ceil(base * LIVE_MULTIPLIER) - base
            elif solve.participant_type in PRACTICE_TYPES and _is_upsolve(solve, parts):
                pts["upsolves"] += UPSOLVE_BONUS
                counts["upsolve_count"] += 1

        if band == "unrated" or (solve.rating - level) >= SOLVE_DAY_MIN_DELTA:
            solve_days.add(solve.solved_at.astimezone(zone).date())

    # Contests: rated rounds always count; everything else is capped. A contest
    # belongs to the week it started in, so a round past midnight counts once.
    in_week = [p for p in parts if start <= p.first_at < end]
    rated = {
        p.contest_id
        for p in in_week
        if p.participant_type in LIVE_TYPES and p.contest_id in rated_contest_ids
    }
    others = {p.contest_id for p in in_week} - rated
    counts["rated_contests"] = len(rated)
    counts["other_contests"] = min(len(others), OTHER_CONTEST_WEEKLY_MAX)
    pts["contests"] = (
        len(rated) * RATED_CONTEST_BONUS + counts["other_contests"] * OTHER_CONTEST_BONUS
    )

    counts["solve_day_count"] = min(len(solve_days), SOLVE_DAY_MAX)
    pts["solve_days"] = counts["solve_day_count"] * SOLVE_DAY_BONUS

    total = sum(pts.values())
    return WeekScore(
        growth_points=total,
        stretch_solves=counts["stretch_solves"],
        breakdown={**pts, **counts},
    )


def _is_upsolve(solve: Solve, participations: list[Participation]) -> bool:
    """A practice AC on a problem from a contest the student played within the 14 days
    before it. It's a first-ever AC, so it wasn't solved during that contest."""
    if solve.contest_id is None:
        return False
    return any(
        p.contest_id == solve.contest_id
        and p.last_at < solve.solved_at <= p.last_at + UPSOLVE_WINDOW
        for p in participations
    )


# ═════════════════════════════════════════════════════════════════════════════
# Brackets and ranks
# ═════════════════════════════════════════════════════════════════════════════


def assign_brackets(levels: dict[str, int]) -> dict[str, int]:
    """Bracket number (1 = lowest levels) for each student, contiguous by level.

    20 or fewer students share one bracket. Otherwise brackets of about 12, with
    sizes within one of each other. Ties in level break on the id, so the result
    never depends on dict order.
    """
    ordered = sorted(levels, key=lambda uid: (levels[uid], uid))
    n = len(ordered)
    if n <= SINGLE_BRACKET_MAX:
        return {uid: 1 for uid in ordered}
    k = max(2, round(n / BRACKET_TARGET_SIZE))
    size, extra = divmod(n, k)
    out: dict[str, int] = {}
    i = 0
    for b in range(1, k + 1):
        take = size + (1 if b <= extra else 0)
        for uid in ordered[i : i + take]:
            out[uid] = b
        i += take
    return out


def place_in_bracket(level: int, ranges: dict[int, tuple[int, int]]) -> int:
    """Bracket for someone joining mid-week: the one whose level range contains
    theirs, else the nearest. `ranges` maps bracket -> (min level, max level)."""
    if not ranges:
        return 1

    def distance(b: int) -> int:
        lo, hi = ranges[b]
        return 0 if lo <= level <= hi else min(abs(level - lo), abs(level - hi))

    return min(ranges, key=lambda b: (distance(b), b))


def rank_entries(entries: list[tuple[str, int, int]]) -> dict[str, int]:
    """Competition ranks (1, 2, 2, 4) from (id, growth_points, stretch_solves).
    Equal GP and equal stretch solves share a rank."""
    ordered = sorted(entries, key=lambda e: (-e[1], -e[2], e[0]))
    ranks: dict[str, int] = {}
    prev_key = None
    prev_rank = 0
    for position, (uid, gp, stretch) in enumerate(ordered, start=1):
        key = (gp, stretch)
        rank = prev_rank if key == prev_key else position
        ranks[uid] = rank
        prev_key, prev_rank = key, rank
    return ranks
