from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.analytics import DashboardResponse, RatingHistoryResponse, TagStatsResponse
from app.services.analytics import get_dashboard, get_rating_history, get_tag_stats

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/dashboard", response_model=DashboardResponse)
async def dashboard(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DashboardResponse:
    return await get_dashboard(db, current_user.id)


@router.get("/tags", response_model=list[TagStatsResponse])
async def tag_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[TagStatsResponse]:
    return await get_tag_stats(db, current_user.id)


@router.get("/rating-history", response_model=list[RatingHistoryResponse])
async def rating_history(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[RatingHistoryResponse]:
    return await get_rating_history(db, current_user.id)
