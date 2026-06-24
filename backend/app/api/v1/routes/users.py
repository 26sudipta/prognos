from fastapi import APIRouter, Depends, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.user import UserMe, UserUpdateRequest
from app.services.auth import soft_delete_user, update_user_name

router = APIRouter(prefix="/users", tags=["users"])

_REFRESH_COOKIE_PATH = "/api/v1/auth"


@router.get("/me", response_model=UserMe)
async def get_me(current_user: User = Depends(get_current_user)) -> UserMe:
    return UserMe.model_validate(current_user)


@router.patch("/me", response_model=UserMe)
async def update_me(
    body: UserUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> UserMe:
    updated = await update_user_name(db, str(current_user.id), body.name)
    return UserMe.model_validate(updated)


@router.delete("/me", status_code=204)
async def delete_me(
    response: Response,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    # TODO (Phase 4): block deletion if user owns active classrooms → 409 Conflict
    await soft_delete_user(db, str(current_user.id))
    response.delete_cookie(key="refresh_token", path=_REFRESH_COOKIE_PATH)
