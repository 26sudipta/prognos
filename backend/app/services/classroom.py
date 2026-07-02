import logging
import secrets
import uuid
from collections import Counter
from datetime import UTC, datetime, timedelta
from statistics import mean
from typing import Any

from fastapi import BackgroundTasks, HTTPException, status
from sqlalchemy import delete, func, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.classroom import (
    Classroom,
    ClassroomInvite,
    ClassroomLeaderboard,
    ClassroomMembership,
    ClassroomMembershipRole,
)
from app.models.user import User
from app.models.user_handle import HandleSyncStatus, UserHandle
from app.schemas.classroom import (
    ClassroomResponse,
    ClassroomSyncResponse,
    CohortAnalytics,
    CohortMemberAttendance,
    CohortTag,
    InviteResponse,
    JoinPreviewResponse,
    LeaderboardEntry,
    LeaderboardResponse,
    MemberResponse,
)
from app.workers.enqueue import enqueue_sync

INVITE_EXPIRE_DAYS = 7


# ── Helpers ──────────────────────────────────────────────────────────────────

def _invite_url(token: str) -> str:
    return f"{settings.FRONTEND_URL}/join/{token}"


def _build_invite_response(invite: ClassroomInvite) -> InviteResponse:
    now = datetime.now(UTC)
    is_active = invite.revoked_at is None and invite.expires_at > now
    return InviteResponse(
        id=invite.id,
        classroom_id=invite.classroom_id,
        token=invite.token,
        expires_at=invite.expires_at,
        created_at=invite.created_at,
        invite_url=_invite_url(invite.token),
        is_active=is_active,
    )


async def _assert_member(db: AsyncSession, classroom_id: uuid.UUID, user_id: uuid.UUID) -> ClassroomMembership:
    """Return membership or raise 403."""
    result = await db.execute(
        select(ClassroomMembership).where(
            ClassroomMembership.classroom_id == classroom_id,
            ClassroomMembership.user_id == user_id,
        )
    )
    membership = result.scalar_one_or_none()
    if not membership:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not a member of this classroom")
    return membership


async def _assert_teacher(db: AsyncSession, classroom_id: uuid.UUID, user_id: uuid.UUID) -> None:
    """Raise 403 if user is not the teacher/owner of this classroom."""
    result = await db.execute(
        select(ClassroomMembership).where(
            ClassroomMembership.classroom_id == classroom_id,
            ClassroomMembership.user_id == user_id,
            ClassroomMembership.role == ClassroomMembershipRole.TEACHER,
        )
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the teacher can perform this action")


async def _get_classroom_or_404(db: AsyncSession, classroom_id: uuid.UUID) -> Classroom:
    result = await db.execute(
        select(Classroom).where(Classroom.id == classroom_id, Classroom.is_active.is_(True))
    )
    classroom = result.scalar_one_or_none()
    if not classroom:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Classroom not found")
    return classroom


async def _member_count(db: AsyncSession, classroom_id: uuid.UUID) -> int:
    result = await db.execute(
        select(func.count()).where(ClassroomMembership.classroom_id == classroom_id)
    )
    return result.scalar_one()


async def _build_classroom_response(
    db: AsyncSession, classroom: Classroom, user_id: uuid.UUID
) -> ClassroomResponse:
    membership = await _assert_member(db, classroom.id, user_id)
    count = await _member_count(db, classroom.id)
    return ClassroomResponse(
        id=classroom.id,
        name=classroom.name,
        owner_id=classroom.owner_id,
        is_active=classroom.is_active,
        created_at=classroom.created_at,
        my_role=membership.role.value,
        member_count=count,
    )


# ── Classroom CRUD ────────────────────────────────────────────────────────────

async def _require_verified_handle(db: AsyncSession, user_id: uuid.UUID, action: str) -> None:
    """Both teachers (create) and students (join) must own a verified CF handle —
    every classroom feature (leaderboard, cohort analytics) is built on that data."""
    handle_result = await db.execute(
        select(UserHandle).where(
            UserHandle.user_id == user_id,
            UserHandle.is_verified.is_(True),
            UserHandle.is_active.is_(True),
        )
    )
    if not handle_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Verify your Codeforces handle before {action} a classroom.",
        )


