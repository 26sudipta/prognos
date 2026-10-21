"""Integration tests for the league rebuild worker (real DB, fixed clock)."""

import uuid
from datetime import UTC, datetime, timedelta

import pytest
import pytest_asyncio
from sqlalchemy import delete, select, update
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.models.analytics import CfProblem, RatingHistory, Submission
from app.models.classroom import Classroom, ClassroomWeeklyScore
from app.models.user import User
from app.models.user_handle import HandlePlatform, HandleStatus, UserHandle
from app.services.classroom import create_classroom, create_invite, join_classroom, remove_member
from app.workers.league_sync import rebuild_league

MON = datetime(2026, 9, 14, tzinfo=UTC)  # a Monday; the class runs on UTC
NOW = MON + timedelta(days=3)  # Thursday of that week
KEYS = ["990001A", "990001B", "990001C", "990001D"]


def _user(tag: str) -> User:
    uid = uuid.uuid4().hex[:8]
    return User(
        email=f"lg_{tag}_{uid}@t.com", google_id=f"lg_{tag}_{uid}", name=f"{tag.title()} {uid}"
    )


async def _with_handle(db, user: User, *, active=True) -> UserHandle:
    h = UserHandle(
        user_id=user.id,
        platform=HandlePlatform.CODEFORCES,
        handle=f"h_{uuid.uuid4().hex[:6]}",
        status=HandleStatus.ACTIVE,
        is_verified=True,
        is_active=active,
        verified_at=datetime.now(UTC),
    )
    db.add(h)
    await db.commit()
    await db.refresh(h)
    return h


async def _ac(db, handle_id, key, at, ptype="PRACTICE", *, cf_id=None, team_id=None, verdict="OK"):
    await db.execute(
        pg_insert(Submission).values(
            user_handle_id=handle_id,
            cf_submission_id=cf_id or int(uuid.uuid4().int % 10**9),
            problem_id=key,
            problem_name=key,
            contest_id=int(key[:-1]),
            verdict=verdict,
            lang="C++",
            submitted_at=at,
            participant_type=ptype,
            team_id=team_id,
        )
    )
    await db.commit()


@pytest_asyncio.fixture
async def catalogue(db_session):
    ratings = {"990001A": 1000, "990001B": 1200, "990001C": 1500, "990001D": None}
    for key, rating in ratings.items():
        await db_session.execute(
            pg_insert(CfProblem)
            .values(
                problem_key=key,
                contest_id=990001,
                problem_index=key[-1],
                name=key,
                rating=rating,
            )
            .on_conflict_do_update(constraint="uq_cf_problems_problem_key", set_={"rating": rating})
        )
    await db_session.commit()
    yield
    await db_session.execute(delete(CfProblem).where(CfProblem.problem_key.in_(KEYS)))
    await db_session.commit()


@pytest_asyncio.fixture
async def league(db_session, catalogue):
    """A UTC class: one teacher, two students (levels 1200 and 800/unrated)."""
    teacher, alice, bob = _user("teacher"), _user("alice"), _user("bob")
    db_session.add_all([teacher, alice, bob])
    await db_session.commit()
    for u in (teacher, alice, bob):
        await db_session.refresh(u)
    t_handle = await _with_handle(db_session, teacher)
    a_handle = await _with_handle(db_session, alice)
    b_handle = await _with_handle(db_session, bob)

    room = await create_classroom(db_session, teacher, "League Class")
    inv = await create_invite(db_session, room.id, teacher.id)
    await join_classroom(db_session, inv.token, alice)
    await join_classroom(db_session, inv.token, bob)

    # Alice: rated 1200 before the week started.
    db_session.add(
        RatingHistory(
            user_handle_id=a_handle.id,
            cf_contest_id=1,
            contest_name="R",
            old_rating=1100,
            new_rating=1200,
            delta=100,
            rank=5,
            contest_time=MON - timedelta(days=20),
        )
    )
    await db_session.commit()
    yield {
        "room": room,
        "teacher": teacher,
        "alice": alice,
        "bob": bob,
        "t_handle": t_handle,
        "a_handle": a_handle,
        "b_handle": b_handle,
    }


