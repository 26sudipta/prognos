"""add refresh-token rotation lineage (grace-window rotation)

Lets token rotation tolerate concurrent multi-tab refreshes instead of 401-bouncing
the tab that loses the race. Two nullable columns on refresh_tokens:

- rotated_at: set when a token is revoked *by rotation* (a logout revoke leaves it
  NULL). A revoked token presented again within a short grace window of its rotated_at
  is treated as a benign sibling refresh and served a fresh pair, not rejected.
- replaced_by_id: self-FK to the child token the rotation minted — records the rotation
  chain for auditing / future reuse-detection. SET NULL on delete so it never blocks the
  user-delete cascade that hard-removes a user's tokens.

Revision ID: 009
Revises: 008
Create Date: 2026-07-18

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "009"
down_revision: str | None = "008"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "refresh_tokens",
        sa.Column("rotated_at", sa.TIMESTAMP(timezone=True), nullable=True),
    )
    op.add_column(
        "refresh_tokens",
        sa.Column("replaced_by_id", sa.UUID(), nullable=True),
    )
    op.create_foreign_key(
        "fk_refresh_tokens_replaced_by_id",
        "refresh_tokens",
        "refresh_tokens",
        ["replaced_by_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint(
        "fk_refresh_tokens_replaced_by_id", "refresh_tokens", type_="foreignkey"
    )
    op.drop_column("refresh_tokens", "replaced_by_id")
    op.drop_column("refresh_tokens", "rotated_at")
