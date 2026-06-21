import enum
import uuid
from datetime import datetime

import sqlalchemy as sa
from sqlalchemy import UUID, Boolean, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin


class HandlePlatform(str, enum.Enum):
    CODEFORCES = "codeforces"


class HandleStatus(str, enum.Enum):
    ACTIVE = "active"
    SUSPENDED = "suspended"


class HandleSyncStatus(str, enum.Enum):
    IDLE = "idle"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    SYNC_ERROR = "sync_error"


class UserHandle(TimestampMixin, Base):
    __tablename__ = "user_handles"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=sa.text("gen_random_uuid()"),
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    platform: Mapped[HandlePlatform] = mapped_column(
        sa.Enum(HandlePlatform, name="handle_platform", values_callable=lambda x: [e.value for e in x]),
        nullable=False,
    )
    handle: Mapped[str] = mapped_column(String(255), nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")
    status: Mapped[HandleStatus] = mapped_column(
        sa.Enum(HandleStatus, name="handle_status", values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        server_default=sa.text("'active'"),
    )
    verification_token: Mapped[str | None] = mapped_column(String(50), nullable=True)
    verification_token_expires_at: Mapped[datetime | None] = mapped_column(
        sa.TIMESTAMP(timezone=True), nullable=True
    )
    verification_attempt_count: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default="0"
    )
    is_locked: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    lockout_expires_at: Mapped[datetime | None] = mapped_column(
        sa.TIMESTAMP(timezone=True), nullable=True
    )
    verified_at: Mapped[datetime | None] = mapped_column(
        sa.TIMESTAMP(timezone=True), nullable=True
    )
    sync_status: Mapped[HandleSyncStatus] = mapped_column(
        sa.Enum(HandleSyncStatus, name="handle_sync_status", values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        server_default=sa.text("'idle'"),
    )
    last_synced_at: Mapped[datetime | None] = mapped_column(
        sa.TIMESTAMP(timezone=True), nullable=True
    )
    last_sync_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    last_manual_sync_at: Mapped[datetime | None] = mapped_column(
        sa.TIMESTAMP(timezone=True), nullable=True
    )

    user: Mapped["User"] = relationship("User", back_populates="handles")
