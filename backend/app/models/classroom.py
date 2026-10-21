import enum
import uuid
from datetime import date, datetime

import sqlalchemy as sa
from sqlalchemy import UUID, Boolean, ForeignKey, Integer, SmallInteger, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base import TimestampMixin


class ClassroomMembershipRole(str, enum.Enum):
    TEACHER = "teacher"
    STUDENT = "student"


class Classroom(TimestampMixin, Base):
    __tablename__ = "classrooms"
    __table_args__ = (
        sa.CheckConstraint("week_starts_on BETWEEN 0 AND 6", name="ck_classrooms_week_starts_on"),
        sa.CheckConstraint(
            "member_visibility IN ('full', 'anonymous')", name="ck_classrooms_member_visibility"
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=sa.text("gen_random_uuid()"),
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    owner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")
    # When the classroom was last bulk-synced via the "Sync" button — drives the
    # per-classroom cooldown that protects the shared CF rate-limit budget.
    last_bulk_sync_at: Mapped[datetime | None] = mapped_column(
        sa.TIMESTAMP(timezone=True), nullable=True
    )
    # IANA zone the class's weeks and solve days follow (Classroom v2, Slice 1).
    timezone: Mapped[str] = mapped_column(String(64), nullable=False, server_default="UTC")
    # 0 = Monday ... 6 = Sunday, matching date.weekday().
    week_starts_on: Mapped[int] = mapped_column(SmallInteger, nullable=False, server_default="0")
    # 'full': classmates see names, handles, avatars. 'anonymous': students see aliases.
    member_visibility: Mapped[str] = mapped_column(
        String(16), nullable=False, server_default="full"
    )
    # Last alias number handed out. Only grows, so "Member 7" is never a second person.
    alias_seq: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")


class ClassroomInvite(Base):
    __tablename__ = "classroom_invites"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=sa.text("gen_random_uuid()"),
    )
    classroom_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("classrooms.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    token: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    created_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False,
    )
    expires_at: Mapped[datetime] = mapped_column(
        sa.TIMESTAMP(timezone=True), nullable=False
    )
    revoked_at: Mapped[datetime | None] = mapped_column(
        sa.TIMESTAMP(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        sa.TIMESTAMP(timezone=True),
        nullable=False,
        server_default=sa.text("now()"),
    )


class ClassroomMembership(Base):
    __tablename__ = "classroom_memberships"
    __table_args__ = (
        sa.UniqueConstraint("classroom_id", "user_id", name="uq_classroom_memberships"),
        sa.UniqueConstraint("classroom_id", "alias_no", name="uq_classroom_memberships_alias"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=sa.text("gen_random_uuid()"),
    )
    classroom_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("classrooms.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    role: Mapped[ClassroomMembershipRole] = mapped_column(
        sa.Enum(
            ClassroomMembershipRole,
            name="classroom_membership_role",
            values_callable=lambda x: [e.value for e in x],
        ),
        nullable=False,
    )
    invite_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("classroom_invites.id", ondelete="SET NULL"),
        nullable=True,
    )
    joined_at: Mapped[datetime] = mapped_column(
        sa.TIMESTAMP(timezone=True),
        nullable=False,
        server_default=sa.text("now()"),
    )
    # Stable per-class number behind the "Member 7" alias in anonymous classes.
    # Taken from classrooms.alias_seq under a row lock at join, never reused.
    alias_no: Mapped[int] = mapped_column(Integer, nullable=False)


class ClassroomLeaderboard(Base):
    __tablename__ = "classroom_leaderboard"
    __table_args__ = (
        sa.UniqueConstraint("classroom_id", "user_id", name="uq_classroom_leaderboard"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=sa.text("gen_random_uuid()"),
    )
    classroom_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("classrooms.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    cf_handle: Mapped[str] = mapped_column(String(255), nullable=False)
    user_name: Mapped[str] = mapped_column(String(255), nullable=False)
    avatar_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    cf_rating: Mapped[int | None] = mapped_column(Integer, nullable=True)
    solved_count: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    current_streak: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    longest_streak: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    days_active_30d: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    last_active_at: Mapped[datetime | None] = mapped_column(
        sa.TIMESTAMP(timezone=True), nullable=True
    )
    top_tags: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    weak_tags: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    computed_at: Mapped[datetime] = mapped_column(
        sa.TIMESTAMP(timezone=True),
        nullable=False,
        server_default=sa.text("now()"),
    )


class ClassroomDailyVisit(Base):
    """One row per member per UTC day on which they opened the classroom.

    Classroom v2 Slice 0 (docs/phase_6_0.md): the baseline that later slices are
    measured against. Written idempotently by the detail and leaderboard reads and
    never read on a request path. `visit_date` stays UTC for good, so baseline and
    pilot numbers remain comparable after classrooms gain their own timezone.
    """

    __tablename__ = "classroom_daily_visits"
    __table_args__ = (
        sa.UniqueConstraint(
            "classroom_id", "user_id", "visit_date", name="uq_classroom_daily_visits"
        ),
        sa.Index("idx_classroom_daily_visits_user_id", "user_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=sa.text("gen_random_uuid()"),
    )
    classroom_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("classrooms.id", ondelete="CASCADE"),
        nullable=False,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    visit_date: Mapped[date] = mapped_column(sa.Date, nullable=False)


class ClassroomWeeklyScore(Base):
    """One student's Growth Points for one week in one classroom (the league cache).

    Written only by `app.workers.league_sync`. `ref_rating` and `bracket` are frozen
    at the first build of the week. `status` flips from 'live' to 'final' once the
    week is past its grace period, after which the row never changes.
    """

    __tablename__ = "classroom_weekly_scores"
    __table_args__ = (
        sa.UniqueConstraint(
            "classroom_id", "user_id", "week_start", name="uq_classroom_weekly_scores"
        ),
        sa.CheckConstraint("status IN ('live', 'final')", name="ck_classroom_weekly_scores_status"),
        sa.Index("idx_classroom_weekly_scores_week", "classroom_id", "week_start", "bracket"),
        sa.Index("idx_classroom_weekly_scores_user_id", "user_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=sa.text("gen_random_uuid()"),
    )
    classroom_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("classrooms.id", ondelete="CASCADE"),
        nullable=False,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    week_start: Mapped[date] = mapped_column(sa.Date, nullable=False)
    ref_rating: Mapped[int] = mapped_column(Integer, nullable=False)
    bracket: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    growth_points: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    stretch_solves: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    breakdown: Mapped[dict] = mapped_column(
        JSONB, nullable=False, server_default=sa.text("'{}'::jsonb")
    )
    rank_in_bracket: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(8), nullable=False, server_default="live")
    scoring_version: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    computed_at: Mapped[datetime] = mapped_column(
        sa.TIMESTAMP(timezone=True),
        nullable=False,
        server_default=sa.text("now()"),
    )
