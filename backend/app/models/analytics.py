import uuid
from datetime import date, datetime

import sqlalchemy as sa
from sqlalchemy import BigInteger, Date, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin


class Submission(Base):
    __tablename__ = "submissions"

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
    cf_submission_id: Mapped[int] = mapped_column(BigInteger, nullable=False, unique=True)
    problem_id: Mapped[str] = mapped_column(String(50), nullable=False)
    problem_name: Mapped[str] = mapped_column(String(500), nullable=False)
    contest_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    verdict: Mapped[str] = mapped_column(String(50), nullable=False)
    lang: Mapped[str] = mapped_column(String(100), nullable=False)
    time_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    memory_kb: Mapped[int | None] = mapped_column(Integer, nullable=True)
    submitted_at: Mapped[datetime] = mapped_column(sa.TIMESTAMP(timezone=True), nullable=False, index=True)

    tags: Mapped[list["SubmissionTag"]] = relationship(
        "SubmissionTag", back_populates="submission", lazy="selectin", cascade="all, delete-orphan"
    )
    handle: Mapped["UserHandle"] = relationship("UserHandle", lazy="noload")


class SubmissionTag(Base):
    __tablename__ = "submission_tags"

    id: Mapped[uuid.UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        primary_key=True,
        server_default=sa.text("gen_random_uuid()"),
    )
    submission_id: Mapped[uuid.UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        ForeignKey("submissions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    tag: Mapped[str] = mapped_column(String(100), nullable=False)

    submission: Mapped["Submission"] = relationship("Submission", back_populates="tags", lazy="noload")


class DailyActivity(Base):
    __tablename__ = "daily_activity"
    __table_args__ = (UniqueConstraint("user_handle_id", "activity_date", name="uq_daily_activity"),)

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
    activity_date: Mapped[date] = mapped_column(Date, nullable=False)
    submission_count: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    solved_count: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")

    handle: Mapped["UserHandle"] = relationship("UserHandle", lazy="noload")


class TagStats(Base):
    __tablename__ = "tag_stats"
    __table_args__ = (UniqueConstraint("user_handle_id", "tag", name="uq_tag_stats"),)

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
    solved_count: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    attempt_count: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    acceptance_rate: Mapped[float] = mapped_column(Float, nullable=False, server_default="0")
    last_activity_at: Mapped[datetime | None] = mapped_column(sa.TIMESTAMP(timezone=True), nullable=True)

    handle: Mapped["UserHandle"] = relationship("UserHandle", lazy="noload")


class RatingHistory(Base):
    __tablename__ = "rating_history"

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
    cf_contest_id: Mapped[int] = mapped_column(Integer, nullable=False)
    contest_name: Mapped[str] = mapped_column(String(500), nullable=False)
    old_rating: Mapped[int] = mapped_column(Integer, nullable=False)
    new_rating: Mapped[int] = mapped_column(Integer, nullable=False)
    delta: Mapped[int] = mapped_column(Integer, nullable=False)
    rank: Mapped[int] = mapped_column(Integer, nullable=False)
    contest_time: Mapped[datetime] = mapped_column(sa.TIMESTAMP(timezone=True), nullable=False)

    handle: Mapped["UserHandle"] = relationship("UserHandle", lazy="noload")
