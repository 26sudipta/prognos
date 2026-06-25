from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.analytics import Contest
from app.schemas.contests import (
    CalendarDay,
    ContestItem,
    ContestsCalendarResponse,
    ContestsListResponse,
)

_STALE_THRESHOLD_HOURS = 8


async def _is_stale(db: AsyncSession) -> bool:
    max_synced = await db.scalar(select(func.max(Contest.last_synced_at)))
    if max_synced is None:
        return True
    return (datetime.now(UTC) - max_synced) > timedelta(hours=_STALE_THRESHOLD_HOURS)


def _default_window() -> tuple[datetime, datetime]:
    now = datetime.now(UTC)
    return now, now + timedelta(days=30)


async def get_contests(
    db: AsyncSession,
    platform: str | None,
    from_dt: datetime | None,
    to_dt: datetime | None,
    limit: int,
    offset: int,
) -> ContestsListResponse:
    now, window_end = _default_window()
    from_dt = from_dt or now
    to_dt = to_dt or window_end

    base_q = select(Contest).where(
        Contest.start_time >= from_dt,
        Contest.start_time <= to_dt,
    )
    if platform:
        base_q = base_q.where(Contest.platform == platform)

    total = await db.scalar(select(func.count()).select_from(base_q.subquery()))

    rows = (
        await db.execute(
            base_q.order_by(Contest.start_time.asc()).limit(limit).offset(offset)
        )
    ).scalars().all()

    return ContestsListResponse(
        contests=[ContestItem.model_validate(r) for r in rows],
        total=total or 0,
        is_stale=await _is_stale(db),
    )


async def get_contests_calendar(
    db: AsyncSession,
    platform: str | None,
    from_dt: datetime | None,
    to_dt: datetime | None,
) -> ContestsCalendarResponse:
    now, window_end = _default_window()
    from_dt = from_dt or now
    to_dt = to_dt or window_end

    q = select(Contest).where(
        Contest.start_time >= from_dt,
        Contest.start_time <= to_dt,
    )
    if platform:
        q = q.where(Contest.platform == platform)
    q = q.order_by(Contest.start_time.asc())

    rows = (await db.execute(q)).scalars().all()

    grouped: dict[str, list[ContestItem]] = {}
    for row in rows:
        day_key = row.start_time.date().isoformat()
        grouped.setdefault(day_key, []).append(ContestItem.model_validate(row))

    days = [CalendarDay(date=d, contests=grouped[d]) for d in sorted(grouped)]

    return ContestsCalendarResponse(days=days, is_stale=await _is_stale(db))


async def get_platforms(db: AsyncSession) -> list[str]:
    rows = (
        await db.execute(
            select(Contest.platform).distinct().order_by(Contest.platform.asc())
        )
    ).scalars().all()
    return list(rows)
