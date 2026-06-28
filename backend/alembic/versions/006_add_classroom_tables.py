"""add_classroom_tables

Revision ID: 006
Revises: 005
Create Date: 2026-06-25

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision: str = "006"
down_revision: str | None = "005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # classrooms — must be created before child tables that FK to it
    op.create_table(
        "classrooms",
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("owner_id", sa.UUID(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["owner_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_classrooms_owner_id", "classrooms", ["owner_id"])

    # classroom_invites — FKs to classrooms + users
    op.create_table(
        "classroom_invites",
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("classroom_id", sa.UUID(), nullable=False),
        sa.Column("token", sa.String(64), nullable=False),
        sa.Column("created_by", sa.UUID(), nullable=False),
        sa.Column("expires_at", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["classroom_id"], ["classrooms.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("token", name="uq_classroom_invites_token"),
    )
    op.create_index("idx_classroom_invites_classroom_id", "classroom_invites", ["classroom_id"])

    # classroom_memberships — FKs to classrooms, users, classroom_invites
    op.create_table(
        "classroom_memberships",
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("classroom_id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column(
            "role",
            sa.Enum("teacher", "student", name="classroom_membership_role"),
            nullable=False,
        ),
        sa.Column("invite_id", sa.UUID(), nullable=True),
        sa.Column("joined_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["classroom_id"], ["classrooms.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["invite_id"], ["classroom_invites.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("classroom_id", "user_id", name="uq_classroom_memberships"),
    )
    op.create_index("idx_classroom_memberships_user_id", "classroom_memberships", ["user_id"])
    op.create_index("idx_classroom_memberships_classroom_id", "classroom_memberships", ["classroom_id"])

    # classroom_leaderboard — precomputed cache
    op.create_table(
        "classroom_leaderboard",
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("classroom_id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("cf_handle", sa.String(255), nullable=False),
        sa.Column("user_name", sa.String(255), nullable=False),
        sa.Column("avatar_url", sa.Text(), nullable=True),
        sa.Column("cf_rating", sa.Integer(), nullable=True),
        sa.Column("solved_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("current_streak", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("longest_streak", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("days_active_30d", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_active_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("top_tags", JSONB, nullable=True),
        sa.Column("weak_tags", JSONB, nullable=True),
        sa.Column("computed_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["classroom_id"], ["classrooms.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("classroom_id", "user_id", name="uq_classroom_leaderboard"),
    )
    op.create_index("idx_classroom_leaderboard_classroom_id", "classroom_leaderboard", ["classroom_id"])


def downgrade() -> None:
    op.drop_index("idx_classroom_leaderboard_classroom_id", table_name="classroom_leaderboard")
    op.drop_table("classroom_leaderboard")
    op.drop_index("idx_classroom_memberships_classroom_id", table_name="classroom_memberships")
    op.drop_index("idx_classroom_memberships_user_id", table_name="classroom_memberships")
    op.drop_table("classroom_memberships")
    op.execute("DROP TYPE classroom_membership_role")
    op.drop_index("idx_classroom_invites_classroom_id", table_name="classroom_invites")
    op.drop_table("classroom_invites")
    op.drop_index("idx_classrooms_owner_id", table_name="classrooms")
    op.drop_table("classrooms")
