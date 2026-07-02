"""add classrooms.last_bulk_sync_at (bulk sync cooldown)

Backs the classroom "Sync" button: pressing it re-syncs every member from CF on the
server's own IP. This column records the last bulk sync so the endpoint can enforce a
per-classroom cooldown that protects the shared CF rate-limit budget.

Revision ID: 008
Revises: 007
Create Date: 2026-07-02

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "008"
down_revision: str | None = "007"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "classrooms",
        sa.Column("last_bulk_sync_at", sa.TIMESTAMP(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("classrooms", "last_bulk_sync_at")