async def _rows(db, room_id):
    res = await db.execute(
        select(ClassroomWeeklyScore)
        .where(ClassroomWeeklyScore.classroom_id == room_id)
        .execution_options(populate_existing=True)
    )
    return {r.user_id: r for r in res.scalars()}


async def _week_rows(db, room_id, week_start):
    res = await db.execute(
        select(ClassroomWeeklyScore)
        .where(
            ClassroomWeeklyScore.classroom_id == room_id,
            ClassroomWeeklyScore.week_start == week_start,
        )
        .execution_options(populate_existing=True)
    )
    return list(res.scalars())


@pytest.mark.asyncio
async def test_scores_students_and_excludes_teacher(db_session, league):
    L = league
    await _ac(
        db_session, L["a_handle"].id, "990001C", MON + timedelta(days=1)
    )  # 1500 vs 1200: reach
    await _ac(db_session, L["a_handle"].id, "990001B", MON + timedelta(days=2))  # at level
    await _ac(db_session, L["t_handle"].id, "990001C", MON + timedelta(days=1))  # teacher: ignored

    await rebuild_league(db_session, L["room"].id, now=NOW)
    rows = await _rows(db_session, L["room"].id)

    assert set(rows) == {L["alice"].id, L["bob"].id}
    alice = rows[L["alice"].id]
    assert alice.ref_rating == 1200 and alice.bracket == 1
    assert alice.growth_points == 12 + 6 + 2 * 2  # reach + at level + 2 solve days
    assert alice.rank_in_bracket == 1 and alice.status == "live"
    assert rows[L["bob"].id].growth_points == 0 and rows[L["bob"].id].ref_rating == 800


@pytest.mark.asyncio
async def test_reverified_student_is_not_double_counted(db_session, league):
    L = league
    old = await _with_handle(db_session, L["alice"], active=False)  # pre-reverify row
    await _ac(db_session, old.id, "990001C", MON + timedelta(days=1), cf_id=777)
    await _ac(db_session, L["a_handle"].id, "990001C", MON + timedelta(days=1), cf_id=777)

    await rebuild_league(db_session, L["room"].id, now=NOW)
    assert (await _rows(db_session, L["room"].id))[L["alice"].id].growth_points == 12 + 2


@pytest.mark.asyncio
async def test_only_first_ever_solo_ac_scores(db_session, league):
    L = league
    await _ac(
        db_session, L["a_handle"].id, "990001C", MON - timedelta(days=30)
    )  # solved last month
    await _ac(db_session, L["a_handle"].id, "990001C", MON + timedelta(days=1))  # re-solve: 0
    await _ac(
        db_session, L["a_handle"].id, "990001B", MON - timedelta(days=5), team_id=9
    )  # team AC
    await _ac(
        db_session, L["a_handle"].id, "990001B", MON + timedelta(days=2)
    )  # first solo: scores

    await rebuild_league(db_session, L["room"].id, now=NOW)
    alice = (await _rows(db_session, L["room"].id))[L["alice"].id]
    assert alice.breakdown["solves"] == 1 and alice.breakdown["at_level"] == 6


@pytest.mark.asyncio
async def test_level_and_bracket_freeze_for_the_week(db_session, league):
    L = league
    await rebuild_league(db_session, L["room"].id, now=NOW)
    db_session.add(
        RatingHistory(
            user_handle_id=L["a_handle"].id,
            cf_contest_id=2,
            contest_name="R2",
            old_rating=1200,
            new_rating=1600,
            delta=400,
            rank=1,
            contest_time=MON + timedelta(days=2),
        )
    )
    await db_session.commit()
    await rebuild_league(db_session, L["room"].id, now=NOW + timedelta(hours=5))
    assert (await _rows(db_session, L["room"].id))[L["alice"].id].ref_rating == 1200


