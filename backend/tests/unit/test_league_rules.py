"""Unit tests for the Growth Points rules (docs/classroom_v2_plan.md §5, §10.7)."""

from datetime import UTC, date, datetime, timedelta

import pytest

from app.services import league_rules as R
from app.services.league_rules import Participation, Solve

T0 = datetime(2026, 10, 12, 0, 0, tzinfo=UTC)  # a Monday
WEEK = (T0, T0 + timedelta(days=7))


def solve(rating, *, ptype="PRACTICE", at=None, key=None, contest=1900):
    at = at or T0 + timedelta(days=1)
    return Solve(key or f"{contest}{rating}", rating, ptype, contest, at)


def score(level, solves=(), parts=(), rated=frozenset(), tz="UTC"):
    return R.score_week(
        level=level,
        solves=solves,
        participations=parts,
        rated_contest_ids=set(rated),
        window=WEEK,
        tz=tz,
    )


# ── Bands ─────────────────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    "delta, band, points",
    [
        (-301, "warmup", 1),
        (-300, "practice", 3),
        (-101, "practice", 3),
        (-100, "at_level", 6),
        (99, "at_level", 6),
        (100, "stretch", 10),
        (299, "stretch", 10),
        (300, "reach", 12),
        (900, "reach", 12),
    ],
)
def test_band_boundaries(delta, band, points):
    assert R.band_for(1500 + delta, 1500) == (band, points)


def test_unrated_problem_scores_flat():
    assert R.band_for(None, 1500) == ("unrated", 2)


def test_warmup_cap_is_exactly_ten():
    eleven = [solve(800, key=f"w{i}", at=T0 + timedelta(hours=i)) for i in range(11)]
    result = score(1400, eleven)
    assert result.breakdown["warmup"] == 10
    assert result.breakdown["solves"] == 11


# ── Multipliers and contest types ─────────────────────────────────────────────


@pytest.mark.parametrize(
    "ptype, extra",
    [
        ("CONTESTANT", 5),
        ("OUT_OF_COMPETITION", 5),
        ("PRACTICE", 0),
        ("VIRTUAL", 0),
    ],
)
def test_live_multiplier_only_for_live_types(ptype, extra):
    result = score(1500, [solve(1600, ptype=ptype)])  # stretch, base 10
    assert result.breakdown["stretch"] == 10
    assert result.breakdown["live_bonus"] == extra


def test_live_multiplier_rounds_up():
    result = score(1500, [solve(1300, ptype="CONTESTANT")])  # practice band, base 3
    assert result.breakdown["live_bonus"] == 2  # ceil(4.5) - 3


def test_warmups_never_get_the_multiplier():
    result = score(1500, [solve(800, ptype="CONTESTANT")])
    assert result.breakdown["warmup"] == 1 and result.breakdown["live_bonus"] == 0


# ── Reference level ───────────────────────────────────────────────────────────


def test_level_is_current_rating_when_at_peak():
    history = [(T0 - timedelta(days=30), 1400), (T0 - timedelta(days=10), 1500)]
    assert R.reference_level(history, [], T0) == 1500


def test_peak_rule_after_a_200_point_slide():
    history = [(T0 - timedelta(days=40), 1700), (T0 - timedelta(days=5), 1500)]
    assert R.reference_level(history, [], T0) == 1550  # 1700 - 150


def test_old_peak_outside_180_days_is_ignored():
    history = [(T0 - timedelta(days=400), 2000), (T0 - timedelta(days=5), 1500)]
    assert R.reference_level(history, [], T0) == 1500


def test_rating_after_week_start_is_not_used():
    history = [(T0 - timedelta(days=5), 1200), (T0 + timedelta(days=2), 1600)]
    assert R.reference_level(history, [], T0) == 1200


def test_unrated_with_nine_vs_ten_solves():
    assert R.reference_level([], [1200] * 9, T0) == 800
    ten = [800, 900, 1000, 1100, 1200, 1300, 1400, 1500, 1600, 1700]
    assert R.reference_level([], ten, T0) == 1400  # nearest-rank 70th percentile


def test_level_floor_is_800():
    assert R.reference_level([(T0 - timedelta(days=3), 420)], [], T0) == 800


# ── Weeks ─────────────────────────────────────────────────────────────────────


