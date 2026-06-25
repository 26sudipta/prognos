import uuid
from datetime import UTC, date, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.analytics import DailyActivity, RatingHistory, TagStats
from app.models.signals import RecommendationSet, WeaknessSignal
from app.models.user_handle import UserHandle
from app.schemas.analytics import (
    DashboardResponse,
    HeatmapDay,
    RatingHistoryResponse,
    RecommendationSetResponse,
    TagStatsResponse,
    WeaknessSignalResponse,
)


async def _get_handle_ids(db: AsyncSession, user_id: uuid.UUID) -> list[uuid.UUID]:
    result = await db.execute(
        select(UserHandle.id).where(
            UserHandle.user_id == user_id,
            UserHandle.is_active.is_(True),
            UserHandle.is_verified.is_(True),
        )
    )
    return list(result.scalars().all())


def _compute_streaks(date_to_solved: dict[date, int]) -> tuple[int, int]:
    """Return (current_streak, longest_streak) from a date→solved_count mapping."""
    today = date.today()

    current = 0
    d = today
    while date_to_solved.get(d, 0) > 0:
        current += 1
        d -= timedelta(days=1)

    longest = 0
    run = 0
    prev: date | None = None
    for d in sorted(date_to_solved.keys()):
        if date_to_solved[d] > 0:
            if prev is not None and (d - prev).days == 1:
                run += 1
            else:
                run = 1
            longest = max(longest, run)
            prev = d
        else:
            prev = None

    return current, longest


async def get_dashboard(db: AsyncSession, user_id: uuid.UUID) -> DashboardResponse:
    handle_ids = await _get_handle_ids(db, user_id)

    if not handle_ids:
        return DashboardResponse(
            heatmap=[],
            current_streak=0,
            longest_streak=0,
            total_solved=0,
            cf_rating=None,
        )

    # Fetch all daily_activity rows across all handles (all time)
    rows = (
        await db.execute(
            select(DailyActivity.activity_date, DailyActivity.solved_count).where(
                DailyActivity.user_handle_id.in_(handle_ids)
            )
        )
    ).all()

    # Aggregate by date across handles
    date_to_solved: dict[date, int] = {}
    for activity_date, solved_count in rows:
        date_to_solved[activity_date] = date_to_solved.get(activity_date, 0) + solved_count

    total_solved = sum(date_to_solved.values())
    current_streak, longest_streak = _compute_streaks(date_to_solved)

    cutoff = date.today() - timedelta(days=364)
    heatmap = [
        HeatmapDay(date=d.isoformat(), count=count)
        for d, count in sorted(date_to_solved.items())
        if d >= cutoff and count > 0
    ]

    # Current rating = new_rating from the most recent rating_history row
    rating_row = (
        await db.execute(
            select(RatingHistory.new_rating)
            .where(RatingHistory.user_handle_id.in_(handle_ids))
            .order_by(RatingHistory.contest_time.desc())
            .limit(1)
        )
    ).scalar_one_or_none()

    return DashboardResponse(
        heatmap=heatmap,
        current_streak=current_streak,
        longest_streak=longest_streak,
        total_solved=total_solved,
        cf_rating=rating_row,
    )


async def get_tag_stats(db: AsyncSession, user_id: uuid.UUID) -> list[TagStatsResponse]:
    handle_ids = await _get_handle_ids(db, user_id)
    if not handle_ids:
        return []

    rows = (
        await db.execute(
            select(TagStats)
            .where(TagStats.user_handle_id.in_(handle_ids))
            .order_by(TagStats.solved_count.desc())
        )
    ).scalars().all()

    return [TagStatsResponse.model_validate(r) for r in rows]


async def get_rating_history(db: AsyncSession, user_id: uuid.UUID) -> list[RatingHistoryResponse]:
    handle_ids = await _get_handle_ids(db, user_id)
    if not handle_ids:
        return []

    rows = (
        await db.execute(
            select(RatingHistory)
            .where(RatingHistory.user_handle_id.in_(handle_ids))
            .order_by(RatingHistory.contest_time.asc())
        )
    ).scalars().all()

    return [RatingHistoryResponse.model_validate(r) for r in rows]


async def get_weaknesses(db: AsyncSession, user_id: uuid.UUID) -> list[WeaknessSignalResponse]:
    handle_ids = await _get_handle_ids(db, user_id)
    if not handle_ids:
        return []

    rows = (
        await db.execute(
            select(WeaknessSignal)
            .where(WeaknessSignal.user_handle_id.in_(handle_ids))
            .order_by(WeaknessSignal.score.desc())
        )
    ).scalars().all()

    return [WeaknessSignalResponse.model_validate(r) for r in rows]


async def get_recommendations(db: AsyncSession, user_id: uuid.UUID) -> RecommendationSetResponse | None:
    row = (
        await db.execute(
            select(RecommendationSet)
            .where(RecommendationSet.user_id == user_id)
            .order_by(RecommendationSet.generated_at.desc())
            .limit(1)
        )
    ).scalar_one_or_none()

    if row is None:
        return None

    # recommendations are selectin-loaded; sort by position
    row.recommendations.sort(key=lambda r: r.position)
    return RecommendationSetResponse.model_validate(row)
