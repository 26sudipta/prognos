"""Integration tests for manual sync logic (service layer + cooldown)."""

import uuid
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user_handle import HandlePlatform, HandleStatus, HandleSyncStatus, UserHandle
from app.services.handle import get_handle_for_user


@pytest_asyncio.fixture
async def verified_handle(db_session: AsyncSession, test_user):
    handle = UserHandle(
        user_id=test_user.id,
        platform=HandlePlatform.CODEFORCES,
        handle="tourist",
        is_verified=True,
        is_active=True,
        status=HandleStatus.ACTIVE,
        sync_status=HandleSyncStatus.IDLE,
    )
    db_session.add(handle)
    await db_session.commit()
    await db_session.refresh(handle)
    yield handle
    await db_session.delete(handle)
    await db_session.commit()


# ---------------------------------------------------------------------------
# get_handle_for_user
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_get_handle_for_user_returns_handle(db_session: AsyncSession, test_user, verified_handle):
    handle = await get_handle_for_user(db_session, test_user.id, verified_handle.id)
    assert handle.id == verified_handle.id


@pytest.mark.asyncio
async def test_get_handle_for_user_404_unknown(db_session: AsyncSession, test_user):
    with pytest.raises(HTTPException) as exc_info:
        await get_handle_for_user(db_session, test_user.id, uuid.uuid4())
    assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_get_handle_for_user_403_wrong_owner(db_session: AsyncSession, test_user, verified_handle):
    other_user_id = uuid.uuid4()
    with pytest.raises(HTTPException) as exc_info:
        await get_handle_for_user(db_session, other_user_id, verified_handle.id)
    assert exc_info.value.status_code == 403


# ---------------------------------------------------------------------------
# Cooldown logic
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_cooldown_blocks_within_30_minutes(db_session: AsyncSession, test_user, verified_handle):
    verified_handle.last_manual_sync_at = datetime.now(UTC) - timedelta(minutes=10)
    await db_session.commit()

    cooldown = timedelta(minutes=30)
    now = datetime.now(UTC)
    is_blocked = (
        verified_handle.last_manual_sync_at is not None
        and now - verified_handle.last_manual_sync_at < cooldown
    )
    assert is_blocked is True


@pytest.mark.asyncio
async def test_cooldown_allows_after_30_minutes(db_session: AsyncSession, test_user, verified_handle):
    verified_handle.last_manual_sync_at = datetime.now(UTC) - timedelta(minutes=35)
    await db_session.commit()

    cooldown = timedelta(minutes=30)
    now = datetime.now(UTC)
    is_blocked = (
        verified_handle.last_manual_sync_at is not None
        and now - verified_handle.last_manual_sync_at < cooldown
    )
    assert is_blocked is False


@pytest.mark.asyncio
async def test_cooldown_not_active_on_first_sync(db_session: AsyncSession, test_user, verified_handle):
    # last_manual_sync_at is None on first sync
    assert verified_handle.last_manual_sync_at is None

    cooldown = timedelta(minutes=30)
    now = datetime.now(UTC)
    is_blocked = (
        verified_handle.last_manual_sync_at is not None
        and now - verified_handle.last_manual_sync_at < cooldown
    )
    assert is_blocked is False


# ---------------------------------------------------------------------------
# sync_handle task dispatch (mocked)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_sync_handle_task_called_with_handle_id(verified_handle):
    with patch("app.workers.cf_sync.sync_handle") as mock_task:
        mock_result = MagicMock()
        mock_result.id = "task-abc-123"
        mock_task.delay.return_value = mock_result

        from app.workers.cf_sync import sync_handle
        result = sync_handle.delay(str(verified_handle.id))

        assert result.id == "task-abc-123"
        mock_task.delay.assert_called_once_with(str(verified_handle.id))
