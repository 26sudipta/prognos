"""Integration tests for CLIST sync: verifies DB upsert behavior with a real DB."""

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, patch

import pytest
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.models.analytics import Contest
from app.workers.clist_sync import _run_sync


def _make_async_session_factory():
    engine = create_async_engine(settings.DATABASE_URL, pool_pre_ping=True)
    factory = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    return engine, factory


def _make_objects(count: int = 2) -> list[dict]:
    base = datetime(2026, 7, 1, 10, 0, 0)
    return [
        {
            "id": 9000 + i,
            "resource": {"name": "codeforces.com"},
            "event": f"Test Contest {i}",
            "start": (base + timedelta(days=i)).strftime("%Y-%m-%dT%H:%M:%S"),
            "end": (base + timedelta(days=i, hours=2)).strftime("%Y-%m-%dT%H:%M:%S"),
            "duration": 7200,
            "href": f"https://codeforces.com/contest/{9000 + i}",
        }
        for i in range(count)
    ]


@pytest.fixture(autouse=True)
async def cleanup_contests():
    """Remove test-inserted contests after each test."""
    yield
    engine, factory = _make_async_session_factory()
    async with factory() as session:
        await session.execute(delete(Contest).where(Contest.clist_id.in_([9000, 9001])))
        await session.commit()
    await engine.dispose()


@pytest.mark.asyncio
async def test_run_sync_inserts_contests():
    objects = _make_objects(2)

    with patch("app.workers.clist_sync._fetch_contests", new=AsyncMock(return_value=objects)):
        result = await _run_sync()

    assert result == {"status": "ok", "upserted": 2}

    engine, factory = _make_async_session_factory()
    async with factory() as session:
        rows = (
            await session.execute(
                select(Contest).where(Contest.clist_id.in_([9000, 9001]))
            )
        ).scalars().all()
    await engine.dispose()

    assert len(rows) == 2
    assert {r.name for r in rows} == {"Test Contest 0", "Test Contest 1"}


@pytest.mark.asyncio
async def test_run_sync_upserts_on_conflict():
    """Second sync with updated name should UPDATE, not duplicate."""
    objects = _make_objects(1)

    with patch("app.workers.clist_sync._fetch_contests", new=AsyncMock(return_value=objects)):
        await _run_sync()

    objects[0]["event"] = "Renamed Contest"
    with patch("app.workers.clist_sync._fetch_contests", new=AsyncMock(return_value=objects)):
        result = await _run_sync()

    assert result["upserted"] == 1

    engine, factory = _make_async_session_factory()
    async with factory() as session:
        rows = (
            await session.execute(select(Contest).where(Contest.clist_id == 9000))
        ).scalars().all()
    await engine.dispose()

    assert len(rows) == 1
    assert rows[0].name == "Renamed Contest"


@pytest.mark.asyncio
async def test_run_sync_preserves_created_at_on_update():
    """created_at must not change when the row is updated."""
    objects = _make_objects(1)

    with patch("app.workers.clist_sync._fetch_contests", new=AsyncMock(return_value=objects)):
        await _run_sync()

    engine, factory = _make_async_session_factory()
    async with factory() as session:
        row_before = (
            await session.execute(select(Contest).where(Contest.clist_id == 9000))
        ).scalar_one()
        created_at_before = row_before.created_at
    await engine.dispose()

    objects[0]["event"] = "Updated Name"
    with patch("app.workers.clist_sync._fetch_contests", new=AsyncMock(return_value=objects)):
        await _run_sync()

    engine, factory = _make_async_session_factory()
    async with factory() as session:
        row_after = (
            await session.execute(select(Contest).where(Contest.clist_id == 9000))
        ).scalar_one()
    await engine.dispose()

    assert row_after.created_at == created_at_before
    assert row_after.name == "Updated Name"
