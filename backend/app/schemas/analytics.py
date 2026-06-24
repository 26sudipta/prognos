from datetime import datetime

from pydantic import BaseModel


class HeatmapDay(BaseModel):
    date: str  # ISO format YYYY-MM-DD
    count: int


class DashboardResponse(BaseModel):
    heatmap: list[HeatmapDay]
    current_streak: int
    longest_streak: int
    total_solved: int
    cf_rating: int | None


class TagStatsResponse(BaseModel):
    tag: str
    solved_count: int
    attempt_count: int
    acceptance_rate: float
    last_activity_at: datetime | None

    model_config = {"from_attributes": True}


class RatingHistoryResponse(BaseModel):
    cf_contest_id: int
    contest_name: str
    old_rating: int
    new_rating: int
    delta: int
    rank: int
    contest_time: datetime

    model_config = {"from_attributes": True}
