"""Read side of the Weekly Growth League (Classroom v2 Slice 1, docs/phase_6_1.md).

Reads `classroom_weekly_scores` and shapes it per viewer. The only write is the
inline rebuild in `_ensure_league`, which follows the same rule as the leaderboard:
the free tier has no broker, so a read rebuilds when the cache is missing, stale,
behind a member's newer sync, or holding a week that is due to finalize.
"""

from __future__ import annotations

import logging
import statistics
import uuid
from collections import defaultdict
from datetime import UTC, date, datetime, timedelta

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.classroom import (
    Classroom,
    ClassroomLeaderboard,
    ClassroomMembership,
    ClassroomMembershipRole,
    ClassroomWeeklyScore,
)
from app.models.user import User
from app.models.user_handle import UserHandle
from app.schemas.classroom import (
    LeagueBracket,
    LeagueEntry,
    LeagueHistoryResponse,
    LeagueHistoryWeek,
    LeagueMe,
    LeaguePulse,
    LeagueResponse,
    LeagueSuggestion,
    LeagueTarget,
    LeagueZeroGp,
)
from app.services import league_rules as R
from app.services.analytics import get_recommendations
from app.services.classroom import (
    _assert_member,
    _classroom_syncing,
    _get_classroom_or_404,
    _identity,
    _max_member_sync,
    _record_visit,
)
from app.workers.league_sync import rebuild_league

logger = logging.getLogger(__name__)

LEAGUE_TTL = timedelta(minutes=10)
HISTORY_MAX_WEEKS = 26


# ── Freshness ─────────────────────────────────────────────────────────────────


async def _ensure_league(db: AsyncSession, classroom: Classroom, now: datetime) -> None:
    current = R.week_start_for(now, classroom.timezone, classroom.week_starts_on)
    newest = await db.scalar(
        select(func.max(ClassroomWeeklyScore.computed_at)).where(
            ClassroomWeeklyScore.classroom_id == classroom.id,
            ClassroomWeeklyScore.week_start == current,
        )
    )
    stale = newest is None or now - newest > LEAGUE_TTL
    behind = False
    if not stale:
        max_sync = await _max_member_sync(db, classroom.id)
        behind = max_sync is not None and max_sync > newest

    due = False
    if not stale and not behind:
        oldest_live = await db.scalar(
            select(func.min(ClassroomWeeklyScore.week_start)).where(
                ClassroomWeeklyScore.classroom_id == classroom.id,
                ClassroomWeeklyScore.status == "live",
                ClassroomWeeklyScore.week_start < current,
            )
        )
        if oldest_live is not None:
            _, end = R.week_window(oldest_live, classroom.timezone)
            due = now >= end + R.FINALIZE_GRACE

    if stale or behind or due:
        try:
            await rebuild_league(db, classroom.id, now=now)
        except Exception:
            logger.exception("inline league rebuild failed for %s", classroom.id)


# ── League view ───────────────────────────────────────────────────────────────


def _parse_week(week: str | None, classroom: Classroom, now: datetime) -> date:
    if week in (None, "", "current"):
        return R.week_start_for(now, classroom.timezone, classroom.week_starts_on)
    try:
        day = date.fromisoformat(week)
    except ValueError:
        raise HTTPException(
            status_code=422,
            detail="week must be 'current' or a date like 2026-10-12",
        ) from None
    # Any date inside a week selects that week.
    return day - timedelta(days=(day.weekday() - classroom.week_starts_on) % 7)


