import enum
import uuid
from datetime import datetime

import sqlalchemy as sa
from sqlalchemy import Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class WeaknessSignalType(str, enum.Enum):
    NEGLECTED = "neglected"
    LOW_SUCCESS = "low_success"
    UNDER_PRACTICED = "under_practiced"


class WeaknessSignal(Base):
    __tablename__ = "weakness_signals"

    id: Mapped[uuid.UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        primary_key=True,
        server_default=sa.text("gen_random_uuid()"),
    )
    user_handle_id: Mapped[uuid.UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        ForeignKey("user_handles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    tag: Mapped[str] = mapped_column(String(100), nullable=False)
    signal_type: Mapped[WeaknessSignalType] = mapped_column(
        sa.Enum(WeaknessSignalType, name="weakness_signal_type", values_callable=lambda x: [e.value for e in x]),
        nullable=False,
    )
    score: Mapped[float] = mapped_column(Float, nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    computed_at: Mapped[datetime] = mapped_column(
        sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()
    )

    handle: Mapped["UserHandle"] = relationship("UserHandle", lazy="noload")


class RecommendationSet(Base):
    __tablename__ = "recommendation_sets"

    id: Mapped[uuid.UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        primary_key=True,
        server_default=sa.text("gen_random_uuid()"),
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    generated_at: Mapped[datetime] = mapped_column(
        sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()
    )

    recommendations: Mapped[list["Recommendation"]] = relationship(
        "Recommendation", back_populates="recommendation_set", lazy="selectin", cascade="all, delete-orphan"
    )
    user: Mapped["User"] = relationship("User", lazy="noload")


class Recommendation(Base):
    __tablename__ = "recommendations"

    id: Mapped[uuid.UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        primary_key=True,
        server_default=sa.text("gen_random_uuid()"),
    )
    recommendation_set_id: Mapped[uuid.UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        ForeignKey("recommendation_sets.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    problem_id: Mapped[str] = mapped_column(String(50), nullable=False)
    problem_name: Mapped[str] = mapped_column(String(500), nullable=False)
    tag: Mapped[str] = mapped_column(String(100), nullable=False)
    difficulty: Mapped[int] = mapped_column(Integer, nullable=False)
    url: Mapped[str] = mapped_column(Text, nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    position: Mapped[int] = mapped_column(Integer, nullable=False)

    recommendation_set: Mapped["RecommendationSet"] = relationship(
        "RecommendationSet", back_populates="recommendations", lazy="noload"
    )