def test_week_start_in_dhaka():
    # Sunday 20:00 UTC is Monday 02:00 in Dhaka, so it's already the next week.
    moment = datetime(2026, 10, 18, 20, 0, tzinfo=UTC)
    assert R.week_start_for(moment, "Asia/Dhaka", 0) == date(2026, 10, 19)
    assert R.week_start_for(moment, "UTC", 0) == date(2026, 10, 12)


def test_week_window_dhaka_is_utc_shifted():
    start, end = R.week_window(date(2026, 10, 19), "Asia/Dhaka")
    assert start == datetime(2026, 10, 18, 18, 0, tzinfo=UTC)
    assert end - start == timedelta(days=7)


@pytest.mark.parametrize(
    "week_start, hours",
    [
        (date(2026, 2, 23), 168),  # an ordinary week
        (date(2026, 3, 2), 167),  # contains spring forward, Mar 8
        (date(2026, 10, 31), 169),  # contains fall back, Nov 1
    ],
)
def test_week_window_across_dst(week_start, hours):
    start, end = R.week_window(week_start, "America/New_York")
    assert end - start == timedelta(hours=hours)


def test_week_starts_on_sunday():
    wednesday = datetime(2026, 10, 14, 12, 0, tzinfo=UTC)
    assert R.week_start_for(wednesday, "UTC", 6) == date(2026, 10, 11)


# ── Solve days ────────────────────────────────────────────────────────────────


def test_solve_days_use_local_dates():
    late = T0 + timedelta(days=1, hours=17, minutes=59)  # 23:59 Dhaka
    early = T0 + timedelta(days=1, hours=18, minutes=1)  # 00:01 Dhaka, next day
    result = score(
        1500, [solve(1500, at=late, key="a"), solve(1500, at=early, key="b")], tz="Asia/Dhaka"
    )
    assert result.breakdown["solve_day_count"] == 2


def test_warmup_only_day_earns_no_solve_day():
    assert score(1500, [solve(1000)]).breakdown["solve_day_count"] == 0


def test_sixth_solve_day_earns_nothing():
    six = [solve(1500, key=f"d{i}", at=T0 + timedelta(days=i, hours=1)) for i in range(6)]
    result = score(1500, six)
    assert result.breakdown["solve_day_count"] == 5
    assert result.breakdown["solve_days"] == 10


def test_unrated_solves_count_as_solve_days():
    assert score(1500, [solve(None)]).breakdown["solve_day_count"] == 1


# ── Upsolves ──────────────────────────────────────────────────────────────────

ROUND = Participation(
    1900, "CONTESTANT", T0 - timedelta(days=1), T0 - timedelta(days=1) + timedelta(hours=2)
)


def test_in_contest_ac_is_not_an_upsolve():
    result = score(
        1500, [solve(1500, ptype="CONTESTANT", at=ROUND.first_at + timedelta(minutes=30))], [ROUND]
    )
    assert result.breakdown["upsolve_count"] == 0


@pytest.mark.parametrize("days_after, counts", [(1, True), (14, True), (15, False)])
def test_upsolve_window_is_14_days(days_after, counts):
    at = ROUND.last_at + timedelta(days=days_after)
    window = (T0, T0 + timedelta(days=30))
    result = R.score_week(
        level=1500,
        solves=[solve(1500, at=at)],
        participations=[ROUND],
        rated_contest_ids=set(),
        window=window,
        tz="UTC",
    )
    assert (result.breakdown["upsolve_count"] == 1) is counts


def test_virtual_solve_is_not_an_upsolve():
    virtual = Participation(
        1900, "VIRTUAL", T0 + timedelta(days=2), T0 + timedelta(days=2, hours=2)
    )
    result = score(
        1500,
        [solve(1500, ptype="VIRTUAL", at=virtual.first_at + timedelta(minutes=40))],
        [ROUND, virtual],
    )
    assert result.breakdown["upsolve_count"] == 0


def test_practice_solve_before_the_contest_is_not_an_upsolve():
    later_round = Participation(
        1900, "CONTESTANT", T0 + timedelta(days=3), T0 + timedelta(days=3, hours=2)
    )
    result = score(1500, [solve(1500, at=T0 + timedelta(days=1))], [later_round])
    assert result.breakdown["upsolve_count"] == 0


def test_upsolve_from_a_different_contest_does_not_count():
    result = score(1500, [solve(1500, contest=1901)], [ROUND])
    assert result.breakdown["upsolve_count"] == 0


