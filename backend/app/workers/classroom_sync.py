"""
Classroom leaderboard rebuild worker.

Runs every hour (beat task) and reactively after each CF sync.
Never queries raw submissions on the hot path — only reads from
pre-computed derived tables (daily_activity, tag_stats, rating_history,
weakness_signals).
"""

import asyncio
import logging
import uuid
from datetime import UTC, date, datetime, timedelta

from celery import shared_task
from sqlalchemy import delete, func, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.models.analytics import DailyActivity, RatingHistory, Submission, TagStats
from app.models.classroom import Classroom, ClassroomLeaderboard, ClassroomMembership
from app.models.signals import WeaknessSignal
from app.models.user import User
from app.models.user_handle import UserHandle
from app.services.analytics import _compute_streaks

logger = logging.getLogger(__name__)

DAYS_LOOKBACK_STREAK = 365
DAYS_LOOKBACK_ACTIVITY = 30


def _make_async_engine():
    return create_async_engine(settings.DATABASE_URL, pool_pre_ping=True)


# ---------------------------------------------------------------------------
# Celery tasks
# ---------------------------------------------------------------------------

@shared_task(bind=True, max_retries=3, default_retry_delay=30)
def rebuild_classroom_leaderboard(self, classroom_id: str) -> dict:
    """Rebuild the leaderboard cache for a single classroom."""
    try:
        return asyncio.run(_rebuild_async(uuid.UUID(classroom_id)))
    except Exception as exc:
        logger.exception("rebuild_classroom_leaderboard failed for %s", classroom_id)
        raise self.retry(exc=exc)


@shared_task
def rebuild_all_classroom_leaderboards() -> None:
    """Beat task: enqueue rebuild for every active classroom."""
    asyncio.run(_enqueue_all_classrooms())


# ---------------------------------------------------------------------------
# Async implementation
# ---------------------------------------------------------------------------

async def _enqueue_all_classrooms() -> None:
    engine = _make_async_engine()
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        result = await session.execute(
            select(Classroom.id).where(Classroom.is_active.is_(True))
        )
        classroom_ids = result.scalars().all()
    await engine.dispose()
    for cid in classroom_ids:
        rebuild_classroom_leaderboard.delay(str(cid))


async def rebuild_leaderboard(session: AsyncSession, classroom_id: uuid.UUID) -> int:
    """Rebuild the leaderboard cache for one classroom using the given session.

    DB-only (reads pre-computed derived tables), so it's cheap enough to run inline on
    the read path when the cache is empty/stale — which is how the worker-free (free-tier)
    deployment keeps leaderboards populated without a Celery broker.
    """
    result = await session.execute(
        select(ClassroomMembership).where(
            ClassroomMembership.classroom_id == classroom_id
        )
    )
    memberships = result.scalars().all()
    member_ids = [m.user_id for m in memberships]

    if not member_ids:
        return 0

    # Remove stale leaderboard rows (members who left)
    await session.execute(
        delete(ClassroomLeaderboard).where(
            ClassroomLeaderboard.classroom_id == classroom_id,
            ClassroomLeaderboard.user_id.notin_(member_ids),
        )
    )

    updated = 0
    for membership in memberships:
        try:
            row = await _build_leaderboard_row(session, classroom_id, membership.user_id)
            if row is None:
                continue  # no verified handle — preserve old row

            await session.execute(
                pg_insert(ClassroomLeaderboard)
                .values(**row)
                .on_conflict_do_update(
                    constraint="uq_classroom_leaderboard",
                    set_={k: v for k, v in row.items() if k not in ("classroom_id", "user_id")},
                )
            )
            updated += 1
        except Exception:
            logger.exception(
                "Failed to rebuild leaderboard row for user %s in classroom %s",
                membership.user_id, classroom_id,
            )

    await session.commit()
    return updated


async def _rebuild_async(classroom_id: uuid.UUID) -> dict:
    engine = _make_async_engine()
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        updated = await rebuild_leaderboard(session, classroom_id)
    await engine.dispose()
    return {"classroom_id": str(classroom_id), "updated": updated}