async def create_classroom(db: AsyncSession, user: User, name: str) -> ClassroomResponse:
    await _require_verified_handle(db, user.id, "creating")

    classroom = Classroom(name=name.strip(), owner_id=user.id)
    db.add(classroom)
    await db.flush()  # get classroom.id before creating membership

    membership = ClassroomMembership(
        classroom_id=classroom.id,
        user_id=user.id,
        role=ClassroomMembershipRole.TEACHER,
        invite_id=None,
    )
    db.add(membership)
    await db.commit()
    await db.refresh(classroom)

    return ClassroomResponse(
        id=classroom.id,
        name=classroom.name,
        owner_id=classroom.owner_id,
        is_active=classroom.is_active,
        created_at=classroom.created_at,
        my_role="teacher",
        member_count=1,
    )


async def get_user_classrooms(db: AsyncSession, user_id: uuid.UUID) -> list[ClassroomResponse]:
    result = await db.execute(
        select(ClassroomMembership, Classroom)
        .join(Classroom, ClassroomMembership.classroom_id == Classroom.id)
        .where(
            ClassroomMembership.user_id == user_id,
            Classroom.is_active.is_(True),
        )
        .order_by(Classroom.created_at.desc())
    )
    rows = result.all()

    responses = []
    for membership, classroom in rows:
        count = await _member_count(db, classroom.id)
        responses.append(ClassroomResponse(
            id=classroom.id,
            name=classroom.name,
            owner_id=classroom.owner_id,
            is_active=classroom.is_active,
            created_at=classroom.created_at,
            my_role=membership.role.value,
            member_count=count,
        ))
    return responses


async def get_classroom(db: AsyncSession, classroom_id: uuid.UUID, user_id: uuid.UUID) -> ClassroomResponse:
    classroom = await _get_classroom_or_404(db, classroom_id)
    return await _build_classroom_response(db, classroom, user_id)


async def delete_classroom(db: AsyncSession, classroom_id: uuid.UUID, user_id: uuid.UUID) -> None:
    classroom = await _get_classroom_or_404(db, classroom_id)
    if classroom.owner_id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the classroom owner can delete it")

    # Hard-delete operational data; soft-delete the classroom record itself
    await db.execute(delete(ClassroomLeaderboard).where(ClassroomLeaderboard.classroom_id == classroom_id))
    await db.execute(delete(ClassroomMembership).where(ClassroomMembership.classroom_id == classroom_id))
    await db.execute(delete(ClassroomInvite).where(ClassroomInvite.classroom_id == classroom_id))
    classroom.is_active = False
    await db.commit()


# ── Invites ───────────────────────────────────────────────────────────────────

async def create_invite(db: AsyncSession, classroom_id: uuid.UUID, user_id: uuid.UUID) -> InviteResponse:
    await _get_classroom_or_404(db, classroom_id)
    await _assert_teacher(db, classroom_id, user_id)

    token = secrets.token_urlsafe(32)
    expires_at = datetime.now(UTC) + timedelta(days=INVITE_EXPIRE_DAYS)
    invite = ClassroomInvite(
        classroom_id=classroom_id,
        token=token,
        created_by=user_id,
        expires_at=expires_at,
    )
    db.add(invite)
    await db.commit()
    await db.refresh(invite)
    return _build_invite_response(invite)


async def list_invites(db: AsyncSession, classroom_id: uuid.UUID, user_id: uuid.UUID) -> list[InviteResponse]:
    await _get_classroom_or_404(db, classroom_id)
    await _assert_teacher(db, classroom_id, user_id)

    now = datetime.now(UTC)
    result = await db.execute(
        select(ClassroomInvite).where(
            ClassroomInvite.classroom_id == classroom_id,
            ClassroomInvite.revoked_at.is_(None),
            ClassroomInvite.expires_at > now,
        ).order_by(ClassroomInvite.created_at.desc())
    )
    return [_build_invite_response(i) for i in result.scalars().all()]