async def _week_rows(db: AsyncSession, classroom_id: uuid.UUID, week_start: date):
    result = await db.execute(
        select(ClassroomWeeklyScore, User, ClassroomMembership.alias_no, UserHandle.handle)
        .join(User, User.id == ClassroomWeeklyScore.user_id)
        .join(
            ClassroomMembership,
            (ClassroomMembership.classroom_id == ClassroomWeeklyScore.classroom_id)
            & (ClassroomMembership.user_id == ClassroomWeeklyScore.user_id),
        )
        .outerjoin(
            UserHandle,
            (UserHandle.user_id == ClassroomWeeklyScore.user_id)
            & UserHandle.is_verified.is_(True)
            & UserHandle.is_active.is_(True),
        )
        .where(
            ClassroomWeeklyScore.classroom_id == classroom_id,
            ClassroomWeeklyScore.week_start == week_start,
        )
        .execution_options(populate_existing=True)
    )
    seen: set[uuid.UUID] = set()
    out = []
    for row, user, alias_no, handle in result.all():
        if row.user_id in seen:  # defensive: one row per member even with duplicate handles
            continue
        seen.add(row.user_id)
        out.append((row, user, alias_no, handle))
    return out


def _contests(row: ClassroomWeeklyScore) -> int:
    b = row.breakdown or {}
    return int(b.get("rated_contests", 0)) + int(b.get("other_contests", 0))


async def get_league(
    db: AsyncSession, classroom_id: uuid.UUID, user_id: uuid.UUID, week: str | None = None
) -> LeagueResponse:
    classroom = await _get_classroom_or_404(db, classroom_id)
    viewer = await _assert_member(db, classroom_id, user_id)
    is_teacher = viewer.role == ClassroomMembershipRole.TEACHER
    now = datetime.now(UTC)

    await _ensure_league(db, classroom, now)
    week_start = _parse_week(week, classroom, now)
    start, end = R.week_window(week_start, classroom.timezone)

    rows = await _week_rows(db, classroom_id, week_start)
    prev_rows = await _week_rows(db, classroom_id, week_start - timedelta(days=7))
    prev_gp = {r.user_id: r.growth_points for r, *_ in prev_rows}

    def identity(member_id, user, alias_no, handle):
        return _identity(
            visibility=classroom.member_visibility,
            viewer_is_teacher=is_teacher,
            viewer_id=user_id,
            member_id=member_id,
            name=user.name,
            handle=handle,
            avatar_url=user.avatar_url,
            alias_no=alias_no,
        )

    entries_by_bracket: dict[int, list[LeagueEntry]] = defaultdict(list)
    levels_by_bracket: dict[int, list[int]] = defaultdict(list)
    my_row = None
    for row, user, alias_no, handle in rows:
        name, shown_handle, avatar = identity(row.user_id, user, alias_no, handle)
        entries_by_bracket[row.bracket].append(
            LeagueEntry(
                rank=row.rank_in_bracket,
                user_id=row.user_id,
                display_name=name,
                cf_handle=shown_handle,
                avatar_url=avatar,
                growth_points=row.growth_points,
                stretch_solves=row.stretch_solves,
                contests=_contests(row),
                delta_vs_last_week=(
                    row.growth_points - prev_gp[row.user_id] if row.user_id in prev_gp else None
                ),
                is_me=row.user_id == user_id,
                ref_rating=row.ref_rating if is_teacher else None,
            )
        )
        levels_by_bracket[row.bracket].append(row.ref_rating)
        if row.user_id == user_id:
            my_row = row

    brackets = []
    for b in sorted(entries_by_bracket):
        if not is_teacher and (my_row is None or b != my_row.bracket):
            continue  # students see only their own bracket (plan D-2)
        entries = sorted(entries_by_bracket[b], key=lambda e: (e.rank, e.display_name))
        brackets.append(
            LeagueBracket(
                bracket=b,
                rating_min=min(levels_by_bracket[b]),
                rating_max=max(levels_by_bracket[b]),
                size=len(entries),
                active_count=sum(1 for e in entries if e.growth_points > 0),
                entries=entries,
            )
        )

    me = None
    suggestions: list[LeagueSuggestion] = []
    if my_row is not None:
        me = await _me(db, classroom_id, user_id, my_row, entries_by_bracket[my_row.bracket])
        suggestions = await _suggestions(db, user_id, my_row.ref_rating)

    pulse = _pulse(rows, prev_rows, identity) if is_teacher and rows else None
    if pulse is not None:
        await attach_last_active(db, classroom_id, pulse)

    statuses = {r.status for r, *_ in rows}
    week_status = "empty" if not rows else ("final" if statuses == {"final"} else "live")
    closed = now >= end
    response = LeagueResponse(
        classroom_id=classroom.id,
        week_start=week_start,
        week_end=week_start + timedelta(days=7),
        status=week_status,
        closes_in_seconds=max(0, int((end - now).total_seconds())),
        finalizes_at=end + R.FINALIZE_GRACE if closed and week_status == "live" else None,
        timezone=classroom.timezone,
        week_starts_on=classroom.week_starts_on,
        scoring_version=R.SCORING_VERSION,
        me=me,
        brackets=brackets,
        pulse=pulse,
        suggestions=suggestions,
        computed_at=max((r.computed_at for r, *_ in rows), default=None),
        syncing=await _classroom_syncing(db, classroom_id),
    )
    await _record_visit(db, classroom_id, user_id)
    return response


