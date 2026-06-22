import uuid

from fastapi import APIRouter, Depends, status
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
)
from app.services.handle import (
    confirm_verification,
    initiate_verification,
    list_handles,
    unlink_handle,
)

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
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> HandleVerifiedResponse:
    row = await confirm_verification(db, current_user.id, body.handle_id)
    return HandleVerifiedResponse(
        handle_id=row.id,
        handle=row.handle,
        platform=row.platform,
        verified_at=row.verified_at,
    )


@router.delete("/{handle_id}", status_code=status.HTTP_204_NO_CONTENT)
async def unlink(
    handle_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    await unlink_handle(db, current_user.id, handle_id)
