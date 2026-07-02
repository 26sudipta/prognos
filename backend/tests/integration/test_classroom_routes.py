"""Integration tests for Phase 4 — Classroom System (services layer, real DB)."""

import uuid
from datetime import UTC, datetime, timedelta

import pytest
import pytest_asyncio
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.classroom import (
    Classroom,
    ClassroomInvite,
    ClassroomLeaderboard,
    ClassroomMembership,
    ClassroomMembershipRole,
)
from app.models.user import User
from app.models.user_handle import UserHandle
from app.services.classroom import (
    create_classroom,
    create_invite,
    delete_classroom,
    get_cohort_analytics,
    get_leaderboard,
    get_user_classrooms,
    join_classroom,
    join_preview,
    leave_classroom,
    list_invites,
    list_members,
    remove_member,
    revoke_invite,
    sync_classroom,
)


# ── Fixtures ──────────────────────────────────────────────────────────────────

def _make_user(suffix: str = "") -> User:
    uid = str(uuid.uuid4())[:8]
    return User(
        email=f"cls_test_{uid}{suffix}@test.com",
        google_id=f"gid_cls_{uid}{suffix}",
        name=f"Test User {uid}",
    )


def _make_handle(user_id: uuid.UUID, handle: str = "tourist") -> UserHandle:
    from app.models.user_handle import HandlePlatform, HandleStatus, HandleSyncStatus
    return UserHandle(
        user_id=user_id,
        platform=HandlePlatform.CODEFORCES,
        handle=handle,
        is_verified=True,
        is_active=True,
        status=HandleStatus.ACTIVE,
        sync_status=HandleSyncStatus.IDLE,
    )


@pytest_asyncio.fixture
async def teacher_user(db_session: AsyncSession):
    user = _make_user("_teacher")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    # A teacher must own a verified handle to create a classroom.
    db_session.add(_make_handle(user.id, handle=f"teach_{str(uuid.uuid4())[:6]}"))
    await db_session.commit()
    yield user
    try:
        await db_session.delete(user)
        await db_session.commit()
    except Exception:
        pass


@pytest_asyncio.fixture
async def student_user(db_session: AsyncSession):
    user = _make_user("_student")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    yield user
    try:
        await db_session.delete(user)
        await db_session.commit()
    except Exception:
        pass


@pytest_asyncio.fixture
async def student_with_handle(db_session: AsyncSession, student_user: User):
    handle = _make_handle(student_user.id, handle=f"handle_{str(uuid.uuid4())[:6]}")
    db_session.add(handle)
    await db_session.commit()
    yield student_user
    try:
        await db_session.delete(handle)
        await db_session.commit()
    except Exception:
        pass


@pytest_asyncio.fixture
async def classroom(db_session: AsyncSession, teacher_user: User):
    c = await create_classroom(db_session, teacher_user, "Test Classroom")
    yield c
    # cleanup is handled by cascade when teacher_user is deleted


@pytest_asyncio.fixture
async def invite(db_session: AsyncSession, classroom, teacher_user: User):
    inv = await create_invite(db_session, classroom.id, teacher_user.id)
    yield inv


# ── create_classroom ──────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_create_classroom_creates_teacher_membership(db_session: AsyncSession, teacher_user: User):
    result = await create_classroom(db_session, teacher_user, "  My Classroom  ")
    assert result.name == "My Classroom"  # strips whitespace via validator
    assert result.my_role == "teacher"
    assert result.member_count == 1
    assert result.owner_id == teacher_user.id


@pytest.mark.asyncio
async def test_create_classroom_requires_verified_handle(db_session: AsyncSession):
    """Only a user with a verified CF handle can become a teacher."""
    from fastapi import HTTPException

    unverified = _make_user("_unverified")
    db_session.add(unverified)
    await db_session.commit()
    await db_session.refresh(unverified)

    with pytest.raises(HTTPException) as exc:
        await create_classroom(db_session, unverified, "No Handle Class")
    assert exc.value.status_code == 403

    await db_session.delete(unverified)
    await db_session.commit()