async def _me(db, classroom_id, user_id, row, bracket_entries: list[LeagueEntry]) -> LeagueMe:
    past = (
        await db.execute(
            select(ClassroomWeeklyScore.week_start, ClassroomWeeklyScore.growth_points)
            .where(
                ClassroomWeeklyScore.classroom_id == classroom_id,
                ClassroomWeeklyScore.user_id == user_id,
                ClassroomWeeklyScore.week_start < row.week_start,
            )
            .order_by(ClassroomWeeklyScore.week_start.desc())
        )
    ).all()
    last4 = [gp for _, gp in past[:4]]

    mine = next(e for e in bracket_entries if e.is_me)
    above = [e for e in bracket_entries if e.growth_points > mine.growth_points]
    target = min(above, key=lambda e: (e.growth_points, e.display_name)) if above else None
    tied = [
        e.display_name
        for e in bracket_entries
        if not e.is_me
        and e.growth_points == mine.growth_points
        and e.stretch_solves == mine.stretch_solves
        and mine.growth_points > 0
    ]
    return LeagueMe(
        growth_points=row.growth_points,
        rank_in_bracket=row.rank_in_bracket,
        bracket=row.bracket,
        ref_rating=row.ref_rating,
        breakdown={k: int(v) for k, v in (row.breakdown or {}).items()},
        avg_last_4_weeks=round(statistics.fmean(last4), 1) if last4 else None,
        weeks_counted=len(last4),
        best_week_gp=max((gp for _, gp in past), default=None),
        next_target=(
            LeagueTarget(
                display_name=target.display_name, gp_gap=target.growth_points - mine.growth_points
            )
            if target
            else None
        ),
        tied_with=sorted(tied),
    )


async def _suggestions(db: AsyncSession, user_id: uuid.UUID, level: int) -> list[LeagueSuggestion]:
    """Up to 3 next problems from the existing recommendation engine, priced in GP."""
    rec_set = await get_recommendations(db, user_id)
    if rec_set is None:
        return []
    out = []
    for rec in rec_set.recommendations[:3]:
        rating = rec.difficulty or None
        band, base = R.band_for(rating, level)
        out.append(
            LeagueSuggestion(
                problem_id=rec.problem_id,
                problem_name=rec.problem_name,
                rating=rating,
                url=rec.url,
                tag=rec.tag,
                band=band,
                gp=base,
            )
        )
    return out