# ── Contests ──────────────────────────────────────────────────────────────────


def test_rated_and_other_contests():
    rated = Participation(
        1950, "CONTESTANT", T0 + timedelta(days=1), T0 + timedelta(days=1, hours=2)
    )
    ooc = Participation(
        1951, "OUT_OF_COMPETITION", T0 + timedelta(days=2), T0 + timedelta(days=2, hours=2)
    )
    virt = Participation(1952, "VIRTUAL", T0 + timedelta(days=3), T0 + timedelta(days=3, hours=2))
    gym = Participation(
        104000, "CONTESTANT", T0 + timedelta(days=4), T0 + timedelta(days=4, hours=2)
    )
    result = score(1500, parts=[rated, ooc, virt, gym], rated={1950})
    assert result.breakdown["rated_contests"] == 1
    assert result.breakdown["other_contests"] == 2  # capped at 2 of 3
    assert result.breakdown["contests"] == 8 + 2 * 5


def test_contest_past_midnight_counts_in_the_week_it_started():
    late = Participation(1960, "CONTESTANT", T0 - timedelta(hours=1), T0 + timedelta(hours=1))
    assert score(1500, parts=[late], rated={1960}).breakdown["rated_contests"] == 0


# ── Whole-week totals ─────────────────────────────────────────────────────────


def test_total_is_sum_of_breakdown_and_first_ever_rules_live_upstream():
    solves = [
        solve(1600, ptype="CONTESTANT", at=T0 + timedelta(days=1, hours=1), key="A", contest=1950),
        solve(1500, at=T0 + timedelta(days=2), key="B", contest=1950),  # upsolve, at level
        solve(800, at=T0 + timedelta(days=3), key="C"),  # warm-up
    ]
    part = Participation(
        1950, "CONTESTANT", T0 + timedelta(days=1), T0 + timedelta(days=1, hours=2)
    )
    result = score(1500, solves, [part], rated={1950})
    b = result.breakdown
    assert b["stretch"] == 10 and b["live_bonus"] == 5
    assert b["at_level"] == 6 and b["upsolves"] == 4
    assert b["warmup"] == 1 and b["contests"] == 8 and b["solve_days"] == 4
    assert result.growth_points == 10 + 5 + 6 + 4 + 1 + 8 + 4
    assert result.stretch_solves == 1


def test_solves_outside_the_window_are_ignored():
    assert score(1500, [solve(1600, at=T0 - timedelta(minutes=1))]).growth_points == 0


# ── Brackets and ranks ────────────────────────────────────────────────────────


def test_twenty_students_share_one_bracket():
    assert set(R.assign_brackets({f"u{i}": 1000 + i for i in range(20)}).values()) == {1}


def test_twenty_one_students_make_two_brackets():
    out = R.assign_brackets({f"u{i:02d}": 1000 + i for i in range(21)})
    assert sorted(list(out.values()).count(b) for b in (1, 2)) == [10, 11]
    assert out["u00"] == 1 and out["u20"] == 2  # contiguous, low levels first


def test_150_students_get_even_brackets():
    out = R.assign_brackets({f"u{i:03d}": 800 + 10 * i for i in range(150)})
    sizes = [list(out.values()).count(b) for b in set(out.values())]
    assert len(sizes) == 12 and max(sizes) - min(sizes) <= 1


def test_bracket_assignment_is_deterministic_on_ties():
    levels = {"b": 1200, "a": 1200, **{f"x{i:02d}": 1000 for i in range(20)}}
    assert R.assign_brackets(levels) == R.assign_brackets(dict(reversed(list(levels.items()))))


def test_mid_week_joiner_placement():
    ranges = {1: (800, 1100), 2: (1150, 1400)}
    assert R.place_in_bracket(1000, ranges) == 1
    assert R.place_in_bracket(1300, ranges) == 2
    assert R.place_in_bracket(1120, ranges) == 1  # in a gap: nearest edge
    assert R.place_in_bracket(2000, ranges) == 2
    assert R.place_in_bracket(1500, {}) == 1


def test_competition_ranking_with_ties():
    ranks = R.rank_entries([("a", 40, 2), ("b", 40, 2), ("c", 50, 0), ("d", 40, 1), ("e", 0, 0)])
    assert ranks == {"c": 1, "a": 2, "b": 2, "d": 4, "e": 5}
