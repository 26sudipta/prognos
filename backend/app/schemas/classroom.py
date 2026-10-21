import uuid
from datetime import date, datetime
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator

from app.services.league_rules import is_valid_timezone

MemberVisibility = Literal["full", "anonymous"]


def _clean_name(v: str) -> str:
    v = v.strip()
    if not v:
        raise ValueError("Classroom name cannot be empty")
    if len(v) > 255:
        raise ValueError("Classroom name must be 255 characters or fewer")
    return v


def _check_timezone(v: str | None) -> str | None:
    if v is not None and not is_valid_timezone(v):
        raise ValueError(f"Unknown timezone {v!r}; use an IANA name such as 'Asia/Dhaka'")
    return v


class ClassroomCreateRequest(BaseModel):
    name: str
    # The create form sends the creator's browser zone; omitted means UTC.
    timezone: str | None = None

    @field_validator("name")
    @classmethod
    def name_not_empty(cls, v: str) -> str:
        return _clean_name(v)

    @field_validator("timezone")
    @classmethod
    def timezone_known(cls, v: str | None) -> str | None:
        return _check_timezone(v)


class ClassroomUpdateRequest(BaseModel):
    """PATCH body. Every field is optional; only the ones sent change."""

    name: str | None = None
    timezone: str | None = None
    week_starts_on: int | None = Field(default=None, ge=0, le=6)
    member_visibility: MemberVisibility | None = None

    @field_validator("name")
    @classmethod
    def name_not_empty(cls, v: str | None) -> str | None:
        return None if v is None else _clean_name(v)

    @field_validator("timezone")
    @classmethod
    def timezone_known(cls, v: str | None) -> str | None:
        return _check_timezone(v)


class ClassroomResponse(BaseModel):
    id: uuid.UUID
    name: str
    owner_id: uuid.UUID
    is_active: bool
    created_at: datetime
    my_role: Literal["teacher", "student"]
    member_count: int
    # Added in Classroom v2 Slice 1. Additive only, so the shipped app keeps parsing.
    timezone: str = "UTC"
    week_starts_on: int = 0
    member_visibility: MemberVisibility = "full"

    model_config = {"from_attributes": True}


class ClassroomsListResponse(BaseModel):
    classrooms: list[ClassroomResponse]


class InviteResponse(BaseModel):
    id: uuid.UUID
    classroom_id: uuid.UUID
    token: str
    expires_at: datetime
    created_at: datetime
    invite_url: str
    is_active: bool

    model_config = {"from_attributes": True}


class InviteListResponse(BaseModel):
    invites: list[InviteResponse]


class JoinRequest(BaseModel):
    token: str


class JoinPreviewResponse(BaseModel):
    is_valid: bool
    classroom_name: str | None = None
    member_count: int | None = None
    error_code: str | None = None


class MemberResponse(BaseModel):
    user_id: uuid.UUID
    user_name: str
    avatar_url: str | None
    cf_handle: str | None
    role: str
    joined_at: datetime

    model_config = {"from_attributes": True}


class MembersListResponse(BaseModel):
    members: list[MemberResponse]


class LeaderboardEntry(BaseModel):
    rank: int
    user_id: uuid.UUID
    cf_handle: str
    user_name: str
    avatar_url: str | None
    cf_rating: int | None
    solved_count: int
    current_streak: int
    longest_streak: int
    days_active_30d: int
    last_active_at: datetime | None
    top_tags: list[dict[str, Any]] | None
    weak_tags: list[dict[str, Any]] | None
    computed_at: datetime
    is_me: bool

    model_config = {"from_attributes": True}


class LeaderboardResponse(BaseModel):
    classroom_id: uuid.UUID
    classroom_name: str
    entries: list[LeaderboardEntry]
    member_count: int
    computed_at: datetime | None
    # True while at least one member's handle is mid-sync, so the frontend can poll
    # and re-render as bulk-sync results land.
    syncing: bool = False


class ClassroomSyncResponse(BaseModel):
    classroom_id: uuid.UUID
    members_enqueued: int


class CohortTag(BaseModel):
    tag: str
    count: int


class CohortMemberAttendance(BaseModel):
    user_id: uuid.UUID
    user_name: str
    cf_handle: str
    days_active_30d: int


class CohortAnalytics(BaseModel):
    classroom_id: uuid.UUID
    classroom_name: str
    member_count: int
    class_average_rating: float | None
    most_neglected_tags: list[CohortTag]
    lowest_success_tags: list[CohortTag]
    student_attendance: list[CohortMemberAttendance]


# ── Weekly Growth League (Classroom v2 Slice 1) ──────────────────────────────

class LeagueTarget(BaseModel):
    display_name: str
    gp_gap: int


class LeagueMe(BaseModel):
    growth_points: int
    rank_in_bracket: int
    bracket: int
    ref_rating: int
    breakdown: dict[str, int]
    avg_last_4_weeks: float | None
    weeks_counted: int
    best_week_gp: int | None
    next_target: LeagueTarget | None
    tied_with: list[str]


class LeagueEntry(BaseModel):
    rank: int
    user_id: uuid.UUID
    display_name: str
    cf_handle: str | None
    avatar_url: str | None
    growth_points: int
    stretch_solves: int
    contests: int
    delta_vs_last_week: int | None
    is_me: bool
    # Teachers only; students get null (their own level is in `me`).
    ref_rating: int | None = None


class LeagueBracket(BaseModel):
    bracket: int
    rating_min: int
    rating_max: int
    size: int
    active_count: int
    entries: list[LeagueEntry]


class LeagueZeroGp(BaseModel):
    user_id: uuid.UUID
    display_name: str
    cf_handle: str | None
    bracket: int
    last_active_at: datetime | None


class LeaguePulse(BaseModel):
    active_members: int
    total_members: int
    median_gp: float
    stretch_solves: int
    contests: int
    prev_active_members: int | None = None
    prev_median_gp: float | None = None
    prev_stretch_solves: int | None = None
    prev_contests: int | None = None
    zero_gp: list[LeagueZeroGp]


class LeagueSuggestion(BaseModel):
    problem_id: str
    problem_name: str
    rating: int | None
    url: str
    tag: str
    band: str
    gp: int


class LeagueResponse(BaseModel):
    classroom_id: uuid.UUID
    week_start: date
    week_end: date
    status: Literal["live", "final", "empty"]
    closes_in_seconds: int
    finalizes_at: datetime | None
    timezone: str
    week_starts_on: int
    scoring_version: int
    me: LeagueMe | None
    brackets: list[LeagueBracket]
    pulse: LeaguePulse | None
    suggestions: list[LeagueSuggestion]
    computed_at: datetime | None
    syncing: bool = False


class LeagueHistoryWeek(BaseModel):
    week_start: date
    status: Literal["live", "final"]
    my_gp: int | None
    class_median: float | None   # teachers only


class LeagueHistoryResponse(BaseModel):
    weeks: list[LeagueHistoryWeek]
