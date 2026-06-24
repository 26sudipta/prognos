import uuid
from datetime import datetime

from pydantic import BaseModel

from app.models.signals import WeaknessSignalType


class HeatmapDay(BaseModel):
    date: str   # ISO format YYYY-MM-DD
    count: int  # total submissions (any verdict) — drives heatmap intensity, matches CF behavior
    solved: int # accepted submissions — shown in tooltip alongside total


class DashboardResponse(BaseModel):
    heatmap: list[HeatmapDay]
    current_streak: int
    longest_streak: int
    total_solved: int
    cf_rating: int | None
    has_verified_handle: bool
    is_syncing: bool = False  # True when handle sync is in-progress or has never completed


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


class WeaknessSignalResponse(BaseModel):
    id: uuid.UUID
    tag: str
    signal_type: WeaknessSignalType
    score: float
    reason: str
    computed_at: datetime

    model_config = {"from_attributes": True}


class RecommendationResponse(BaseModel):
    id: uuid.UUID
    problem_id: str
    problem_name: str
    tag: str
    difficulty: int
    url: str
    reason: str
    position: int

    model_config = {"from_attributes": True}


class RecommendationSetResponse(BaseModel):
    id: uuid.UUID
    generated_at: datetime
    recommendations: list[RecommendationResponse]

    model_config = {"from_attributes": True}