async def revoke_invite(
    db: AsyncSession, classroom_id: uuid.UUID, invite_id: uuid.UUID, user_id: uuid.UUID
) -> None:
    await _get_classroom_or_404(db, classroom_id)
    await _assert_teacher(db, classroom_id, user_id)

    result = await db.execute(
        select(ClassroomInvite).where(
            ClassroomInvite.id == invite_id,
            ClassroomInvite.classroom_id == classroom_id,
        )
    )
    invite = result.scalar_one_or_none()
    if not invite:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invite not found")
    if invite.revoked_at is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Invite already revoked")

    invite.revoked_at = datetime.now(UTC)
    await db.commit()


# ── Join ──────────────────────────────────────────────────────────────────────

async def join_preview(db: AsyncSession, token: str) -> JoinPreviewResponse:
    """Lightweight public endpoint — returns classroom name without auth."""
    result = await db.execute(
        select(ClassroomInvite).where(ClassroomInvite.token == token)
    )
    invite = result.scalar_one_or_none()
    if not invite:
        return JoinPreviewResponse(is_valid=False, error_code="NOT_FOUND")
    if invite.revoked_at is not None:
        return JoinPreviewResponse(is_valid=False, error_code="REVOKED")
    if invite.expires_at < datetime.now(UTC):
        return JoinPreviewResponse(is_valid=False, error_code="EXPIRED")

    classroom_result = await db.execute(
        select(Classroom).where(Classroom.id == invite.classroom_id)
    )
    classroom = classroom_result.scalar_one_or_none()
    if not classroom or not classroom.is_active:
        return JoinPreviewResponse(is_valid=False, error_code="NOT_FOUND")

    count = await _member_count(db, classroom.id)
    return JoinPreviewResponse(is_valid=True, classroom_name=classroom.name, member_count=count)


async def join_classroom(db: AsyncSession, token: str, user: User) -> ClassroomResponse:
    # 1. Validate invite
    result = await db.execute(
        select(ClassroomInvite).where(ClassroomInvite.token == token)
    )
    invite = result.scalar_one_or_none()
    if not invite:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invite not found")
    if invite.revoked_at is not None:
        raise HTTPException(status_code=status.HTTP_410_GONE, detail="Invite link has been revoked")
    if invite.expires_at < datetime.now(UTC):
        raise HTTPException(status_code=status.HTTP_410_GONE, detail="Invite link has expired")

    # 2. Validate classroom
    classroom = await _get_classroom_or_404(db, invite.classroom_id)

    # 3. Require verified handle
    await _require_verified_handle(db, user.id, "joining")

    # 4. Check not already a member
    existing = await db.execute(
        select(ClassroomMembership).where(
            ClassroomMembership.classroom_id == classroom.id,
            ClassroomMembership.user_id == user.id,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="You're already a member of this classroom",
        )

    # 5. Create membership (unique constraint guards against concurrent joins)
    membership = ClassroomMembership(
        classroom_id=classroom.id,
        user_id=user.id,
        role=ClassroomMembershipRole.STUDENT,
        invite_id=invite.id,
    )
    db.add(membership)
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="You're already a member of this classroom",
        )

    count = await _member_count(db, classroom.id)
    return ClassroomResponse(
        id=classroom.id,
        name=classroom.name,
        owner_id=classroom.owner_id,
        is_active=classroom.is_active,
        created_at=classroom.created_at,
        my_role="student",
        member_count=count,
    )


# ── Members ───────────────────────────────────────────────────────────────────

async def list_members(db: AsyncSession, classroom_id: uuid.UUID, user_id: uuid.UUID) -> list[MemberResponse]:
    await _get_classroom_or_404(db, classroom_id)
    await _assert_member(db, classroom_id, user_id)

    result = await db.execute(
        select(ClassroomMembership, User)
        .join(User, ClassroomMembership.user_id == User.id)
        .where(ClassroomMembership.classroom_id == classroom_id)
        .order_by(ClassroomMembership.joined_at.asc())
    )
    rows = result.all()

    members = []
    for membership, user in rows:
        # Get verified handle if any
        handle_result = await db.execute(
            select(UserHandle.handle).where(
                UserHandle.user_id == user.id,
                UserHandle.is_verified.is_(True),
                UserHandle.is_active.is_(True),
            )
        )
        cf_handle = handle_result.scalar_one_or_none()
        members.append(MemberResponse(
            user_id=user.id,
            user_name=user.name,
            avatar_url=user.avatar_url,
            cf_handle=cf_handle,
            role=membership.role.value,
            joined_at=membership.joined_at,
        ))
    return members