@pytest.mark.asyncio
async def test_create_classroom_name_blank_raises(db_session: AsyncSession, teacher_user: User):
    from pydantic import ValidationError
    from app.schemas.classroom import ClassroomCreateRequest
    with pytest.raises(ValidationError):
        ClassroomCreateRequest(name="   ")


# ── get_user_classrooms ───────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_get_user_classrooms_shows_only_own(db_session: AsyncSession, teacher_user: User):
    await create_classroom(db_session, teacher_user, "Alpha")
    await create_classroom(db_session, teacher_user, "Beta")
    results = await get_user_classrooms(db_session, teacher_user.id)
    names = {r.name for r in results}
    assert "Alpha" in names
    assert "Beta" in names


@pytest.mark.asyncio
async def test_get_user_classrooms_empty_for_new_user(db_session: AsyncSession):
    fresh_user = _make_user("_fresh")
    db_session.add(fresh_user)
    await db_session.commit()
    results = await get_user_classrooms(db_session, fresh_user.id)
    assert results == []
    await db_session.delete(fresh_user)
    await db_session.commit()


# ── delete_classroom ──────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_delete_classroom_owner_succeeds(db_session: AsyncSession, teacher_user: User):
    c = await create_classroom(db_session, teacher_user, "To Delete")
    await delete_classroom(db_session, c.id, teacher_user.id)
    remaining = await get_user_classrooms(db_session, teacher_user.id)
    # classroom should not appear (is_active=false)
    assert not any(r.id == c.id for r in remaining)


@pytest.mark.asyncio
async def test_delete_classroom_non_owner_raises_403(db_session: AsyncSession, teacher_user: User, student_user: User):
    from fastapi import HTTPException
    c = await create_classroom(db_session, teacher_user, "To Delete")
    with pytest.raises(HTTPException) as exc:
        await delete_classroom(db_session, c.id, student_user.id)
    assert exc.value.status_code == 403


# ── Invites ───────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_create_invite_returns_valid_url(db_session: AsyncSession, classroom, teacher_user: User):
    inv = await create_invite(db_session, classroom.id, teacher_user.id)
    assert inv.invite_url.startswith("http")
    assert inv.token in inv.invite_url
    assert inv.is_active is True


@pytest.mark.asyncio
async def test_create_invite_student_raises_403(db_session: AsyncSession, classroom, student_user: User):
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as exc:
        await create_invite(db_session, classroom.id, student_user.id)
    assert exc.value.status_code == 403


@pytest.mark.asyncio
async def test_revoke_invite_marks_inactive(db_session: AsyncSession, classroom, teacher_user: User, invite):
    await revoke_invite(db_session, classroom.id, invite.id, teacher_user.id)
    active = await list_invites(db_session, classroom.id, teacher_user.id)
    assert not any(i.id == invite.id for i in active)


@pytest.mark.asyncio
async def test_revoke_invite_twice_raises_409(db_session: AsyncSession, classroom, teacher_user: User, invite):
    from fastapi import HTTPException
    await revoke_invite(db_session, classroom.id, invite.id, teacher_user.id)
    with pytest.raises(HTTPException) as exc:
        await revoke_invite(db_session, classroom.id, invite.id, teacher_user.id)
    assert exc.value.status_code == 409


# ── join_preview ──────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_join_preview_valid_token(db_session: AsyncSession, classroom, invite):
    result = await join_preview(db_session, invite.token)
    assert result.is_valid is True
    assert result.classroom_name == "Test Classroom"
    assert result.member_count == 1


@pytest.mark.asyncio
async def test_join_preview_unknown_token(db_session: AsyncSession):
    result = await join_preview(db_session, "nonexistent-token")
    assert result.is_valid is False
    assert result.error_code == "NOT_FOUND"


