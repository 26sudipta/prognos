"""add_missing_unique_constraints

Revision ID: 004
Revises: 003
Create Date: 2026-06-24

"""

from collections.abc import Sequence

from alembic import op

revision: str = "004"
down_revision: str | None = "003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_unique_constraint(
        "uq_rating_history_handle_contest",
        "rating_history",
        ["user_handle_id", "cf_contest_id"],
    )
    op.create_unique_constraint(
        "uq_weakness_signals_handle_tag_type",
        "weakness_signals",
        ["user_handle_id", "tag", "signal_type"],
    )


def downgrade() -> None:
    op.drop_constraint("uq_weakness_signals_handle_tag_type", "weakness_signals", type_="unique")
    op.drop_constraint("uq_rating_history_handle_contest", "rating_history", type_="unique")
