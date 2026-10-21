"""Integration tests for the league read API, class settings and anonymous mode."""

import uuid
from datetime import UTC, datetime, timedelta

import pytest
import pytest_asyncio
from fastapi import HTTPException
from pydantic import ValidationError
from sqlalchemy import delete, select, update
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.models.analytics import CfProblem, Submission
from app.models.classroom import ClassroomDailyVisit, ClassroomMembership, ClassroomWeeklyScore
from app.models.signals import Recommendation, RecommendationSet
from app.models.user import User
from app.models.user_handle import HandlePlatform, HandleStatus, UserHandle
from app.schemas.classroom import ClassroomCreateRequest, ClassroomUpdateRequest
from app.services import classroom as classroom_service
from app.services import league_rules as R
from app.services.classroom import (
    create_classroom,
    create_invite,
    get_leaderboard,
    join_classroom,
    leave_classroom,
    list_members,
    update_classroom,
)
from app.services.league import get_league, get_league_history

KEY = "990002A"


def _user(tag):
    uid = uuid.uuid4().hex[:8]
    return User(
        email=f"la_{tag}_{uid}@t.com", google_id=f"la_{tag}_{uid}", name=f"{tag.title()} {uid}"
    )


async def _make(db, tag):
    u = _user(tag)
    db.add(u)
    await db.commit()
    await db.refresh(u)
    h = UserHandle(
        user_id=u.id,
        platform=HandlePlatform.CODEFORCES,
        handle=f"{tag}_{uuid.uuid4().hex[:5]}",
        status=HandleStatus.ACTIVE,
        is_verified=True,
        is_active=True,
        verified_at=datetime.now(UTC),
    )
    db.add(h)
    await db.commit()
    await db.refresh(h)
    return u, h


def _mid_week(tz="UTC"):
    now = datetime.now(UTC)
    start, _ = R.week_window(R.week_start_for(now, tz, 0), tz)
    return start + (now - start) / 2  # always inside the current week


@pytest_asyncio.fixture
async def setup(db_session):
    await db_session.execute(
        pg_insert(CfProblem)
        .values(
            problem_key=KEY,
            contest_id=990002,
            problem_index="A",
            name="Q",
            rating=1000,
        )
        .on_conflict_do_update(constraint="uq_cf_problems_problem_key", set_={"rating": 1000})
    )
    await db_session.commit()

    teacher, _ = await _make(db_session, "teacher")
    alice, a_h = await _make(db_session, "alice")
    bob, b_h = await _make(db_session, "bob")
    room = await create_classroom(db_session, teacher, "Settings Class", timezone="Asia/Dhaka")
    inv = await create_invite(db_session, room.id, teacher.id)
    await join_classroom(db_session, inv.token, alice)
    await join_classroom(db_session, inv.token, bob)
    await db_session.execute(
        pg_insert(Submission).values(
            user_handle_id=a_h.id,
            cf_submission_id=int(uuid.uuid4().int % 10**9),
            problem_id=KEY,
            problem_name="Q",
            contest_id=990002,
            verdict="OK",
            lang="C++",
            submitted_at=_mid_week("Asia/Dhaka"),
            participant_type="PRACTICE",
        )
    )
    await db_session.commit()
    yield {"room": room, "teacher": teacher, "alice": alice, "bob": bob, "inv": inv, "a_h": a_h}
    await db_session.execute(delete(CfProblem).where(CfProblem.problem_key == KEY))
    await db_session.commit()


# ── Views ─────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_student_sees_own_bracket_and_me(db_session, setup):
    S = setup
    res = await get_league(db_session, S["room"].id, S["alice"].id)
    assert res.status == "live" and res.timezone == "Asia/Dhaka"
    assert res.pulse is None and len(res.brackets) == 1
    assert (
        res.me.growth_points == 10 + 2 and res.me.ref_rating == 800
    )  # unrated: level 800, 1000 is a stretch
    entries = {e.is_me: e for e in res.brackets[0].entries}
    assert entries[True].ref_rating is None  # levels are teacher-only
    assert res.me.next_target is None  # first in bracket


@pytest.mark.asyncio
async def test_teacher_sees_every_bracket_and_pulse(db_session, setup):
    S = setup
    res = await get_league(db_session, S["room"].id, S["teacher"].id)
    assert res.me is None and res.suggestions == []
    assert res.pulse.total_members == 2 and res.pulse.active_members == 1
    assert [z.user_id for z in res.pulse.zero_gp] == [S["bob"].id]
    assert all(e.ref_rating is not None for b in res.brackets for e in b.entries)


@pytest.mark.asyncio
async def test_next_target_and_gap(db_session, setup):
    S = setup
    bob_view = await get_league(db_session, S["room"].id, S["bob"].id)
    assert bob_view.me.growth_points == 0
    assert bob_view.me.next_target.gp_gap == bob_view.brackets[0].entries[0].growth_points


