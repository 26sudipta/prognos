"""Unit tests for weakness signal detection logic."""

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
import uuid

import pytest

from app.models.analytics import TagStats
from app.models.signals import WeaknessSignalType
from app.workers.cf_sync import _compute_weakness_signals


def _make_tag_stats(
    handle_id: uuid.UUID,
    tag: str,
    solved_count: int = 0,
    attempt_count: int = 0,
    acceptance_rate: float = 0.0,
    last_activity_at: datetime | None = None,
) -> TagStats:
    row = TagStats()
    row.user_handle_id = handle_id
    row.tag = tag
    row.solved_count = solved_count
    row.attempt_count = attempt_count
    row.acceptance_rate = acceptance_rate
    row.last_activity_at = last_activity_at
    return row


@pytest.mark.asyncio
async def test_neglected_signal_fires():
    handle_id = uuid.uuid4()
    stale_date = datetime.now(UTC) - timedelta(days=20)
    row = _make_tag_stats(handle_id, "dp", solved_count=3, last_activity_at=stale_date)

    added: list = []
    session = MagicMock()
    session.execute = AsyncMock(return_value=MagicMock(scalars=MagicMock(return_value=MagicMock(all=MagicMock(return_value=[row])))))
    session.add_all = lambda items: added.extend(items)
    session.commit = AsyncMock()

    await _compute_weakness_signals(handle_id, session)

    assert len(added) == 1
    assert added[0].signal_type == WeaknessSignalType.NEGLECTED
    assert added[0].tag == "dp"


@pytest.mark.asyncio
async def test_low_success_signal_fires():
    handle_id = uuid.uuid4()
    row = _make_tag_stats(handle_id, "graphs", solved_count=2, attempt_count=10, acceptance_rate=0.20)

    added: list = []
    session = MagicMock()
    session.execute = AsyncMock(return_value=MagicMock(scalars=MagicMock(return_value=MagicMock(all=MagicMock(return_value=[row])))))
    session.add_all = lambda items: added.extend(items)
    session.commit = AsyncMock()

    await _compute_weakness_signals(handle_id, session)

    assert len(added) == 1
    assert added[0].signal_type == WeaknessSignalType.LOW_SUCCESS
    assert added[0].score > 0


@pytest.mark.asyncio
async def test_under_practiced_signal_fires():
    handle_id = uuid.uuid4()
    row = _make_tag_stats(handle_id, "bitmask", solved_count=2, attempt_count=2, acceptance_rate=1.0)

    added: list = []
    session = MagicMock()
    session.execute = AsyncMock(return_value=MagicMock(scalars=MagicMock(return_value=MagicMock(all=MagicMock(return_value=[row])))))
    session.add_all = lambda items: added.extend(items)
    session.commit = AsyncMock()

    await _compute_weakness_signals(handle_id, session)

    assert len(added) == 1
    assert added[0].signal_type == WeaknessSignalType.UNDER_PRACTICED


@pytest.mark.asyncio
async def test_no_signal_for_healthy_tag():
    handle_id = uuid.uuid4()
    recent = datetime.now(UTC) - timedelta(days=3)
    row = _make_tag_stats(
        handle_id, "math", solved_count=10, attempt_count=12, acceptance_rate=0.83,
        last_activity_at=recent
    )

    added: list = []
    session = MagicMock()
    session.execute = AsyncMock(return_value=MagicMock(scalars=MagicMock(return_value=MagicMock(all=MagicMock(return_value=[row])))))
    session.add_all = lambda items: added.extend(items)
    session.commit = AsyncMock()

    await _compute_weakness_signals(handle_id, session)

    assert len(added) == 0


@pytest.mark.asyncio
async def test_neglected_requires_at_least_one_solved():
    handle_id = uuid.uuid4()
    stale_date = datetime.now(UTC) - timedelta(days=20)
    # solved_count=0 — neglected must NOT fire (under_practiced may fire instead)
    row = _make_tag_stats(handle_id, "dp", solved_count=0, last_activity_at=stale_date)

    added: list = []
    session = MagicMock()
    session.execute = AsyncMock(return_value=MagicMock(scalars=MagicMock(return_value=MagicMock(all=MagicMock(return_value=[row])))))
    session.add_all = lambda items: added.extend(items)
    session.commit = AsyncMock()

    await _compute_weakness_signals(handle_id, session)

    neglected = [s for s in added if s.signal_type == WeaknessSignalType.NEGLECTED]
    assert len(neglected) == 0