@pytest.mark.asyncio
async def test_problem_rated_mid_week_is_rescored(db_session, league):
    L = league
    await _ac(db_session, L["b_handle"].id, "990001D", MON + timedelta(days=1))  # unrated for now
    await rebuild_league(db_session, L["room"].id, now=NOW)
    assert (await _rows(db_session, L["room"].id))[L["bob"].id].breakdown["unrated"] == 2

    await db_session.execute(
        update(CfProblem).where(CfProblem.problem_key == "990001D").values(rating=900)
    )
    await db_session.commit()
    await rebuild_league(db_session, L["room"].id, now=NOW + timedelta(hours=1))
    bob = (await _rows(db_session, L["room"].id))[L["bob"].id]
    assert bob.breakdown["unrated"] == 0 and bob.breakdown["stretch"] == 10  # 900 vs 800


@pytest.mark.asyncio
async def test_week_finalizes_after_grace_and_then_never_changes(db_session, league):
    L = league
    await _ac(db_session, L["a_handle"].id, "990001B", MON + timedelta(days=1))
    await rebuild_league(db_session, L["room"].id, now=NOW)

    after_grace = MON + timedelta(days=7) + timedelta(hours=49)
    await rebuild_league(db_session, L["room"].id, now=after_grace)
    rows = await _week_rows(db_session, L["room"].id, MON.date())
    assert len(rows) == 2 and all(r.status == "final" for r in rows)
    frozen = {r.user_id: r.growth_points for r in rows}

    await _ac(
        db_session, L["a_handle"].id, "990001C", MON + timedelta(days=2)
    )  # late-arriving data
    await rebuild_league(db_session, L["room"].id, now=after_grace + timedelta(hours=1))
    res = await db_session.execute(
        select(ClassroomWeeklyScore)
        .where(
            ClassroomWeeklyScore.classroom_id == L["room"].id,
            ClassroomWeeklyScore.week_start == MON.date(),
        )
        .execution_options(populate_existing=True)
    )
    assert {r.user_id: r.growth_points for r in res.scalars()} == frozen


@pytest.mark.asyncio
async def test_week_stays_live_within_grace(db_session, league):
    L = league
    await rebuild_league(db_session, L["room"].id, now=NOW)
    await rebuild_league(db_session, L["room"].id, now=MON + timedelta(days=8))  # 24 h after close
    rows = await _week_rows(db_session, L["room"].id, MON.date())
    assert len(rows) == 2 and all(r.status == "live" for r in rows)


@pytest.mark.asyncio
async def test_removed_member_leaves_the_live_week(db_session, league):
    L = league
    await rebuild_league(db_session, L["room"].id, now=NOW)
    await remove_member(db_session, L["room"].id, L["bob"].id, L["teacher"].id)
    await rebuild_league(db_session, L["room"].id, now=NOW + timedelta(minutes=5))
    assert set(await _rows(db_session, L["room"].id)) == {L["alice"].id}


@pytest.mark.asyncio
async def test_week_follows_the_class_timezone(db_session, league):
    L = league
    await db_session.execute(
        update(Classroom).where(Classroom.id == L["room"].id).values(timezone="Asia/Dhaka")
    )
    await db_session.commit()
    # Sunday 19:00 UTC is Monday 01:00 in Dhaka: next week, not this one.
    await _ac(db_session, L["a_handle"].id, "990001B", MON + timedelta(days=6, hours=19))
    await rebuild_league(db_session, L["room"].id, now=MON + timedelta(days=6, hours=20))
    rows = await _rows(db_session, L["room"].id)
    alice = rows[L["alice"].id]
    assert alice.week_start == (MON + timedelta(days=7)).date()
    assert alice.breakdown["at_level"] == 6
