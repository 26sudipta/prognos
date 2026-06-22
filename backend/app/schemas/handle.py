import uuid
from datetime import datetime

from pydantic import BaseModel

from app.models.user_handle import HandlePlatform, HandleStatus, HandleSyncStatus


class HandleInitiateRequest(BaseModel):
    handle: str
    platform: HandlePlatform = HandlePlatform.CODEFORCES


class HandleInitiateResponse(BaseModel):
    handle_id: uuid.UUID
    handle: str
    platform: HandlePlatform
    token: str
    expires_at: datetime


class HandleConfirmRequest(BaseModel):
    handle_id: uuid.UUID


class HandleVerifiedResponse(BaseModel):
    handle_id: uuid.UUID
    handle: str
    platform: HandlePlatform
    verified_at: datetime


class HandleResponse(BaseModel):
    id: uuid.UUID
    handle: str
    platform: HandlePlatform
    is_verified: bool
    status: HandleStatus
    sync_status: HandleSyncStatus
    verified_at: datetime | None
    last_synced_at: datetime | None

    model_config = {"from_attributes": True}


class ConfirmErrorResponse(BaseModel):
    detail: str
    attempts_remaining: int
