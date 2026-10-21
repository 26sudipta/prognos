"""Weekly Growth League rebuild (Classroom v2 Slice 1, docs/phase_6_1.md).

DB-only: reads submissions, rating history and the cf_problems catalogue, never
Codeforces. The scoring rules themselves live in `app.services.league_rules`; this
module only gathers their inputs and writes `classroom_weekly_scores`.
"""

from __future__ import annotations

import logging
import uuid
from collections import defaultdict
from datetime import UTC, date, datetime

from sqlalchemy import and_, delete, func, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.analytics import CfProblem, RatingHistory, Submission
from app.models.classroom import (
    Classroom,
    ClassroomMembership,
    ClassroomMembershipRole,
    ClassroomWeeklyScore,
)
from app.models.user_handle import HandlePlatform, UserHandle
from app.services import league_rules as R

logger = logging.getLogger(__name__)

PARTICIPATION_TYPES = tuple(R.LIVE_TYPES | {R.VIRTUAL_TYPE})


async def rebuild_league(
    session: AsyncSession, classroom_id: uuid.UUID, *, now: datetime | None = None
) -> int:
    """Rebuild the current week, plus any older week that is still `live`.

    Older live weeks are rescored until `FINALIZE_GRACE` after they close (late syncs,
    late CF problem ratings), then written one last time as `final`. Returns the
    number of rows written. Commits.
    """
    now = now or datetime.now(UTC)
    classroom = (
        await session.execute(
            select(Classroom)
            .where(Classroom.id == classroom_id)
            .execution_options(populate_existing=True)
        )
    ).scalar_one_or_none()
    if classroom is None or not classroom.is_active:
        return 0

    current = R.week_start_for(now, classroom.timezone, classroom.week_starts_on)
    older_live = (
        (
            await session.execute(
                select(ClassroomWeeklyScore.week_start)
                .where(
                    ClassroomWeeklyScore.classroom_id == classroom_id,
                    ClassroomWeeklyScore.status == "live",
                    ClassroomWeeklyScore.week_start < current,
                )
                .distinct()
            )
        )
        .scalars()
        .all()
    )

    written = 0
    for week_start in sorted(older_live):
        _, end = R.week_window(week_start, classroom.timezone)
        written += await _build_week(
            session, classroom, week_start, now=now, final=now >= end + R.FINALIZE_GRACE
        )
    written += await _build_week(session, classroom, current, now=now, final=False)
    await session.commit()
    return written


async def _build_week(
    session: AsyncSession,
    classroom: Classroom,
    week_start: date,
    *,
    now: datetime,
    final: bool,
) -> int:
    tz = classroom.timezone
    start, end = R.week_window(week_start, tz)

    existing = {
        row.user_id: row
        for row in (
            await session.execute(
                select(ClassroomWeeklyScore)
                .where(
                    ClassroomWeeklyScore.classroom_id == classroom.id,
                    ClassroomWeeklyScore.week_start == week_start,
                )
                .execution_options(populate_existing=True)
            )
        ).scalars()
    }
    if any(row.status == "final" for row in existing.values()):
        return 0  # final rows never change

    members = await _student_handles(session, classroom.id)
    # Members who left: their live rows go with them.
    gone = [uid for uid in existing if uid not in members]
    if gone:
        await session.execute(
            delete(ClassroomWeeklyScore).where(
                ClassroomWeeklyScore.classroom_id == classroom.id,
                ClassroomWeeklyScore.week_start == week_start,
                ClassroomWeeklyScore.user_id.in_(gone),
            )
        )
    if not members:
        return 0

    handle_ids = list(members.values())
    history = await _rating_history(session, handle_ids)
    firsts = await _first_solves(session, handle_ids, since=start - R.UNRATED_WINDOW, until=end)
    participations = await _participations(
        session, handle_ids, since=start - R.UPSOLVE_WINDOW, until=end
    )

    # 1. Levels: frozen for anyone already scored this week.
    levels: dict[uuid.UUID, int] = {}
    for uid, hid in members.items():
        if uid in existing:
            levels[uid] = existing[uid].ref_rating
            continue
        recent = [s.rating for s in firsts[hid] if s.rating is not None and s.solved_at < start]
        levels[uid] = R.reference_level([(t, r) for _, r, t in history[hid]], recent, as_of=start)

    # 2. Brackets: frozen too. Newcomers join the nearest existing bracket.
    brackets: dict[uuid.UUID, int] = {}
    if existing:
        ranges: dict[int, tuple[int, int]] = {}
        for row in existing.values():
            if row.user_id in members:
                lo, hi = ranges.get(row.bracket, (row.ref_rating, row.ref_rating))
                ranges[row.bracket] = (min(lo, row.ref_rating), max(hi, row.ref_rating))
        for uid in members:
            brackets[uid] = (
                existing[uid].bracket
                if uid in existing
                else R.place_in_bracket(levels[uid], ranges)
            )
    else:
        assigned = R.assign_brackets({str(uid): lvl for uid, lvl in levels.items()})
        brackets = {uuid.UUID(k): v for k, v in assigned.items()}

    # 3. Scores.
    scores: dict[uuid.UUID, R.WeekScore] = {}
    for uid, hid in members.items():
        scores[uid] = R.score_week(
            level=levels[uid],
            solves=[s for s in firsts[hid] if s.solved_at >= start],
            participations=participations[hid],
            rated_contest_ids={cid for cid, _, _ in history[hid]},
            window=(start, end),
            tz=tz,
        )

    # 4. Ranks inside each bracket.
    by_bracket: dict[int, list[tuple[str, int, int]]] = defaultdict(list)
    for uid, sc in scores.items():
        by_bracket[brackets[uid]].append((str(uid), sc.growth_points, sc.stretch_solves))
    ranks: dict[str, int] = {}
    for entries in by_bracket.values():
        ranks.update(R.rank_entries(entries))

    # 5. Write.
    status = "final" if final else "live"
    for uid, sc in scores.items():
        values = {
            "classroom_id": classroom.id,
            "user_id": uid,
            "week_start": week_start,
            "ref_rating": levels[uid],
            "bracket": brackets[uid],
            "growth_points": sc.growth_points,
            "stretch_solves": sc.stretch_solves,
            "breakdown": sc.breakdown,
            "rank_in_bracket": ranks[str(uid)],
            "status": status,
            "scoring_version": R.SCORING_VERSION,
            "computed_at": now,
        }
        stmt = pg_insert(ClassroomWeeklyScore).values(**values)
        await session.execute(
            stmt.on_conflict_do_update(
                constraint="uq_classroom_weekly_scores",
                set_={
                    k: v
                    for k, v in values.items()
                    if k not in ("classroom_id", "user_id", "week_start")
                },
            )
        )
    return len(scores)