async def remove_member(
    db: AsyncSession, classroom_id: uuid.UUID, target_user_id: uuid.UUID, requesting_user_id: uuid.UUID
) -> None:
    classroom = await _get_classroom_or_404(db, classroom_id)
    await _assert_teacher(db, classroom_id, requesting_user_id)

    if target_user_id == classroom.owner_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot remove the classroom owner",
        )

    result = await db.execute(
        select(ClassroomMembership).where(
            ClassroomMembership.classroom_id == classroom_id,
            ClassroomMembership.user_id == target_user_id,
        )
    )
    membership = result.scalar_one_or_none()
    if not membership:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Member not found")

    await db.delete(membership)
    # Immediately remove from leaderboard cache
    await db.execute(
        delete(ClassroomLeaderboard).where(
            ClassroomLeaderboard.classroom_id == classroom_id,
            ClassroomLeaderboard.user_id == target_user_id,
        )
    )
    await db.commit()


async def leave_classroom(db: AsyncSession, classroom_id: uuid.UUID, user_id: uuid.UUID) -> None:
    classroom = await _get_classroom_or_404(db, classroom_id)

    if classroom.owner_id == user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Classroom owner cannot leave — delete the classroom instead",
        )

    result = await db.execute(
        select(ClassroomMembership).where(
            ClassroomMembership.classroom_id == classroom_id,
            ClassroomMembership.user_id == user_id,
        )
    )
    membership = result.scalar_one_or_none()
    if not membership:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="You're not a member of this classroom")

    await db.delete(membership)
    await db.execute(
        delete(ClassroomLeaderboard).where(
            ClassroomLeaderboard.classroom_id == classroom_id,
            ClassroomLeaderboard.user_id == user_id,
        )
    )
    await db.commit()


# ── Leaderboard ───────────────────────────────────────────────────────────────

logger = logging.getLogger(__name__)

# How long a cached leaderboard is served before a read triggers an inline rebuild.
LEADERBOARD_TTL = timedelta(minutes=10)

# Minimum gap between "Sync" button presses for a classroom — protects the shared CF
# rate-limit budget (a full 100-member re-sync already takes ~3 min of CF calls).
BULK_SYNC_COOLDOWN = timedelta(minutes=15)


async def _classroom_syncing(db: AsyncSession, classroom_id: uuid.UUID) -> bool:
    """True if any member's verified handle is currently mid-sync."""
    result = await db.execute(
        select(func.count())
        .select_from(UserHandle)
        .join(ClassroomMembership, ClassroomMembership.user_id == UserHandle.user_id)
        .where(
            ClassroomMembership.classroom_id == classroom_id,
            UserHandle.is_verified.is_(True),
            UserHandle.is_active.is_(True),
            UserHandle.sync_status == HandleSyncStatus.IN_PROGRESS,
        )
    )
    return result.scalar_one() > 0


async def _fetch_leaderboard_rows(db: AsyncSession, classroom_id: uuid.UUID):
    result = await db.execute(
        select(ClassroomLeaderboard)
        .where(ClassroomLeaderboard.classroom_id == classroom_id)
        .order_by(
            ClassroomLeaderboard.cf_rating.desc().nulls_last(),
            ClassroomLeaderboard.solved_count.desc(),
        )
        # populate_existing: sessions use expire_on_commit=False, so after an inline
        # rebuild (a Core upsert + commit) the identity-mapped rows would otherwise be
        # returned stale. Force fresh DB values so the rebuild is reflected immediately.
        .execution_options(populate_existing=True)
    )
    return result.scalars().all()


