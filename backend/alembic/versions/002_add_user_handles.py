"""add_user_handles

Revision ID: 002
Revises: 001
Create Date: 2026-06-20

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "002"
down_revision: str | None = "001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "user_handles",
        sa.Column(
            "id",
            sa.UUID(),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column(
            "platform",
            sa.Enum("codeforces", name="handle_platform"),
            nullable=False,
        ),
        sa.Column("handle", sa.String(255), nullable=False),
        sa.Column("is_verified", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column(
            "status",
            sa.Enum("active", "suspended", name="handle_status"),
            nullable=False,
            server_default=sa.text("'active'"),
        ),
        sa.Column("verification_token", sa.String(50), nullable=True),
        sa.Column("verification_token_expires_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column(
            "verification_attempt_count", sa.Integer(), nullable=False, server_default="0"
        ),
        sa.Column("is_locked", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("lockout_expires_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("verified_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column(
            "sync_status",
            sa.Enum("idle", "in_progress", "completed", "sync_error", name="handle_sync_status"),
            nullable=False,
            server_default=sa.text("'idle'"),
        ),
        sa.Column("last_synced_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("last_sync_error", sa.Text(), nullable=True),
        sa.Column("last_manual_sync_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index("idx_user_handles_user_id", "user_handles", ["user_id"])
    # Partial unique index: only one active handle per user per platform.
    # A full UNIQUE(user_id, platform, is_active) would block multiple historical
    # inactive rows (soft-deleted handles), so we filter to is_active = true only.
    op.create_index(
        "uq_user_handles_active_platform",
        "user_handles",
        ["user_id", "platform"],
        unique=True,
        postgresql_where=sa.text("is_active = true"),
    )


def downgrade() -> None:
    op.drop_index("uq_user_handles_active_platform", table_name="user_handles")
    op.drop_index("idx_user_handles_user_id", table_name="user_handles")
    op.drop_table("user_handles")
    op.execute("DROP TYPE handle_sync_status")
    op.execute("DROP TYPE handle_status")
    op.execute("DROP TYPE handle_platform")
