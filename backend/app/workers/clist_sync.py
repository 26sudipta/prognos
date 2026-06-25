"""
CLIST contest sync worker.

Fetches upcoming contests (now → now+30d) from clist.by and upserts
them into the contests table. Global data — not per-user.

Runs every 4 hours via Celery beat. Degrades gracefully: if the CLIST
API is unreachable, the last cached data in the DB stays intact.
"""

import asyncio
import logging
from datetime import UTC, datetime, timedelta

import httpx
from celery import shared_task
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.models.analytics import Contest

logger = logging.getLogger(__name__)

CLIST_API_BASE = "https://clist.by/api/v4"
LOOKAHEAD_DAYS = 30


def _make_async_engine():
    return create_async_engine(settings.DATABASE_URL, pool_pre_ping=True)


# ---------------------------------------------------------------------------
# Celery task
# ---------------------------------------------------------------------------


@shared_task(bind=True, max_retries=3, default_retry_delay=300)
def sync_clist_contests(self) -> dict:
    """Upsert upcoming contests from CLIST. Called by beat every 4h."""
    try:
        return asyncio.run(_run_sync())
    except Exception as exc:
        logger.exception("sync_clist_contests failed")
        raise self.retry(exc=exc)


# ---------------------------------------------------------------------------
# Core logic (importable for tests without Celery machinery)
# ---------------------------------------------------------------------------


async def _run_sync() -> dict:
    now = datetime.now(UTC)
    window_end = now + timedelta(days=LOOKAHEAD_DAYS)

    try:
        objects = await _fetch_contests(now, window_end)
    except Exception:
        logger.exception("CLIST API fetch failed — retaining cached data")
        return {"status": "skipped", "reason": "api_error"}

    if not objects:
        return {"status": "ok", "upserted": 0}

    synced_at = datetime.now(UTC)
    rows = [_map_contest(obj, synced_at) for obj in objects]

    engine = _make_async_engine()
    try:
        async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
        async with async_session() as session:
            stmt = pg_insert(Contest).values(rows)
            stmt = stmt.on_conflict_do_update(
                index_elements=["clist_id"],
                set_={
                    "platform": stmt.excluded.platform,
                    "name": stmt.excluded.name,
                    "start_time": stmt.excluded.start_time,
                    "end_time": stmt.excluded.end_time,
                    "duration_seconds": stmt.excluded.duration_seconds,
                    "url": stmt.excluded.url,
                    "last_synced_at": stmt.excluded.last_synced_at,
                    "updated_at": stmt.excluded.updated_at,
                    # created_at deliberately excluded: keep original insertion time
                },
            )
            await session.execute(stmt)
            await session.commit()
    finally:
        await engine.dispose()

    logger.info("CLIST sync complete: %d contests upserted", len(rows))
    return {"status": "ok", "upserted": len(rows)}


async def _fetch_contests(now: datetime, window_end: datetime) -> list[dict]:
    """Call CLIST API and return the raw objects list."""
    params = {
        "username": settings.CLIST_USERNAME,
        "api_key": settings.CLIST_API_KEY,
        "start__gt": now.strftime("%Y-%m-%dT%H:%M:%S"),
        "start__lt": window_end.strftime("%Y-%m-%dT%H:%M:%S"),
        "order_by": "start",
        "limit": 200,
    }
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(f"{CLIST_API_BASE}/contest/", params=params)
        resp.raise_for_status()
    return resp.json().get("objects", [])


def _map_contest(obj: dict, synced_at: datetime) -> dict:
    """Map a single CLIST API object to a contests row dict."""
    # CLIST returns naive ISO strings — they are UTC per CLIST documentation.
    def _parse_utc(s: str) -> datetime:
        dt = datetime.fromisoformat(s)
        return dt if dt.tzinfo is not None else dt.replace(tzinfo=UTC)

    return {
        "clist_id": obj["id"],
        "platform": obj["resource"]["name"],
        "name": obj["event"],
        "start_time": _parse_utc(obj["start"]),
        "end_time": _parse_utc(obj["end"]),
        "duration_seconds": obj["duration"],
        "url": obj["href"],
        "last_synced_at": synced_at,
        "created_at": synced_at,
        "updated_at": synced_at,
    }
