import uuid
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.handle import (
    HandleConfirmRequest,
    HandleInitiateRequest,
    HandleInitiateResponse,
    HandleResponse,
    HandleVerifiedResponse,
    SyncResponse,
)
from app.services.handle import (
    confirm_verification,
    get_handle_for_user,
    initiate_verification,
    list_handles,
    unlink_handle,
)
from app.workers.enqueue import enqueue_sync

router = APIRouter(prefix="/handles", tags=["handles"])


@router.get("", response_model=list[HandleResponse])
async def get_handles(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[HandleResponse]:
    handles = await list_handles(db, current_user.id)
    return [HandleResponse.model_validate(h) for h in handles]


@router.post("/verify/initiate", response_model=HandleInitiateResponse, status_code=status.HTTP_201_CREATED)
async def initiate(
    body: HandleInitiateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> HandleInitiateResponse:
    row = await initiate_verification(db, current_user.id, body.handle, body.platform)
    return HandleInitiateResponse(
        handle_id=row.id,
        handle=row.handle,
        platform=row.platform,
        token=row.verification_token,
        expires_at=row.verification_token_expires_at,
    )


@router.post("/verify/confirm", response_model=HandleVerifiedResponse)
async def confirm(
    body: HandleConfirmRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> HandleVerifiedResponse:
    row = await confirm_verification(db, current_user.id, body.handle_id)
    enqueue_sync(row.id, background_tasks)
    return HandleVerifiedResponse(
        handle_id=row.id,
        handle=row.handle,
        platform=row.platform,
        verified_at=row.verified_at,
    )


@router.post("/{handle_id}/sync", response_model=SyncResponse)
async def manual_sync(
    handle_id: uuid.UUID,
    background_tasks: BackgroundTasks,
    force: bool = False,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SyncResponse:
    handle = await get_handle_for_user(db, current_user.id, handle_id)

    # `force=true` lets the owner bypass the cooldown to recover a handle whose data
    # is missing/stale (e.g. a sync that stored 0 submissions). Owner-only via
    # get_handle_for_user, so it can't be abused against another account.
    cooldown = timedelta(minutes=30)
    if (
        not force
        and handle.last_manual_sync_at
        and datetime.now(UTC) - handle.last_manual_sync_at < cooldown
    ):
        retry_after = int((handle.last_manual_sync_at + cooldown - datetime.now(UTC)).total_seconds())
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={"message": "Sync cooldown active", "retry_after_seconds": retry_after},
        )

    handle.last_manual_sync_at = datetime.now(UTC)
    await db.commit()

    task_id = enqueue_sync(handle_id, background_tasks)
    return SyncResponse(task_id=task_id, handle_id=handle_id)


@router.delete("/{handle_id}", status_code=status.HTTP_204_NO_CONTENT)
async def unlink(
    handle_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    await unlink_handle(db, current_user.id, handle_id)