# ── Input gathering ───────────────────────────────────────────────────────────


async def _student_handles(
    session: AsyncSession, classroom_id: uuid.UUID
) -> dict[uuid.UUID, uuid.UUID]:
    """user_id -> the one active verified CF handle id, for student members only.

    Only the active handle counts. After a re-verify, the same CF submissions exist
    under the old (inactive) handle row too, and counting both would double points.
    """
    rows = await session.execute(
        select(ClassroomMembership.user_id, UserHandle.id)
        .join(
            UserHandle,
            and_(
                UserHandle.user_id == ClassroomMembership.user_id,
                UserHandle.platform == HandlePlatform.CODEFORCES,
                UserHandle.is_verified.is_(True),
                UserHandle.is_active.is_(True),
            ),
        )
        .where(
            ClassroomMembership.classroom_id == classroom_id,
            ClassroomMembership.role == ClassroomMembershipRole.STUDENT,
        )
        .order_by(ClassroomMembership.user_id, UserHandle.verified_at.desc().nulls_last())
    )
    out: dict[uuid.UUID, uuid.UUID] = {}
    for user_id, handle_id in rows.all():
        out.setdefault(user_id, handle_id)
    return out


async def _rating_history(
    session: AsyncSession, handle_ids: list[uuid.UUID]
) -> dict[uuid.UUID, list[tuple[int, int, datetime]]]:
    """handle -> [(contest id, rating after it, time)]."""
    out: dict[uuid.UUID, list[tuple[int, int, datetime]]] = defaultdict(list)
    rows = await session.execute(
        select(
            RatingHistory.user_handle_id,
            RatingHistory.cf_contest_id,
            RatingHistory.new_rating,
            RatingHistory.contest_time,
        ).where(RatingHistory.user_handle_id.in_(handle_ids))
    )
    for hid, cid, rating, at in rows.all():
        out[hid].append((cid, rating, at))
    return out


async def _first_solves(
    session: AsyncSession, handle_ids: list[uuid.UUID], *, since: datetime, until: datetime
) -> dict[uuid.UUID, list[R.Solve]]:
    """First-ever individual AC per (handle, problem), kept if it falls in [since, until).

    Team ACs are left out of the "first-ever" check entirely, so a later solo solve
    of a problem first cracked with a team still scores. Ratings come from
    cf_problems at query time, so late CF ratings need no backfill.
    """
    firsts = (
        select(
            Submission.user_handle_id,
            Submission.problem_id,
            Submission.contest_id,
            Submission.participant_type,
            Submission.submitted_at,
        )
        .where(
            Submission.user_handle_id.in_(handle_ids),
            Submission.verdict == "OK",
            Submission.team_id.is_(None),
        )
        .distinct(Submission.user_handle_id, Submission.problem_id)
        .order_by(Submission.user_handle_id, Submission.problem_id, Submission.submitted_at)
        .subquery()
    )
    rows = await session.execute(
        select(firsts, CfProblem.rating)
        .outerjoin(CfProblem, CfProblem.problem_key == firsts.c.problem_id)
        .where(firsts.c.submitted_at >= since, firsts.c.submitted_at < until)
    )
    out: dict[uuid.UUID, list[R.Solve]] = defaultdict(list)
    for hid, problem_id, contest_id, ptype, at, rating in rows.all():
        out[hid].append(R.Solve(problem_id, rating, ptype or "UNKNOWN", contest_id, at))
    return out


async def _participations(
    session: AsyncSession, handle_ids: list[uuid.UUID], *, since: datetime, until: datetime
) -> dict[uuid.UUID, list[R.Participation]]:
    """Contests with live or virtual submissions (team ones included) in the window."""
    rows = await session.execute(
        select(
            Submission.user_handle_id,
            Submission.contest_id,
            Submission.participant_type,
            func.min(Submission.submitted_at),
            func.max(Submission.submitted_at),
        )
        .where(
            Submission.user_handle_id.in_(handle_ids),
            Submission.contest_id.is_not(None),
            Submission.participant_type.in_(PARTICIPATION_TYPES),
            Submission.submitted_at >= since,
            Submission.submitted_at < until,
        )
        .group_by(Submission.user_handle_id, Submission.contest_id, Submission.participant_type)
    )
    out: dict[uuid.UUID, list[R.Participation]] = defaultdict(list)
    for hid, cid, ptype, first_at, last_at in rows.all():
        out[hid].append(R.Participation(cid, ptype, first_at, last_at))
    return out
