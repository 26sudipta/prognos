import uuid

from fastapi import APIRouter, BackgroundTasks, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.classroom import (
    ClassroomCreateRequest,
    ClassroomResponse,
    ClassroomsListResponse,
    ClassroomSyncResponse,
    CohortAnalytics,
    InviteListResponse,
    InviteResponse,
    JoinPreviewResponse,
    JoinRequest,
    LeaderboardResponse,
    MembersListResponse,
)
from app.services.classroom import (
    create_classroom,
    create_invite,
    delete_classroom,
    get_classroom,
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

router = APIRouter(prefix="/classrooms", tags=["classrooms"])


# ── Static / action routes first (before /{classroom_id} to avoid path capture) ──

@router.get("", response_model=ClassroomsListResponse)
async def list_classrooms(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ClassroomsListResponse:
    classrooms = await get_user_classrooms(db, current_user.id)
    return ClassroomsListResponse(classrooms=classrooms)


@router.post("", response_model=ClassroomResponse, status_code=status.HTTP_201_CREATED)
async def create_new_classroom(
    body: ClassroomCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ClassroomResponse:
    return await create_classroom(db, current_user, body.name)


@router.post("/join", response_model=ClassroomResponse, status_code=status.HTTP_201_CREATED)
async def join_via_invite(
    body: JoinRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ClassroomResponse:
    return await join_classroom(db, body.token, current_user)


@router.get("/join-preview/{token}", response_model=JoinPreviewResponse)
async def get_join_preview(
    token: str,
    db: AsyncSession = Depends(get_db),
) -> JoinPreviewResponse:
    """Public endpoint — no auth required. Returns classroom info for the invite landing page."""
    return await join_preview(db, token)


# ── Classroom-scoped routes ────────────────────────────────────────────────────

@router.get("/{classroom_id}", response_model=ClassroomResponse)
async def get_classroom_detail(
    classroom_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ClassroomResponse:
    return await get_classroom(db, classroom_id, current_user.id)


@router.delete("/{classroom_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_classroom_endpoint(
    classroom_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    await delete_classroom(db, classroom_id, current_user.id)


@router.get("/{classroom_id}/leaderboard", response_model=LeaderboardResponse)
async def get_classroom_leaderboard(
    classroom_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> LeaderboardResponse:
    return await get_leaderboard(db, classroom_id, current_user.id)


@router.post(
    "/{classroom_id}/sync",
    response_model=ClassroomSyncResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def sync_classroom_endpoint(
    classroom_id: uuid.UUID,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ClassroomSyncResponse:
    return await sync_classroom(db, classroom_id, current_user.id, background_tasks)


@router.get("/{classroom_id}/cohort", response_model=CohortAnalytics)
async def get_cohort(
    classroom_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CohortAnalytics:
    return await get_cohort_analytics(db, classroom_id, current_user.id)


@router.get("/{classroom_id}/members", response_model=MembersListResponse)
async def get_members(
    classroom_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> MembersListResponse:
    members = await list_members(db, classroom_id, current_user.id)
    return MembersListResponse(members=members)


@router.delete("/{classroom_id}/members/me", status_code=status.HTTP_204_NO_CONTENT)
async def leave_classroom_endpoint(
    classroom_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    await leave_classroom(db, classroom_id, current_user.id)


@router.delete("/{classroom_id}/members/{target_user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_member_endpoint(
    classroom_id: uuid.UUID,
    target_user_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    await remove_member(db, classroom_id, target_user_id, current_user.id)


# ── Invite routes ──────────────────────────────────────────────────────────────

@router.post(
    "/{classroom_id}/invites",
    response_model=InviteResponse,
    status_code=status.HTTP_201_CREATED,
)
async def generate_invite(
    classroom_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> InviteResponse:
    return await create_invite(db, classroom_id, current_user.id)


@router.get("/{classroom_id}/invites", response_model=InviteListResponse)
async def get_invites(
    classroom_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> InviteListResponse:
    invites = await list_invites(db, classroom_id, current_user.id)
    return InviteListResponse(invites=invites)


@router.delete(
    "/{classroom_id}/invites/{invite_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def revoke_invite_endpoint(
    classroom_id: uuid.UUID,
    invite_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    await revoke_invite(db, classroom_id, invite_id, current_user.id)
