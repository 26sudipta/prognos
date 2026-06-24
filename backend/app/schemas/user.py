import uuid

from pydantic import BaseModel, Field


class UserMe(BaseModel):
    id: uuid.UUID
    email: str
    name: str
    avatar_url: str | None
    is_active: bool

    model_config = {"from_attributes": True}


class UserUpdateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
