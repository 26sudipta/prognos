from fastapi import APIRouter, Depends

from app.api.v1.deps import get_current_user
from app.models.user import User
from app.schemas.user import UserMe

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserMe)
async def get_me(current_user: User = Depends(get_current_user)) -> UserMe:
    return UserMe.model_validate(current_user)
