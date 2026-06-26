from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.contests import ContestsCalendarResponse, ContestsListResponse
from app.services.contests import get_contests, get_contests_calendar, get_platforms

router = APIRouter(prefix="/contests", tags=["contests"])


@router.get("", response_model=ContestsListResponse)
async def list_contests(
    platform: list[str] | None = Query(default=None),
    from_dt: datetime | None = Query(default=None),
    to_dt: datetime | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
) -> ContestsListResponse:
    return await get_contests(db, platform, from_dt, to_dt, limit, offset)


@router.get("/calendar", response_model=ContestsCalendarResponse)
async def contests_calendar(
    platform: list[str] | None = Query(default=None),
    from_dt: datetime | None = Query(default=None),
    to_dt: datetime | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
) -> ContestsCalendarResponse:
    return await get_contests_calendar(db, platform, from_dt, to_dt)


@router.get("/platforms", response_model=list[str])
async def list_platforms(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
) -> list[str]:
    return await get_platforms(db)
