import uuid

from pydantic import BaseModel


class UserMe(BaseModel):
    id: uuid.UUID
    email: str
    name: str
    avatar_url: str | None
    is_active: bool

    model_config = {"from_attributes": True}
