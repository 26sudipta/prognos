"""submissions unique per handle (fix cross-handle insert no-op)

The original `submissions.cf_submission_id` UNIQUE was GLOBAL. After a user re-verifies a
handle (which creates a new user_handles row), the new handle re-fetches the same CF
submission ids, but every insert collided with the rows already stored under the old
handle → ON CONFLICT DO NOTHING → 0 rows stored under the active handle → blank dashboard.
Scope uniqueness to (user_handle_id, cf_submission_id) so each handle stores its own rows.

Revision ID: 007
Revises: 006
Create Date: 2026-06-30

"""

from collections.abc import Sequence

from alembic import op

revision: str = "007"
down_revision: str | None = "006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Postgres auto-named the unnamed UniqueConstraint("cf_submission_id") from rev 003.
    op.drop_constraint("submissions_cf_submission_id_key", "submissions", type_="unique")
    op.create_unique_constraint(
        "uq_submissions_handle_cf_id",
        "submissions",
        ["user_handle_id", "cf_submission_id"],
    )


def downgrade() -> None:
    op.drop_constraint("uq_submissions_handle_cf_id", "submissions", type_="unique")
    op.create_unique_constraint(
        "submissions_cf_submission_id_key", "submissions", ["cf_submission_id"]
    )
