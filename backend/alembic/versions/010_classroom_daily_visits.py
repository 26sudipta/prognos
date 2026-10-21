"""add classroom_daily_visits (Classroom v2 Slice 0 baseline)

One row per member per UTC day on which they opened a classroom. It is the
baseline the Classroom v2 league and later slices get measured against, so it
ships before anything visible changes. See docs/phase_6_0.md.

Revision ID: 010
Revises: 009
Create Date: 2026-10-21

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "010"
down_revision: str | None = "009"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "classroom_daily_visits",
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("classroom_id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("visit_date", sa.Date(), nullable=False),
        sa.ForeignKeyConstraint(["classroom_id"], ["classrooms.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "classroom_id", "user_id", "visit_date", name="uq_classroom_daily_visits"
        ),
    )
    op.create_index(
        "idx_classroom_daily_visits_user_id", "classroom_daily_visits", ["user_id"]
    )


def downgrade() -> None:
    op.drop_index("idx_classroom_daily_visits_user_id", table_name="classroom_daily_visits")
    op.drop_table("classroom_daily_visits")