async def _max_member_sync(db: AsyncSession, classroom_id: uuid.UUID):
    """Newest last_synced_at across the classroom's verified members (None if none synced)."""
    result = await db.execute(
        select(func.max(UserHandle.last_synced_at))
        .select_from(UserHandle)
        .join(ClassroomMembership, ClassroomMembership.user_id == UserHandle.user_id)
        .where(
            ClassroomMembership.classroom_id == classroom_id,
            UserHandle.is_verified.is_(True),
            UserHandle.is_active.is_(True),
        )
    )
    return result.scalar_one_or_none()


async def _ensure_leaderboard(db: AsyncSession, classroom_id: uuid.UUID, member_count: int):
    """Return leaderboard rows, rebuilding the cache inline when it's empty, stale, or behind.

    The worker-free (free-tier) deployment has no broker, so `_trigger_leaderboard_rebuilds`
    (`.delay()`) is a no-op — nothing rebuilds the cache after a member sync. So we also rebuild
    on read whenever a member's data is newer than the board ("behind"): this makes on-demand and
    cron syncs reflect promptly (and gives live incremental updates while a bulk sync runs) instead
    of waiting out the TTL. DB-only → stays fast, and self-limits (after a rebuild the board is no
    longer behind).
    """
    rows = await _fetch_leaderboard_rows(db, classroom_id)
    newest = rows[0].computed_at if rows else None
    is_stale = newest is None or (datetime.now(UTC) - newest) > LEADERBOARD_TTL

    is_behind = False
    if member_count > 0 and not is_stale:
        max_sync = await _max_member_sync(db, classroom_id)
        is_behind = max_sync is not None and (newest is None or max_sync > newest)

    if member_count > 0 and (is_stale or is_behind):
        from app.workers.classroom_sync import rebuild_leaderboard
        try:
            await rebuild_leaderboard(db, classroom_id)
            rows = await _fetch_leaderboard_rows(db, classroom_id)
        except Exception:
            logger.exception("inline leaderboard rebuild failed for %s", classroom_id)
    return rows


async def get_leaderboard(
    db: AsyncSession, classroom_id: uuid.UUID, user_id: uuid.UUID
) -> LeaderboardResponse:
    classroom = await _get_classroom_or_404(db, classroom_id)
    await _assert_member(db, classroom_id, user_id)

    member_count = await _member_count(db, classroom_id)
    rows = await _ensure_leaderboard(db, classroom_id, member_count)

    entries = []
    for rank, row in enumerate(rows, start=1):
        entries.append(LeaderboardEntry(
            rank=rank,
            user_id=row.user_id,
            cf_handle=row.cf_handle,
            user_name=row.user_name,
            avatar_url=row.avatar_url,
            cf_rating=row.cf_rating,
            solved_count=row.solved_count,
            current_streak=row.current_streak,
            longest_streak=row.longest_streak,
            days_active_30d=row.days_active_30d,
            last_active_at=row.last_active_at,
            top_tags=row.top_tags,
            weak_tags=row.weak_tags,
            computed_at=row.computed_at,
            is_me=(row.user_id == user_id),
        ))

    computed_at = rows[0].computed_at if rows else None

    return LeaderboardResponse(
        classroom_id=classroom.id,
        classroom_name=classroom.name,
        entries=entries,
        member_count=member_count,
        computed_at=computed_at,
        syncing=await _classroom_syncing(db, classroom_id),
    )