@pytest.mark.asyncio
async def test_join_preview_expired_token(db_session: AsyncSession, classroom, teacher_user: User):
    # Insert an already-expired invite directly
    expired_invite = ClassroomInvite(
        classroom_id=classroom.id,
        token=f"expired_{uuid.uuid4()}",
        created_by=teacher_user.id,
        expires_at=datetime.now(UTC) - timedelta(hours=1),
    )
    db_session.add(expired_invite)
    await db_session.commit()

    result = await join_preview(db_session, expired_invite.token)
    assert result.is_valid is False
    assert result.error_code == "EXPIRED"

    await db_session.delete(expired_invite)
    await db_session.commit()


# ── join_classroom ────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_join_classroom_happy_path(db_session: AsyncSession, classroom, invite, student_with_handle: User):
    result = await join_classroom(db_session, invite.token, student_with_handle)
    assert result.my_role == "student"
    assert result.member_count == 2


@pytest.mark.asyncio
async def test_join_classroom_no_handle_raises_403(db_session: AsyncSession, classroom, invite, student_user: User):
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as exc:
        await join_classroom(db_session, invite.token, student_user)
    assert exc.value.status_code == 403
    assert "handle" in exc.value.detail.lower()


@pytest.mark.asyncio
async def test_join_classroom_already_member_raises_409(
    db_session: AsyncSession, classroom, invite, student_with_handle: User
):
    from fastapi import HTTPException
    await join_classroom(db_session, invite.token, student_with_handle)
    with pytest.raises(HTTPException) as exc:
        await join_classroom(db_session, invite.token, student_with_handle)
    assert exc.value.status_code == 409


@pytest.mark.asyncio
async def test_join_classroom_revoked_invite_raises_410(
    db_session: AsyncSession, classroom, invite, teacher_user: User, student_with_handle: User
):
    from fastapi import HTTPException
    await revoke_invite(db_session, classroom.id, invite.id, teacher_user.id)
    with pytest.raises(HTTPException) as exc:
        await join_classroom(db_session, invite.token, student_with_handle)
    assert exc.value.status_code == 410


@pytest.mark.asyncio
async def test_join_classroom_expired_invite_raises_410(
    db_session: AsyncSession, classroom, teacher_user: User, student_with_handle: User
):
    from fastapi import HTTPException
    from datetime import timedelta
    expired = ClassroomInvite(
        classroom_id=classroom.id,
        created_by=teacher_user.id,
        token=f"exp_{uuid.uuid4()}",
        expires_at=datetime.now(UTC) - timedelta(hours=1),
    )
    db_session.add(expired)
    await db_session.commit()
    with pytest.raises(HTTPException) as exc:
        await join_classroom(db_session, expired.token, student_with_handle)
    assert exc.value.status_code == 410


@pytest.mark.asyncio
async def test_join_classroom_invalid_token_raises_404(db_session: AsyncSession, student_with_handle: User):
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as exc:
        await join_classroom(db_session, "bad-token", student_with_handle)
    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_join_is_multi_use(
    db_session: AsyncSession, classroom, invite, student_with_handle: User
):
    """Same invite token can be used by multiple students."""
    second_student = _make_user("_s2")
    db_session.add(second_student)
    await db_session.commit()
    handle2 = _make_handle(second_student.id, handle=f"h_{str(uuid.uuid4())[:6]}")
    db_session.add(handle2)
    await db_session.commit()

    r1 = await join_classroom(db_session, invite.token, student_with_handle)
    r2 = await join_classroom(db_session, invite.token, second_student)
    assert r1.member_count == 2
    assert r2.member_count == 3

    await db_session.delete(handle2)
    await db_session.delete(second_student)
    await db_session.commit()


# ── Member management ─────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_list_members_shows_teacher_and_student(
    db_session: AsyncSession, classroom, invite, teacher_user: User, student_with_handle: User
):
    await join_classroom(db_session, invite.token, student_with_handle)
    members = await list_members(db_session, classroom.id, teacher_user.id)
    roles = {m.role for m in members}
    assert "teacher" in roles
    assert "student" in roles


