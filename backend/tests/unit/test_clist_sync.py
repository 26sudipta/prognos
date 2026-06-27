"""Unit tests for the CLIST contest sync worker."""

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.workers.clist_sync import _fetch_contests, _map_contest, _run_sync


def _make_clist_object(
    clist_id: int = 1001,
    resource_name: str = "codeforces.com",
    event: str = "Codeforces Round 900",
    start: str = "2026-07-01T10:00:00",
    end: str = "2026-07-01T12:30:00",
    duration: int = 9000,
    href: str = "https://codeforces.com/contest/900",
) -> dict:
    return {
        "id": clist_id,
        "resource": resource_name,
        "event": event,
        "start": start,
        "end": end,
        "duration": duration,
        "href": href,
    }


# ---------------------------------------------------------------------------
# _map_contest
# ---------------------------------------------------------------------------


def test_map_contest_fields():
    synced_at = datetime(2026, 6, 24, 12, 0, 0, tzinfo=UTC)
    obj = _make_clist_object()
    row = _map_contest(obj, synced_at)

    assert row["clist_id"] == 1001
    assert row["platform"] == "codeforces.com"
    assert row["name"] == "Codeforces Round 900"
    assert row["duration_seconds"] == 9000
    assert row["url"] == "https://codeforces.com/contest/900"
    assert row["last_synced_at"] == synced_at
    assert row["created_at"] == synced_at
    assert row["updated_at"] == synced_at


def test_map_contest_naive_datetime_made_utc():
    """CLIST returns naive ISO strings — _map_contest must make them UTC-aware."""
    synced_at = datetime.now(UTC)
    obj = _make_clist_object(start="2026-07-01T10:00:00", end="2026-07-01T12:30:00")
    row = _map_contest(obj, synced_at)

    assert row["start_time"].tzinfo is not None
    assert row["end_time"].tzinfo is not None


def test_map_contest_tz_aware_datetime_preserved():
    """If CLIST ever returns timezone-aware strings, they should pass through unchanged."""
    synced_at = datetime.now(UTC)
    obj = _make_clist_object(start="2026-07-01T10:00:00+00:00", end="2026-07-01T12:30:00+00:00")
    row = _map_contest(obj, synced_at)

    assert row["start_time"].tzinfo is not None
    assert row["end_time"].tzinfo is not None


# ---------------------------------------------------------------------------
# _fetch_contests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_fetch_contests_passes_correct_params():
    now = datetime(2026, 6, 24, 10, 0, 0, tzinfo=UTC)
    window_end = now + timedelta(days=30)

    mock_response = MagicMock()
    mock_response.json.return_value = {"objects": [_make_clist_object()]}
    mock_response.raise_for_status = MagicMock()

    mock_client = AsyncMock()
    mock_client.get = AsyncMock(return_value=mock_response)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)

    with patch("app.workers.clist_sync.httpx.AsyncClient", return_value=mock_client):
        objects = await _fetch_contests(now, window_end)

    assert len(objects) == 1
    call_kwargs = mock_client.get.call_args
    params = call_kwargs.kwargs["params"]
    assert params["start__gt"] == "2026-06-24T10:00:00"
    assert params["start__lt"] == "2026-07-24T10:00:00"
    assert params["order_by"] == "start"
    assert params["limit"] == 200


@pytest.mark.asyncio
async def test_fetch_contests_returns_empty_on_empty_response():
    now = datetime.now(UTC)
    window_end = now + timedelta(days=30)

    mock_response = MagicMock()
    mock_response.json.return_value = {"objects": []}
    mock_response.raise_for_status = MagicMock()

    mock_client = AsyncMock()
    mock_client.get = AsyncMock(return_value=mock_response)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)

    with patch("app.workers.clist_sync.httpx.AsyncClient", return_value=mock_client):
        objects = await _fetch_contests(now, window_end)

    assert objects == []


# ---------------------------------------------------------------------------
# _run_sync — graceful degradation
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_run_sync_skips_on_http_error():
    """If CLIST API raises, _run_sync returns skipped without touching the DB."""
    with patch("app.workers.clist_sync._fetch_contests", new=AsyncMock(side_effect=Exception("timeout"))):
        result = await _run_sync()

    assert result["status"] == "skipped"
    assert result["reason"] == "api_error"


@pytest.mark.asyncio
async def test_run_sync_returns_zero_when_no_contests():
    with patch("app.workers.clist_sync._fetch_contests", new=AsyncMock(return_value=[])):
        result = await _run_sync()

    assert result == {"status": "ok", "upserted": 0}


@pytest.mark.asyncio
async def test_run_sync_upserts_and_returns_count():
    """With mocked engine and fetched objects, _run_sync reports correct count."""
    objects = [_make_clist_object(clist_id=i) for i in range(5)]

    mock_session = AsyncMock()
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=False)
    mock_session_maker = MagicMock(return_value=mock_session)
    mock_engine = AsyncMock()
    mock_engine.dispose = AsyncMock()

    with (
        patch("app.workers.clist_sync._fetch_contests", new=AsyncMock(return_value=objects)),
        patch("app.workers.clist_sync._make_async_engine", return_value=mock_engine),
        patch("app.workers.clist_sync.sessionmaker", return_value=mock_session_maker),
    ):
        result = await _run_sync()

    assert result == {"status": "ok", "upserted": 5}
    mock_session.execute.assert_awaited_once()
    mock_session.commit.assert_awaited_once()
    mock_engine.dispose.assert_awaited_once()
