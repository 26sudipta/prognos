import uuid
from datetime import date, datetime

import sqlalchemy as sa
from sqlalchemy import BigInteger, Date, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin


class Submission(Base):
    __tablename__ = "submissions"
    # Uniqueness is per-handle, NOT global: the same CF submission id legitimately
    # belongs under each user_handle row that owns the account (e.g. after a re-verify
    # creates a new handle row). A global unique made the new handle's inserts no-op.
    __table_args__ = (
        UniqueConstraint("user_handle_id", "cf_submission_id", name="uq_submissions_handle_cf_id"),
        # Weekly league windows scan one handle's submissions by time on every rebuild.
        sa.Index("idx_submissions_handle_submitted_at", "user_handle_id", "submitted_at"),
    )

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
    cf_submission_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    problem_id: Mapped[str] = mapped_column(String(50), nullable=False)
    problem_name: Mapped[str] = mapped_column(String(500), nullable=False)
    contest_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    verdict: Mapped[str] = mapped_column(String(50), nullable=False)
    lang: Mapped[str] = mapped_column(String(100), nullable=False)
    time_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    memory_kb: Mapped[int | None] = mapped_column(Integer, nullable=True)
    submitted_at: Mapped[datetime] = mapped_column(sa.TIMESTAMP(timezone=True), nullable=False, index=True)
    # CF `author.participantType`: CONTESTANT, OUT_OF_COMPETITION, VIRTUAL, PRACTICE or
    # MANAGER. NULL means "ingested before migration 011, not yet backfilled". UNKNOWN means
    # the backfill re-fetch no longer found the submission; it scores like PRACTICE.
    participant_type: Mapped[str | None] = mapped_column(String(24), nullable=True)
    # CF `author.teamId` for ICPC-style team submissions, NULL for individual ones. Team
    # solves can't be credited to one person, so the league skips their band points.
    team_id: Mapped[int | None] = mapped_column(Integer, nullable=True)

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


class Contest(TimestampMixin, Base):
    __tablename__ = "contests"

    id: Mapped[uuid.UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        primary_key=True,
        server_default=sa.text("gen_random_uuid()"),
    )
    clist_id: Mapped[int] = mapped_column(BigInteger, nullable=False, unique=True)
    platform: Mapped[str] = mapped_column(String(100), nullable=False)
    name: Mapped[str] = mapped_column(String(500), nullable=False)
    start_time: Mapped[datetime] = mapped_column(sa.TIMESTAMP(timezone=True), nullable=False, index=True)
    end_time: Mapped[datetime] = mapped_column(sa.TIMESTAMP(timezone=True), nullable=False)
    duration_seconds: Mapped[int] = mapped_column(Integer, nullable=False)
    url: Mapped[str] = mapped_column(Text, nullable=False)
    last_synced_at: Mapped[datetime] = mapped_column(sa.TIMESTAMP(timezone=True), nullable=False)


class CfProblem(Base):
    """Local mirror of Codeforces `problemset.problems`, refreshed at most once a day.

    `problem_key` uses the same format as `Submission.problem_id` (contest id + index,
    e.g. "1903A"), so ratings are joined at rebuild time instead of being copied onto
    submissions. Gym problems are absent from the problemset and simply stay unrated.
    """

    __tablename__ = "cf_problems"
    __table_args__ = (
        UniqueConstraint("problem_key", name="uq_cf_problems_problem_key"),
        sa.Index("idx_cf_problems_contest_id", "contest_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        primary_key=True,
        server_default=sa.text("gen_random_uuid()"),
    )
    problem_key: Mapped[str] = mapped_column(String(50), nullable=False)
    contest_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    problem_index: Mapped[str] = mapped_column(String(16), nullable=False)
    name: Mapped[str] = mapped_column(String(500), nullable=False)
    rating: Mapped[int | None] = mapped_column(Integer, nullable=True)
    tags: Mapped[list] = mapped_column(JSONB, nullable=False, server_default=sa.text("'[]'::jsonb"))
    solved_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("now()")
    )