@pytest.mark.asyncio
async def test_remove_member_removes_from_list(
    db_session: AsyncSession, classroom, invite, teacher_user: User, student_with_handle: User
):
    await join_classroom(db_session, invite.token, student_with_handle)
    await remove_member(db_session, classroom.id, student_with_handle.id, teacher_user.id)
    members = await list_members(db_session, classroom.id, teacher_user.id)
    assert not any(m.user_id == student_with_handle.id for m in members)


@pytest.mark.asyncio
async def test_remove_owner_raises_400(db_session: AsyncSession, classroom, teacher_user: User):
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as exc:
        await remove_member(db_session, classroom.id, teacher_user.id, teacher_user.id)
    assert exc.value.status_code == 400


@pytest.mark.asyncio
async def test_leave_classroom_student_succeeds(
    db_session: AsyncSession, classroom, invite, teacher_user: User, student_with_handle: User
):
    await join_classroom(db_session, invite.token, student_with_handle)
    await leave_classroom(db_session, classroom.id, student_with_handle.id)
    members = await list_members(db_session, classroom.id, teacher_user.id)
    assert not any(m.user_id == student_with_handle.id for m in members)


@pytest.mark.asyncio
async def test_leave_classroom_owner_raises_400(db_session: AsyncSession, classroom, teacher_user: User):
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as exc:
        await leave_classroom(db_session, classroom.id, teacher_user.id)
    assert exc.value.status_code == 400


# ── Leaderboard ───────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_leaderboard_lazily_rebuilds_on_read(db_session: AsyncSession, classroom, teacher_user: User):
    # Worker-free deployment: nothing rebuilds the cache in the background, so the first
    # read must rebuild it inline and include the verified teacher.
    result = await get_leaderboard(db_session, classroom.id, teacher_user.id)
    assert len(result.entries) == 1
    assert result.entries[0].is_me is True
    assert result.computed_at is not None
    assert result.classroom_name == "Test Classroom"


@pytest.mark.asyncio
async def test_leaderboard_returns_entries_after_upsert(
    db_session: AsyncSession, classroom, teacher_user: User
):
    # Manually insert a leaderboard row (simulates Celery rebuild)
    row = ClassroomLeaderboard(
        classroom_id=classroom.id,
        user_id=teacher_user.id,
        cf_handle="tourist",
        user_name="Test User",
        cf_rating=2800,
        solved_count=500,
        current_streak=10,
        longest_streak=50,
        days_active_30d=25,
        computed_at=datetime.now(UTC),  # fresh → read serves cache instead of rebuilding
    )
    db_session.add(row)
    await db_session.commit()

    result = await get_leaderboard(db_session, classroom.id, teacher_user.id)
    assert len(result.entries) == 1
    assert result.entries[0].cf_rating == 2800
    assert result.entries[0].is_me is True
    assert result.entries[0].rank == 1


# ── Classroom bulk sync ("Sync" button) ───────────────────────────────────────

async def _handle_id_for(db_session: AsyncSession, user_id: uuid.UUID) -> uuid.UUID:
    from sqlalchemy import select
    return (
        await db_session.execute(
            select(UserHandle.id).where(UserHandle.user_id == user_id)
        )
    ).scalar_one()


