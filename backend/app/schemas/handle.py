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
    is_locked: bool
    status: HandleStatus
    sync_status: HandleSyncStatus
    verified_at: datetime | None
    last_synced_at: datetime | None
    lockout_expires_at: datetime | None
    # Owner-only in-flight verification state — lets the frontend resume the pending
    # step after a refresh instead of dropping back to "enter handle" and minting a
    # new token. Only ever the caller's own single-use, expiring token.
    verification_token: str | None
    verification_token_expires_at: datetime | None

    model_config = {"from_attributes": True}


class ConfirmErrorResponse(BaseModel):
    detail: str
    attempts_remaining: int


class SyncResponse(BaseModel):
    task_id: str
    handle_id: uuid.UUID
