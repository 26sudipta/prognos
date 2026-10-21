"""classroom league: class settings, member aliases, weekly scores

Classroom v2 Slice 1b (docs/phase_6_1.md).

- classrooms.timezone / week_starts_on: weeks and solve days follow the class's
  clock, not the server's UTC one.
- classrooms.member_visibility: 'full' or 'anonymous' (students see aliases).
- classroom_memberships.alias_no: a stable per-class number behind "Member 7".
  Existing members are numbered in join order. classrooms.alias_seq is the
  counter, so an alias is never handed to a second person, even after a leave.
- classroom_weekly_scores: the precomputed league cache, one row per student per
  week, the same compute-on-write pattern as classroom_leaderboard.

Revision ID: 012
Revises: 011
Create Date: 2026-10-21

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "012"
down_revision: str | None = "011"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "classrooms",
        sa.Column("timezone", sa.String(64), server_default="UTC", nullable=False),
    )
    op.add_column(
        "classrooms",
        sa.Column("week_starts_on", sa.SmallInteger(), server_default="0", nullable=False),
    )
    op.add_column(
        "classrooms",
        sa.Column("member_visibility", sa.String(16), server_default="full", nullable=False),
    )
    op.create_check_constraint(
        "ck_classrooms_week_starts_on", "classrooms", "week_starts_on BETWEEN 0 AND 6"
    )
    op.create_check_constraint(
        "ck_classrooms_member_visibility",
        "classrooms",
        "member_visibility IN ('full', 'anonymous')",
    )

    # Stable alias numbers, assigned in join order for existing members.
    op.add_column("classroom_memberships", sa.Column("alias_no", sa.Integer(), nullable=True))
    memberships = sa.table(
        "classroom_memberships",
        sa.column("id", sa.UUID()),
        sa.column("classroom_id", sa.UUID()),
        sa.column("joined_at", sa.TIMESTAMP(timezone=True)),
        sa.column("alias_no", sa.Integer()),
    )
    numbered = sa.select(
        memberships.c.id,
        sa.func.row_number()
        .over(
            partition_by=memberships.c.classroom_id,
            order_by=(memberships.c.joined_at, memberships.c.id),
        )
        .label("n"),
    ).subquery()
    op.execute(
        memberships.update().where(memberships.c.id == numbered.c.id).values(alias_no=numbered.c.n)
    )
    op.alter_column("classroom_memberships", "alias_no", nullable=False)

    op.add_column(
        "classrooms",
        sa.Column("alias_seq", sa.Integer(), server_default="0", nullable=False),
    )
    classrooms = sa.table(
        "classrooms", sa.column("id", sa.UUID()), sa.column("alias_seq", sa.Integer())
    )
    highest = (
        sa.select(memberships.c.classroom_id, sa.func.max(memberships.c.alias_no).label("top"))
        .group_by(memberships.c.classroom_id)
        .subquery()
    )
    op.execute(
        classrooms.update()
        .where(classrooms.c.id == highest.c.classroom_id)
        .values(alias_seq=highest.c.top)
    )
    op.create_unique_constraint(
        "uq_classroom_memberships_alias", "classroom_memberships", ["classroom_id", "alias_no"]
    )

    op.create_table(
        "classroom_weekly_scores",
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("classroom_id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("week_start", sa.Date(), nullable=False),
        sa.Column("ref_rating", sa.Integer(), nullable=False),
        sa.Column("bracket", sa.SmallInteger(), nullable=False),
        sa.Column("growth_points", sa.Integer(), server_default="0", nullable=False),
        sa.Column("stretch_solves", sa.Integer(), server_default="0", nullable=False),
        sa.Column(
            "breakdown",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column("rank_in_bracket", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(8), server_default="live", nullable=False),
        sa.Column("scoring_version", sa.SmallInteger(), nullable=False),
        sa.Column(
            "computed_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["classroom_id"], ["classrooms.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "classroom_id", "user_id", "week_start", name="uq_classroom_weekly_scores"
        ),
        sa.CheckConstraint("status IN ('live', 'final')", name="ck_classroom_weekly_scores_status"),
    )
    op.create_index(
        "idx_classroom_weekly_scores_week",
        "classroom_weekly_scores",
        ["classroom_id", "week_start", "bracket"],
    )
    op.create_index("idx_classroom_weekly_scores_user_id", "classroom_weekly_scores", ["user_id"])


def downgrade() -> None:
    op.drop_index("idx_classroom_weekly_scores_user_id", table_name="classroom_weekly_scores")
    op.drop_index("idx_classroom_weekly_scores_week", table_name="classroom_weekly_scores")
    op.drop_table("classroom_weekly_scores")
    op.drop_column("classrooms", "alias_seq")
    op.drop_constraint("uq_classroom_memberships_alias", "classroom_memberships", type_="unique")
    op.drop_column("classroom_memberships", "alias_no")
    op.drop_constraint("ck_classrooms_member_visibility", "classrooms", type_="check")
    op.drop_constraint("ck_classrooms_week_starts_on", "classrooms", type_="check")
    op.drop_column("classrooms", "member_visibility")
    op.drop_column("classrooms", "week_starts_on")
    op.drop_column("classrooms", "timezone")