@pytest.mark.asyncio
async def test_sync_classroom_enqueues_members_in_leaderboard_order(
    db_session: AsyncSession, classroom, invite, student_with_handle: User, teacher_user: User, monkeypatch
):
    from fastapi import BackgroundTasks

    await join_classroom(db_session, invite.token, student_with_handle)

    teacher_hid = await _handle_id_for(db_session, teacher_user.id)
    student_hid = await _handle_id_for(db_session, student_with_handle.id)

    # Fresh leaderboard rows so ordering is deterministic (teacher rated higher → first).
    now = datetime.now(UTC)
    db_session.add_all([
        ClassroomLeaderboard(
            classroom_id=classroom.id, user_id=teacher_user.id, cf_handle="t",
            user_name="T", cf_rating=2800, computed_at=now,
        ),
        ClassroomLeaderboard(
            classroom_id=classroom.id, user_id=student_with_handle.id, cf_handle="s",
            user_name="S", cf_rating=1500, computed_at=now,
        ),
    ])
    await db_session.commit()

    enqueued: list[uuid.UUID] = []
    monkeypatch.setattr(
        "app.services.classroom.enqueue_sync",
        lambda hid, bt: enqueued.append(hid) or "task",
    )

    result = await sync_classroom(db_session, classroom.id, teacher_user.id, BackgroundTasks())
    assert result.members_enqueued == 2
    assert enqueued == [teacher_hid, student_hid]  # top→bottom of the board


@pytest.mark.asyncio
async def test_sync_classroom_cooldown_returns_429(
    db_session: AsyncSession, classroom, teacher_user: User, monkeypatch
):
    from fastapi import BackgroundTasks, HTTPException

    monkeypatch.setattr("app.services.classroom.enqueue_sync", lambda hid, bt: "task")

    await sync_classroom(db_session, classroom.id, teacher_user.id, BackgroundTasks())
    with pytest.raises(HTTPException) as exc:
        await sync_classroom(db_session, classroom.id, teacher_user.id, BackgroundTasks())
    assert exc.value.status_code == 429
    assert exc.value.detail["retry_after_seconds"] > 0


@pytest.mark.asyncio
async def test_sync_classroom_non_member_raises_403(
    db_session: AsyncSession, classroom, student_user: User, monkeypatch
):
    from fastapi import BackgroundTasks, HTTPException

    monkeypatch.setattr("app.services.classroom.enqueue_sync", lambda hid, bt: "task")
    with pytest.raises(HTTPException) as exc:
        await sync_classroom(db_session, classroom.id, student_user.id, BackgroundTasks())
    assert exc.value.status_code == 403


@pytest.mark.asyncio
async def test_leaderboard_syncing_flag_reflects_in_progress_handle(
    db_session: AsyncSession, classroom, teacher_user: User
):
    from sqlalchemy import update
    from app.models.user_handle import HandleSyncStatus

    # Not syncing initially.
    result = await get_leaderboard(db_session, classroom.id, teacher_user.id)
    assert result.syncing is False

    await db_session.execute(
        update(UserHandle)
        .where(UserHandle.user_id == teacher_user.id)
        .values(sync_status=HandleSyncStatus.IN_PROGRESS)
    )
    await db_session.commit()

    result = await get_leaderboard(db_session, classroom.id, teacher_user.id)
    assert result.syncing is True


@pytest.mark.asyncio
async def test_sync_classroom_marks_handles_in_progress(
    db_session: AsyncSession, classroom, teacher_user: User, monkeypatch
):
    # The immediate leaderboard read after a sync must report syncing=true so the frontend
    # starts polling — even though the actual BackgroundTasks run after the response.
    from fastapi import BackgroundTasks
    from sqlalchemy import select
    from app.models.user_handle import HandleSyncStatus

    monkeypatch.setattr("app.services.classroom.enqueue_sync", lambda hid, bt: "task")
    await sync_classroom(db_session, classroom.id, teacher_user.id, BackgroundTasks())

    status_val = (
        await db_session.execute(
            select(UserHandle.sync_status).where(UserHandle.user_id == teacher_user.id)
        )
    ).scalar_one()
    assert status_val == HandleSyncStatus.IN_PROGRESS

    result = await get_leaderboard(db_session, classroom.id, teacher_user.id)
    assert result.syncing is True


