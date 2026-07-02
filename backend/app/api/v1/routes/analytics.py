from fastapi import APIRouter, BackgroundTasks, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.analytics import (
    DashboardResponse,
    RatingHistoryResponse,
    RecommendationSetResponse,
    TagStatsResponse,
    WeaknessSignalResponse,
)
from app.services.analytics import (
    get_dashboard,
    get_rating_history,
    get_recommendations,
    get_tag_stats,
    get_weaknesses,
    refresh_recommendations,
)

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/dashboard", response_model=DashboardResponse)
async def dashboard(
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DashboardResponse:
    return await get_dashboard(db, current_user.id, background_tasks)


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


@router.get("/weaknesses", response_model=list[WeaknessSignalResponse])
async def weaknesses(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[WeaknessSignalResponse]:
    return await get_weaknesses(db, current_user.id)


@router.get("/recommendations", response_model=RecommendationSetResponse | None)
async def recommendations(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> RecommendationSetResponse | None:
    return await get_recommendations(db, current_user.id)


@router.post("/recommendations/refresh", response_model=RecommendationSetResponse | None)
async def recommendations_refresh(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> RecommendationSetResponse | None:
    return await refresh_recommendations(db, current_user.id)
