"""Unit tests for the contests service layer."""

import uuid
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.contests import _is_stale, get_contests_calendar, get_platforms


# ---------------------------------------------------------------------------
# _is_stale
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_is_stale_when_no_rows():
    db = AsyncMock()
    db.scalar = AsyncMock(return_value=None)
    assert await _is_stale(db) is True


@pytest.mark.asyncio
async def test_is_stale_when_synced_recently():
    db = AsyncMock()
    db.scalar = AsyncMock(return_value=datetime.now(UTC) - timedelta(hours=3))
    assert await _is_stale(db) is False


@pytest.mark.asyncio
async def test_is_stale_when_over_threshold():
    db = AsyncMock()
    db.scalar = AsyncMock(return_value=datetime.now(UTC) - timedelta(hours=9))
    assert await _is_stale(db) is True


@pytest.mark.asyncio
async def test_is_stale_exactly_at_threshold_is_not_stale():
    """Boundary: exactly 8h means NOT stale (> 8h triggers staleness)."""
    db = AsyncMock()
    db.scalar = AsyncMock(return_value=datetime.now(UTC) - timedelta(hours=8, seconds=-1))
    assert await _is_stale(db) is False


# ---------------------------------------------------------------------------
# get_contests_calendar — grouping logic
# ---------------------------------------------------------------------------


def _make_contest(clist_id: int, start_offset_days: int):
    """Create a mock Contest ORM row."""
    base = datetime(2026, 7, 1, 10, 0, 0, tzinfo=UTC)
    start = base + timedelta(days=start_offset_days)
    obj = MagicMock()
    obj.id = uuid.uuid4()
    obj.clist_id = clist_id
    obj.platform = "codeforces.com"
    obj.name = f"Contest {clist_id}"
    obj.start_time = start
    obj.end_time = start + timedelta(hours=2)
    obj.duration_seconds = 7200
    obj.url = f"https://codeforces.com/contest/{clist_id}"
    obj.last_synced_at = datetime.now(UTC)
    return obj


@pytest.mark.asyncio
async def test_calendar_groups_by_utc_date():
    """Contests on the same UTC date must appear in the same day bucket."""
    # Two contests on 2026-07-01, one on 2026-07-02
    contests = [_make_contest(1, 0), _make_contest(2, 0), _make_contest(3, 1)]

    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = contests

    db = AsyncMock()
    db.execute = AsyncMock(return_value=mock_result)
    db.scalar = AsyncMock(return_value=datetime.now(UTC))  # not stale

    result = await get_contests_calendar(db, platform=None, from_dt=None, to_dt=None)

    assert len(result.days) == 2
    assert result.days[0].date == "2026-07-01"
    assert len(result.days[0].contests) == 2
    assert result.days[1].date == "2026-07-02"
    assert len(result.days[1].contests) == 1


@pytest.mark.asyncio
async def test_calendar_days_sorted_ascending():
    """Days must be sorted chronologically."""
    # Insert in reverse order
    contests = [_make_contest(3, 2), _make_contest(1, 0), _make_contest(2, 1)]

    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = contests

    db = AsyncMock()
    db.execute = AsyncMock(return_value=mock_result)
    db.scalar = AsyncMock(return_value=datetime.now(UTC))

    result = await get_contests_calendar(db, platform=None, from_dt=None, to_dt=None)

    dates = [d.date for d in result.days]
    assert dates == sorted(dates)


@pytest.mark.asyncio
async def test_calendar_empty_when_no_contests():
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = []

    db = AsyncMock()
    db.execute = AsyncMock(return_value=mock_result)
    db.scalar = AsyncMock(return_value=None)  # no rows → stale

    result = await get_contests_calendar(db, platform=None, from_dt=None, to_dt=None)

    assert result.days == []
    assert result.is_stale is True


# ---------------------------------------------------------------------------
# get_platforms — basic smoke test
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_platforms_returns_sorted_list():
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = ["atcoder.jp", "codeforces.com"]

    db = AsyncMock()
    db.execute = AsyncMock(return_value=mock_result)

    result = await get_platforms(db)
    assert result == ["atcoder.jp", "codeforces.com"]
