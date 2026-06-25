import uuid
from datetime import datetime

from pydantic import BaseModel


class ContestItem(BaseModel):
    id: uuid.UUID
    clist_id: int
    platform: str
    name: str
    start_time: datetime
    end_time: datetime
    duration_seconds: int
    url: str
    last_synced_at: datetime

    model_config = {"from_attributes": True}


class ContestsListResponse(BaseModel):
    contests: list[ContestItem]
    total: int
    is_stale: bool


class CalendarDay(BaseModel):
    date: str  # ISO date YYYY-MM-DD (UTC)
    contests: list[ContestItem]


class ContestsCalendarResponse(BaseModel):
    days: list[CalendarDay]
    is_stale: bool
