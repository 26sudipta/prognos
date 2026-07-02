import uuid
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, field_validator


class ClassroomCreateRequest(BaseModel):
    name: str

    @field_validator("name")
    @classmethod
    def name_not_empty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Classroom name cannot be empty")
        if len(v) > 255:
            raise ValueError("Classroom name must be 255 characters or fewer")
        return v


class ClassroomResponse(BaseModel):
    id: uuid.UUID
    name: str
    owner_id: uuid.UUID
    is_active: bool
    created_at: datetime
    my_role: Literal["teacher", "student"]
    member_count: int

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