@pytest.mark.asyncio
async def test_leaderboard_rebuilds_when_member_synced_after_board(
    db_session: AsyncSession, classroom, teacher_user: User
):
    # Free tier has no broker, so member syncs don't rebuild the cache. A read must rebuild
    # when a member's last_synced_at is newer than the (still within-TTL) board — otherwise the
    # leaderboard would show stale numbers for up to the TTL after an on-demand sync.
    from sqlalchemy import select

    now = datetime.now(UTC)
    # A fresh (within-TTL) but bogus cached row.
    db_session.add(ClassroomLeaderboard(
        classroom_id=classroom.id, user_id=teacher_user.id, cf_handle="t",
        user_name="T", cf_rating=9999, solved_count=999, computed_at=now - timedelta(minutes=1),
    ))
    # Member synced more recently than the board was built → board is "behind".
    handle = (
        await db_session.execute(select(UserHandle).where(UserHandle.user_id == teacher_user.id))
    ).scalar_one()
    handle.last_synced_at = now
    await db_session.commit()

    result = await get_leaderboard(db_session, classroom.id, teacher_user.id)
    # Rebuilt from real (empty) data → the bogus 999 is gone.
    assert result.entries[0].solved_count == 0


# ── Cohort analytics ──────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_cohort_student_raises_403(
    db_session: AsyncSession, classroom, invite, student_with_handle: User
):
    from fastapi import HTTPException
    await join_classroom(db_session, invite.token, student_with_handle)
    with pytest.raises(HTTPException) as exc:
        await get_cohort_analytics(db_session, classroom.id, student_with_handle.id)
    assert exc.value.status_code == 403


@pytest.mark.asyncio
async def test_cohort_no_activity(db_session: AsyncSession, classroom, teacher_user: User):
    # Cohort rebuilds the leaderboard on read, so the verified teacher appears — but with
    # no synced activity there's no rating, no weak tags, and 0 active days.
    result = await get_cohort_analytics(db_session, classroom.id, teacher_user.id)
    assert result.member_count == 1
    assert result.class_average_rating is None
    assert result.most_neglected_tags == []
    assert len(result.student_attendance) == 1
    assert result.student_attendance[0].days_active_30d == 0


@pytest.mark.asyncio
async def test_cohort_aggregates_weak_tags(db_session: AsyncSession, classroom, teacher_user: User):
    # Two students both have 'dp' as neglected — it should appear as count=2
    for i, handle in enumerate(["handle_a", "handle_b"]):
        fresh = _make_user(f"_cohort{i}")
        db_session.add(fresh)
        await db_session.commit()
        row = ClassroomLeaderboard(
            classroom_id=classroom.id,
            user_id=fresh.id,
            cf_handle=handle,
            user_name=f"user{i}",
            cf_rating=1500,
            solved_count=100,
            current_streak=5,
            longest_streak=20,
            days_active_30d=10,
            weak_tags=[{"tag": "dp", "signal_type": "neglected", "score": 15.0}],
            computed_at=datetime.now(UTC),  # fresh → cohort serves cache, no rebuild
        )
        db_session.add(row)
    await db_session.commit()

    result = await get_cohort_analytics(db_session, classroom.id, teacher_user.id)
    dp_entry = next((t for t in result.most_neglected_tags if t.tag == "dp"), None)
    assert dp_entry is not None
    assert dp_entry.count == 2

    # Cleanup
    await db_session.execute(
        delete(ClassroomLeaderboard).where(ClassroomLeaderboard.classroom_id == classroom.id)
    )
    await db_session.commit()


# ── Account deletion guard ────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_soft_delete_user_blocked_when_owns_classroom(db_session: AsyncSession, teacher_user: User):
    from fastapi import HTTPException
    from app.services.auth import soft_delete_user

    await create_classroom(db_session, teacher_user, "My Class")
    with pytest.raises(HTTPException) as exc:
        await soft_delete_user(db_session, str(teacher_user.id))
    assert exc.value.status_code == 409