def _pulse(rows, prev_rows, identity) -> LeaguePulse:
    def totals(rs):
        gps = [r.growth_points for r, *_ in rs]
        return {
            "active": sum(1 for g in gps if g > 0),
            "median": float(statistics.median(gps)) if gps else 0.0,
            "stretch": sum(r.stretch_solves for r, *_ in rs),
            "contests": sum(_contests(r) for r, *_ in rs),
        }

    now_t = totals(rows)
    prev_t = totals(prev_rows) if prev_rows else None

    zero = []
    for row, user, alias_no, handle in rows:
        if row.growth_points == 0:
            name, shown_handle, _ = identity(row.user_id, user, alias_no, handle)
            zero.append((row, name, shown_handle))
    return LeaguePulse(
        active_members=now_t["active"],
        total_members=len(rows),
        median_gp=now_t["median"],
        stretch_solves=now_t["stretch"],
        contests=now_t["contests"],
        prev_active_members=prev_t["active"] if prev_t else None,
        prev_median_gp=prev_t["median"] if prev_t else None,
        prev_stretch_solves=prev_t["stretch"] if prev_t else None,
        prev_contests=prev_t["contests"] if prev_t else None,
        zero_gp=[
            LeagueZeroGp(
                user_id=row.user_id,
                display_name=name,
                cf_handle=handle,
                bracket=row.bracket,
                last_active_at=None,
            )
            for row, name, handle in zero
        ],
    )


async def attach_last_active(db: AsyncSession, classroom_id: uuid.UUID, pulse: LeaguePulse) -> None:
    """Fill zero_gp[].last_active_at from the leaderboard cache, longest-quiet first."""
    if not pulse.zero_gp:
        return
    ids = [z.user_id for z in pulse.zero_gp]
    rows = await db.execute(
        select(ClassroomLeaderboard.user_id, ClassroomLeaderboard.last_active_at).where(
            ClassroomLeaderboard.classroom_id == classroom_id,
            ClassroomLeaderboard.user_id.in_(ids),
        )
    )
    last = dict(rows.all())
    for z in pulse.zero_gp:
        z.last_active_at = last.get(z.user_id)
    epoch = datetime.min.replace(tzinfo=UTC)
    pulse.zero_gp.sort(key=lambda z: (z.last_active_at or epoch, z.display_name))


# ── History ───────────────────────────────────────────────────────────────────


async def get_league_history(
    db: AsyncSession, classroom_id: uuid.UUID, user_id: uuid.UUID, weeks: int = 8
) -> LeagueHistoryResponse:
    await _get_classroom_or_404(db, classroom_id)
    viewer = await _assert_member(db, classroom_id, user_id)
    is_teacher = viewer.role == ClassroomMembershipRole.TEACHER
    weeks = max(1, min(weeks, HISTORY_MAX_WEEKS))

    starts = (
        (
            await db.execute(
                select(ClassroomWeeklyScore.week_start)
                .where(ClassroomWeeklyScore.classroom_id == classroom_id)
                .group_by(ClassroomWeeklyScore.week_start)
                .order_by(ClassroomWeeklyScore.week_start.desc())
                .limit(weeks)
            )
        )
        .scalars()
        .all()
    )
    if not starts:
        return LeagueHistoryResponse(weeks=[])

    rows = (
        await db.execute(
            select(
                ClassroomWeeklyScore.week_start,
                ClassroomWeeklyScore.user_id,
                ClassroomWeeklyScore.growth_points,
                ClassroomWeeklyScore.status,
            ).where(
                ClassroomWeeklyScore.classroom_id == classroom_id,
                ClassroomWeeklyScore.week_start.in_(starts),
            )
        )
    ).all()
    by_week: dict[date, list] = defaultdict(list)
    for ws, uid, gp, st in rows:
        by_week[ws].append((uid, gp, st))

    out = []
    for ws in sorted(by_week):
        items = by_week[ws]
        mine = next((gp for uid, gp, _ in items if uid == user_id), None)
        out.append(
            LeagueHistoryWeek(
                week_start=ws,
                status="final" if all(st == "final" for *_, st in items) else "live",
                my_gp=mine,
                # Students compare with their own past here, not the class (plan P4).
                class_median=float(statistics.median(gp for _, gp, _ in items))
                if is_teacher
                else None,
            )
        )
    return LeagueHistoryResponse(weeks=out)