@pytest.mark.asyncio
async def test_non_member_gets_403(db_session, setup):
    stranger, _ = await _make(db_session, "stranger")
    with pytest.raises(HTTPException) as exc:
        await get_league(db_session, setup["room"].id, stranger.id)
    assert exc.value.status_code == 403


@pytest.mark.asyncio
async def test_bad_week_param_is_422(db_session, setup):
    with pytest.raises(HTTPException) as exc:
        await get_league(db_session, setup["room"].id, setup["alice"].id, week="last tuesday")
    assert exc.value.status_code == 422


@pytest.mark.asyncio
async def test_league_read_logs_a_visit(db_session, setup):
    S = setup
    await get_league(db_session, S["room"].id, S["bob"].id)
    rows = await db_session.execute(
        select(ClassroomDailyVisit).where(
            ClassroomDailyVisit.classroom_id == S["room"].id,
            ClassroomDailyVisit.user_id == S["bob"].id,
        )
    )
    assert len(rows.scalars().all()) == 1


@pytest.mark.asyncio
async def test_suggestions_are_priced_in_gp(db_session, setup):
    S = setup
    rs = RecommendationSet(user_id=S["alice"].id, generated_at=datetime.now(UTC))
    db_session.add(rs)
    await db_session.flush()
    for pos, diff in enumerate((900, 1000, 1200, 1500)):
        db_session.add(
            Recommendation(
                recommendation_set_id=rs.id,
                problem_id=f"9{pos}A",
                problem_name="P",
                tag="dp",
                difficulty=diff,
                url="https://codeforces.com/x",
                reason="r",
                position=pos,
            )
        )
    await db_session.commit()
    res = await get_league(db_session, S["room"].id, S["alice"].id)
    assert [(s.rating, s.band, s.gp) for s in res.suggestions] == [
        (900, "stretch", 10),
        (1000, "stretch", 10),
        (1200, "reach", 12),
    ]


@pytest.mark.asyncio
async def test_rebuilds_when_a_member_synced_after_the_board(db_session, setup):
    S = setup
    await get_league(db_session, S["room"].id, S["bob"].id)
    later = datetime.now(UTC) + timedelta(seconds=5)
    b_h = (
        await db_session.execute(select(UserHandle).where(UserHandle.user_id == S["bob"].id))
    ).scalar_one()
    await db_session.execute(
        pg_insert(Submission).values(
            user_handle_id=b_h.id,
            cf_submission_id=int(uuid.uuid4().int % 10**9),
            problem_id=KEY,
            problem_name="Q",
            contest_id=990002,
            verdict="OK",
            lang="C++",
            submitted_at=_mid_week("Asia/Dhaka"),
            participant_type="PRACTICE",
        )
    )
    await db_session.execute(
        update(UserHandle).where(UserHandle.id == b_h.id).values(last_synced_at=later)
    )
    await db_session.commit()
    res = await get_league(db_session, S["room"].id, S["bob"].id)
    assert res.me.growth_points > 0


@pytest.mark.asyncio
async def test_history_hides_class_median_from_students(db_session, setup):
    S = setup
    await get_league(db_session, S["room"].id, S["alice"].id)
    student = await get_league_history(db_session, S["room"].id, S["alice"].id)
    teacher = await get_league_history(db_session, S["room"].id, S["teacher"].id)
    assert student.weeks[-1].my_gp == 12 and student.weeks[-1].class_median is None
    assert teacher.weeks[-1].my_gp is None and teacher.weeks[-1].class_median == 6.0


# ── Anonymous mode ────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_anonymous_mode_masks_classmates_everywhere(db_session, setup):
    S = setup
    await update_classroom(
        db_session,
        S["room"].id,
        S["teacher"].id,
        ClassroomUpdateRequest(member_visibility="anonymous"),
    )
    alice_id, bob_id = S["alice"].id, S["bob"].id

    league = await get_league(db_session, S["room"].id, alice_id)
    names = {e.user_id: e for e in league.brackets[0].entries}
    assert names[alice_id].display_name == S["alice"].name  # self: real
    assert names[bob_id].display_name == "Member 3" and names[bob_id].avatar_url is None

    board = await get_leaderboard(db_session, S["room"].id, alice_id)
    others = [e for e in board.entries if e.user_id != alice_id]
    assert others and all(
        e.user_name.startswith("Member ") and e.cf_handle.startswith("Member ") for e in others
    )

    members = await list_members(db_session, S["room"].id, alice_id)
    assert {m.user_name for m in members if m.user_id != alice_id} == {"Member 1", "Member 3"}

    teacher_view = await list_members(db_session, S["room"].id, S["teacher"].id)
    assert {m.user_name for m in teacher_view} == {
        S["teacher"].name,
        S["alice"].name,
        S["bob"].name,
    }

    again = await list_members(db_session, S["room"].id, alice_id)
    assert {m.user_id: m.user_name for m in again} == {m.user_id: m.user_name for m in members}


