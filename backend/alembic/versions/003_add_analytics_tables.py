"""add_analytics_tables

Revision ID: 003
Revises: 002
Create Date: 2026-06-24

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "003"
down_revision: str | None = "002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # --- submissions ---
    op.create_table(
        "submissions",
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("user_handle_id", sa.UUID(), nullable=False),
        sa.Column("cf_submission_id", sa.BigInteger(), nullable=False),
        sa.Column("problem_id", sa.String(50), nullable=False),
        sa.Column("problem_name", sa.String(500), nullable=False),
        sa.Column("contest_id", sa.Integer(), nullable=True),
        sa.Column("verdict", sa.String(50), nullable=False),
        sa.Column("lang", sa.String(100), nullable=False),
        sa.Column("time_ms", sa.Integer(), nullable=True),
        sa.Column("memory_kb", sa.Integer(), nullable=True),
        sa.Column("submitted_at", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_handle_id"], ["user_handles.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("cf_submission_id"),
    )
    op.create_index("idx_submissions_user_handle_id", "submissions", ["user_handle_id"])
    op.create_index("idx_submissions_submitted_at", "submissions", ["submitted_at"])

    # --- submission_tags ---
    op.create_table(
        "submission_tags",
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("submission_id", sa.UUID(), nullable=False),
        sa.Column("tag", sa.String(100), nullable=False),
        sa.ForeignKeyConstraint(["submission_id"], ["submissions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_submission_tags_submission_id", "submission_tags", ["submission_id"])

    # --- daily_activity ---
    op.create_table(
        "daily_activity",
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("user_handle_id", sa.UUID(), nullable=False),
        sa.Column("activity_date", sa.Date(), nullable=False),
        sa.Column("submission_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("solved_count", sa.Integer(), nullable=False, server_default="0"),
        sa.ForeignKeyConstraint(["user_handle_id"], ["user_handles.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_handle_id", "activity_date", name="uq_daily_activity"),
    )
    op.create_index("idx_daily_activity_user_handle_id", "daily_activity", ["user_handle_id"])

    # --- tag_stats ---
    op.create_table(
        "tag_stats",
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("user_handle_id", sa.UUID(), nullable=False),
        sa.Column("tag", sa.String(100), nullable=False),
        sa.Column("solved_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("attempt_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("acceptance_rate", sa.Float(), nullable=False, server_default="0"),
        sa.Column("last_activity_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["user_handle_id"], ["user_handles.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_handle_id", "tag", name="uq_tag_stats"),
    )
    op.create_index("idx_tag_stats_user_handle_id", "tag_stats", ["user_handle_id"])

    # --- rating_history ---
    op.create_table(
        "rating_history",
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("user_handle_id", sa.UUID(), nullable=False),
        sa.Column("cf_contest_id", sa.Integer(), nullable=False),
        sa.Column("contest_name", sa.String(500), nullable=False),
        sa.Column("old_rating", sa.Integer(), nullable=False),
        sa.Column("new_rating", sa.Integer(), nullable=False),
        sa.Column("delta", sa.Integer(), nullable=False),
        sa.Column("rank", sa.Integer(), nullable=False),
        sa.Column("contest_time", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_handle_id"], ["user_handles.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_rating_history_user_handle_id", "rating_history", ["user_handle_id"])

    # --- weakness_signals ---
    signal_type_enum = sa.Enum(
        "neglected", "low_success", "under_practiced",
        name="weakness_signal_type",
    )
    op.create_table(
        "weakness_signals",
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("user_handle_id", sa.UUID(), nullable=False),
        sa.Column("tag", sa.String(100), nullable=False),
        sa.Column("signal_type", signal_type_enum, nullable=False),
        sa.Column("score", sa.Float(), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("computed_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["user_handle_id"], ["user_handles.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_weakness_signals_user_handle_id", "weakness_signals", ["user_handle_id"])

    # --- recommendation_sets ---
    op.create_table(
        "recommendation_sets",
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("generated_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_recommendation_sets_user_id", "recommendation_sets", ["user_id"])

    # --- recommendations ---
    op.create_table(
        "recommendations",
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("recommendation_set_id", sa.UUID(), nullable=False),
        sa.Column("problem_id", sa.String(50), nullable=False),
        sa.Column("problem_name", sa.String(500), nullable=False),
        sa.Column("tag", sa.String(100), nullable=False),
        sa.Column("difficulty", sa.Integer(), nullable=False),
        sa.Column("url", sa.Text(), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["recommendation_set_id"], ["recommendation_sets.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "idx_recommendations_set_id", "recommendations", ["recommendation_set_id"]
    )


def downgrade() -> None:
    op.drop_table("recommendations")
    op.drop_table("recommendation_sets")
    op.drop_table("weakness_signals")
    op.execute("DROP TYPE IF EXISTS weakness_signal_type")
    op.drop_table("rating_history")
    op.drop_table("tag_stats")
    op.drop_table("daily_activity")
    op.drop_table("submission_tags")
    op.drop_table("submissions")
