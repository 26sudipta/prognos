"""add submissions.participant_type/team_id and the cf_problems catalogue

Classroom v2 Slice 1a, data fidelity (docs/phase_6_1.md). Growth Points need two
facts the sync used to throw away: whether a solve happened live in a contest,
in a virtual round or in practice (`author.participantType`), and how hard the
problem is (`problem.rating`). The first is stored on each submission. The
second lives in `cf_problems` and is joined at rebuild time on
`submissions.problem_id = cf_problems.problem_key`, so a problem Codeforces
rates days after its round needs no backfill.

Revision ID: 011
Revises: 010
Create Date: 2026-10-21

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "011"
down_revision: str | None = "010"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("submissions", sa.Column("participant_type", sa.String(24), nullable=True))
    op.add_column("submissions", sa.Column("team_id", sa.Integer(), nullable=True))
    op.create_index(
        "idx_submissions_handle_submitted_at", "submissions", ["user_handle_id", "submitted_at"]
    )

    op.create_table(
        "cf_problems",
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("problem_key", sa.String(50), nullable=False),
        sa.Column("contest_id", sa.Integer(), nullable=True),
        sa.Column("problem_index", sa.String(16), nullable=False),
        sa.Column("name", sa.String(500), nullable=False),
        sa.Column("rating", sa.Integer(), nullable=True),
        sa.Column(
            "tags",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'[]'::jsonb"),
            nullable=False,
        ),
        sa.Column("solved_count", sa.Integer(), nullable=True),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("problem_key", name="uq_cf_problems_problem_key"),
    )
    op.create_index("idx_cf_problems_contest_id", "cf_problems", ["contest_id"])


def downgrade() -> None:
    op.drop_index("idx_cf_problems_contest_id", table_name="cf_problems")
    op.drop_table("cf_problems")
    op.drop_index("idx_submissions_handle_submitted_at", table_name="submissions")
    op.drop_column("submissions", "team_id")
    op.drop_column("submissions", "participant_type")