@pytest.mark.asyncio
async def test_existing_response_shapes_are_unchanged(db_session, setup):
    """The shipped Android app parses these; keys may only be added, never removed."""
    S = setup
    board = (await get_leaderboard(db_session, S["room"].id, S["alice"].id)).model_dump()
    assert set(board) >= {
        "classroom_id",
        "classroom_name",
        "entries",
        "member_count",
        "computed_at",
        "syncing",
    }
    assert set(board["entries"][0]) >= {
        "rank",
        "user_id",
        "cf_handle",
        "user_name",
        "avatar_url",
        "cf_rating",
        "solved_count",
        "current_streak",
        "longest_streak",
        "days_active_30d",
        "last_active_at",
        "top_tags",
        "weak_tags",
        "computed_at",
        "is_me",
    }
    member = (await list_members(db_session, S["room"].id, S["alice"].id))[0].model_dump()
    assert set(member) >= {"user_id", "user_name", "avatar_url", "cf_handle", "role", "joined_at"}


# ── Settings ──────────────────────────────────────────────────────────────────


def test_unknown_timezone_is_rejected_by_the_schema():
    with pytest.raises(ValidationError):
        ClassroomUpdateRequest(timezone="Mars/Olympus")
    with pytest.raises(ValidationError):
        ClassroomCreateRequest(name="x", timezone="Not/AZone")
    with pytest.raises(ValidationError):
        ClassroomUpdateRequest(week_starts_on=7)


@pytest.mark.asyncio
async def test_student_cannot_patch(db_session, setup):
    with pytest.raises(HTTPException) as exc:
        await update_classroom(
            db_session, setup["room"].id, setup["alice"].id, ClassroomUpdateRequest(name="Hijacked")
        )
    assert exc.value.status_code == 403


@pytest.mark.asyncio
async def test_timezone_change_drops_live_rows_keeps_final(db_session, setup):
    S = setup
    await get_league(db_session, S["room"].id, S["alice"].id)
    old_final = date_ = (datetime.now(UTC) - timedelta(days=60)).date()
    await db_session.execute(
        pg_insert(ClassroomWeeklyScore).values(
            classroom_id=S["room"].id,
            user_id=S["alice"].id,
            week_start=old_final,
            ref_rating=800,
            bracket=1,
            growth_points=40,
            stretch_solves=1,
            breakdown={},
            rank_in_bracket=1,
            status="final",
            scoring_version=1,
        )
    )
    await db_session.commit()

    res = await update_classroom(
        db_session,
        S["room"].id,
        S["teacher"].id,
        ClassroomUpdateRequest(timezone="Europe/London", week_starts_on=6),
    )
    assert res.timezone == "Europe/London" and res.week_starts_on == 6
    left = (
        (
            await db_session.execute(
                select(ClassroomWeeklyScore).where(
                    ClassroomWeeklyScore.classroom_id == S["room"].id
                )
            )
        )
        .scalars()
        .all()
    )
    assert [(r.week_start, r.status) for r in left] == [(date_, "final")]


# ── Membership ────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_alias_numbers_are_stable_and_never_reused(db_session, setup):
    S = setup
    rows = (
        await db_session.execute(
            select(ClassroomMembership.user_id, ClassroomMembership.alias_no).where(
                ClassroomMembership.classroom_id == S["room"].id
            )
        )
    ).all()
    assert dict(rows) == {S["teacher"].id: 1, S["alice"].id: 2, S["bob"].id: 3}

    await leave_classroom(db_session, S["room"].id, S["bob"].id)
    await join_classroom(db_session, S["inv"].token, S["bob"])
    alias = await db_session.scalar(
        select(ClassroomMembership.alias_no).where(
            ClassroomMembership.classroom_id == S["room"].id,
            ClassroomMembership.user_id == S["bob"].id,
        )
    )
    assert alias == 4


@pytest.mark.asyncio
async def test_member_cap_returns_409(db_session, setup, monkeypatch):
    S = setup
    monkeypatch.setattr(classroom_service, "MAX_CLASSROOM_MEMBERS", 3)
    extra, _ = await _make(db_session, "extra")
    with pytest.raises(HTTPException) as exc:
        await join_classroom(db_session, S["inv"].token, extra)
    assert exc.value.status_code == 409 and "full" in exc.value.detail


@pytest.mark.asyncio
async def test_leaving_removes_league_rows(db_session, setup):
    S = setup
    await get_league(db_session, S["room"].id, S["alice"].id)
    await leave_classroom(db_session, S["room"].id, S["alice"].id)
    left = (
        (
            await db_session.execute(
                select(ClassroomWeeklyScore).where(
                    ClassroomWeeklyScore.classroom_id == S["room"].id,
                    ClassroomWeeklyScore.user_id == S["alice"].id,
                )
            )
        )
        .scalars()
        .all()
    )
    assert left == []