async def _build_leaderboard_row(
    session: AsyncSession, classroom_id: uuid.UUID, user_id: uuid.UUID
) -> dict | None:
    # Get user metadata
    user = await session.get(User, user_id)
    if not user:
        return None

    # Get verified active handle
    handle_result = await session.execute(
        select(UserHandle).where(
            UserHandle.user_id == user_id,
            UserHandle.is_verified.is_(True),
            UserHandle.is_active.is_(True),
        )
    )
    handle = handle_result.scalar_one_or_none()
    if not handle:
        return None  # signal partial failure — old row preserved

    handle_id = handle.id

    # CF rating — most recent contest
    rating_result = await session.execute(
        select(RatingHistory.new_rating)
        .where(RatingHistory.user_handle_id == handle_id)
        .order_by(RatingHistory.contest_time.desc())
        .limit(1)
    )
    cf_rating: int | None = rating_result.scalar_one_or_none()

    # Solved count — distinct accepted problems
    solved_result = await session.execute(
        select(func.count(Submission.problem_id.distinct())).where(
            Submission.user_handle_id == handle_id,
            Submission.verdict == "OK",
        )
    )
    solved_count: int = solved_result.scalar_one() or 0

    # Streaks — from daily_activity (last 365 days)
    cutoff = date.today() - timedelta(days=DAYS_LOOKBACK_STREAK)
    activity_result = await session.execute(
        select(DailyActivity.activity_date, DailyActivity.submission_count).where(
            DailyActivity.user_handle_id == handle_id,
            DailyActivity.activity_date >= cutoff,
        )
    )
    date_to_subs = {row.activity_date: row.submission_count for row in activity_result.all()}
    current_streak, longest_streak = _compute_streaks(date_to_subs)

    # Days active in last 30 days
    cutoff_30d = date.today() - timedelta(days=DAYS_LOOKBACK_ACTIVITY)
    active_30d_result = await session.execute(
        select(func.count()).where(
            DailyActivity.user_handle_id == handle_id,
            DailyActivity.activity_date >= cutoff_30d,
            DailyActivity.submission_count > 0,
        )
    )
    days_active_30d: int = active_30d_result.scalar_one() or 0

    # Last active date
    last_active_result = await session.execute(
        select(func.max(DailyActivity.activity_date)).where(
            DailyActivity.user_handle_id == handle_id,
            DailyActivity.submission_count > 0,
        )
    )
    last_active_date: date | None = last_active_result.scalar_one_or_none()
    last_active_at: datetime | None = (
        datetime.combine(last_active_date, datetime.min.time()).replace(tzinfo=UTC)
        if last_active_date else None
    )

    # Top 5 tags by solved count
    tags_result = await session.execute(
        select(TagStats.tag, TagStats.solved_count)
        .where(TagStats.user_handle_id == handle_id)
        .order_by(TagStats.solved_count.desc())
        .limit(5)
    )
    top_tags = [{"tag": row.tag, "solved_count": row.solved_count} for row in tags_result.all()]

    # Top 3 weakness signals by score
    signals_result = await session.execute(
        select(WeaknessSignal.tag, WeaknessSignal.signal_type, WeaknessSignal.score)
        .where(WeaknessSignal.user_handle_id == handle_id)
        .order_by(WeaknessSignal.score.desc())
        .limit(3)
    )
    weak_tags = [
        {"tag": row.tag, "signal_type": row.signal_type.value, "score": float(row.score)}
        for row in signals_result.all()
    ]

    return {
        "classroom_id": classroom_id,
        "user_id": user_id,
        "cf_handle": handle.handle,
        "user_name": user.name,
        "avatar_url": user.avatar_url,
        "cf_rating": cf_rating,
        "solved_count": solved_count,
        "current_streak": current_streak,
        "longest_streak": longest_streak,
        "days_active_30d": days_active_30d,
        "last_active_at": last_active_at,
        "top_tags": top_tags or None,
        "weak_tags": weak_tags or None,
        "computed_at": datetime.now(UTC),
    }
