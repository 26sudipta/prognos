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


def _ensure_utc(dt: datetime | None) -> datetime | None:
    if dt is None:
        return None
    return dt if dt.tzinfo is not None else dt.replace(tzinfo=UTC)


async def get_contests(
    db: AsyncSession,
    platform: list[str] | None,
    from_dt: datetime | None,
    to_dt: datetime | None,
    limit: int,
    offset: int,
) -> ContestsListResponse:
    now, window_end = _default_window()
    from_dt = _ensure_utc(from_dt) or now
    to_dt = _ensure_utc(to_dt) or window_end

    # end_time > from_dt keeps live contests (already started, not yet finished) visible
    base_q = select(Contest).where(
        Contest.end_time > from_dt,
        Contest.start_time <= to_dt,
    )
    if platform:
        base_q = base_q.where(Contest.platform.in_(platform))

    total = await db.scalar(select(func.count()).select_from(base_q.subquery()))

    rows = (
        await db.execute(
            base_q.order_by(Contest.start_time.asc(), Contest.clist_id.asc()).limit(limit).offset(offset)
        )
    ).scalars().all()

    return ContestsListResponse(
        contests=[ContestItem.model_validate(r) for r in rows],
        total=total or 0,
        is_stale=await _is_stale(db),
    )


async def get_contests_calendar(
    db: AsyncSession,
    platform: list[str] | None,
    from_dt: datetime | None,
    to_dt: datetime | None,
) -> ContestsCalendarResponse:
    now, window_end = _default_window()
    from_dt = _ensure_utc(from_dt) or now
    to_dt = _ensure_utc(to_dt) or window_end

    q = select(Contest).where(
        Contest.end_time > from_dt,
        Contest.start_time <= to_dt,
    )
    if platform:
        q = q.where(Contest.platform.in_(platform))
    q = q.order_by(Contest.start_time.asc(), Contest.clist_id.asc())

    rows = (await db.execute(q)).scalars().all()

    grouped: dict[str, list[ContestItem]] = {}
    for row in rows:
        day_key = row.start_time.date().isoformat()
        grouped.setdefault(day_key, []).append(ContestItem.model_validate(row))

    days = [CalendarDay(date=d, contests=grouped[d]) for d in sorted(grouped)]

    return ContestsCalendarResponse(days=days, is_stale=await _is_stale(db))


async def get_platforms(db: AsyncSession) -> list[str]:
    now, window_end = _default_window()
    rows = (
        await db.execute(
            select(Contest.platform)
            .where(Contest.end_time > now, Contest.start_time <= window_end)
            .distinct()
            .order_by(Contest.platform.asc())
        )
    ).scalars().all()
    return list(rows)