async def sync_classroom(
    db: AsyncSession,
    classroom_id: uuid.UUID,
    user_id: uuid.UUID,
    background_tasks: BackgroundTasks,
) -> ClassroomSyncResponse:
    """Bulk-sync every member of a classroom from CF, top→bottom of the leaderboard.

    Any member (teacher or student) may trigger it. Clients never send CF data — the
    server fetches authoritatively on its own IP, so the leaderboard can only ever
    reflect real Codeforces data. Enqueued syncs run through the shared rate-limited
    path (Celery, else sequential BackgroundTasks with a 2s inter-call delay).
    """
    classroom = await _get_classroom_or_404(db, classroom_id)
    await _assert_member(db, classroom_id, user_id)

    now = datetime.now(UTC)
    if classroom.last_bulk_sync_at and now - classroom.last_bulk_sync_at < BULK_SYNC_COOLDOWN:
        retry_after = int(
            (classroom.last_bulk_sync_at + BULK_SYNC_COOLDOWN - now).total_seconds()
        )
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "message": "Classroom sync cooldown active",
                "retry_after_seconds": retry_after,
            },
        )

    # Order members by current leaderboard rank so the visible top of the board
    # refreshes first; append any members missing from the cache (e.g. never synced).
    member_count = await _member_count(db, classroom_id)
    rows = await _ensure_leaderboard(db, classroom_id, member_count)
    ordered_user_ids = [r.user_id for r in rows]

    all_members = (
        await db.execute(
            select(ClassroomMembership.user_id).where(
                ClassroomMembership.classroom_id == classroom_id
            )
        )
    ).scalars().all()
    for mid in all_members:
        if mid not in ordered_user_ids:
            ordered_user_ids.append(mid)

    # Map each member to their verified CF handle_id, preserving leaderboard order.
    handle_rows = (
        await db.execute(
            select(UserHandle.user_id, UserHandle.id).where(
                UserHandle.user_id.in_(ordered_user_ids),
                UserHandle.is_verified.is_(True),
                UserHandle.is_active.is_(True),
            )
        )
    ).all()
    user_to_handle = {uid: hid for uid, hid in handle_rows}
    ordered_handle_ids = [
        user_to_handle[uid] for uid in ordered_user_ids if uid in user_to_handle
    ]

    # Pre-mark handles in_progress so the leaderboard read that fires immediately after this
    # response deterministically reports syncing=true and the frontend starts polling — the
    # enqueued BackgroundTasks only run *after* the response. Safe: _sync_handle_async always
    # runs regardless of status and cron re-syncs all verified handles, so a handle can't get
    # stuck if a task fails to run.
    if ordered_handle_ids:
        await db.execute(
            update(UserHandle)
            .where(UserHandle.id.in_(ordered_handle_ids))
            .values(sync_status=HandleSyncStatus.IN_PROGRESS)
        )

    for handle_id in ordered_handle_ids:
        enqueue_sync(handle_id, background_tasks)

    classroom.last_bulk_sync_at = now
    await db.commit()

    return ClassroomSyncResponse(
        classroom_id=classroom_id, members_enqueued=len(ordered_handle_ids)
    )


# ── Cohort Analytics ──────────────────────────────────────────────────────────

async def get_cohort_analytics(
    db: AsyncSession, classroom_id: uuid.UUID, user_id: uuid.UUID
) -> CohortAnalytics:
    classroom = await _get_classroom_or_404(db, classroom_id)
    await _assert_teacher(db, classroom_id, user_id)

    # Cohort stats derive from the leaderboard cache — build/refresh it on read too, so
    # the teacher's analytics panel isn't empty on the worker-free deployment.
    member_count = await _member_count(db, classroom_id)
    entries = await _ensure_leaderboard(db, classroom_id, member_count)

    ratings = [e.cf_rating for e in entries if e.cf_rating is not None]
    class_average_rating: float | None = mean(ratings) if ratings else None

    neglected_counter: Counter[str] = Counter()
    low_success_counter: Counter[str] = Counter()
    for e in entries:
        for wt in (e.weak_tags or []):
            sig_type = wt.get("signal_type", "")
            tag = wt.get("tag", "")
            if not tag:
                continue
            if sig_type == "neglected":
                neglected_counter[tag] += 1
            elif sig_type == "low_success":
                low_success_counter[tag] += 1

    most_neglected = [CohortTag(tag=t, count=c) for t, c in neglected_counter.most_common(5)]
    lowest_success = [CohortTag(tag=t, count=c) for t, c in low_success_counter.most_common(5)]

    attendance = sorted(
        [
            CohortMemberAttendance(
                user_id=e.user_id,
                user_name=e.user_name,
                cf_handle=e.cf_handle,
                days_active_30d=e.days_active_30d,
            )
            for e in entries
        ],
        key=lambda x: x.days_active_30d,
        reverse=True,
    )

    return CohortAnalytics(
        classroom_id=classroom.id,
        classroom_name=classroom.name,
        member_count=member_count,
        class_average_rating=class_average_rating,
        most_neglected_tags=most_neglected,
        lowest_success_tags=lowest_success,
        student_attendance=attendance,
    )
