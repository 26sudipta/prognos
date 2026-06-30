"""Unit tests for handle service — no DB, CF API mocked via respx."""
import re
import uuid
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import respx
from fastapi import HTTPException
from httpx import Response

from app.models.user_handle import HandlePlatform, HandleStatus, HandleSyncStatus, UserHandle
from app.services.handle import (
    CONFIRM_POLL_ATTEMPTS,
    MAX_VERIFY_ATTEMPTS,
    TOKEN_PREFIX,
    confirm_verification,
    fetch_cf_user,
    generate_verification_token,
    initiate_verification,
)


# ---------------------------------------------------------------------------
# CF API param remap (the submission-pagination bug)
# ---------------------------------------------------------------------------

@respx.mock
@pytest.mark.asyncio
async def test_cf_get_remaps_from_underscore_to_from():
    """The CF API expects `from`; callers pass `from_` (Python keyword). If we send the
    literal `from_`, CF ignores it and pagination silently refetches page 1."""
    import httpx

    from app.workers.cf_sync import _cf_get

    route = respx.get("https://codeforces.com/api/user.status").mock(
        return_value=Response(200, json={"status": "OK", "result": []})
    )
    async with httpx.AsyncClient() as client:
        await _cf_get(client, "user.status", handle="tourist", from_=501, count=500)

    url = str(route.calls.last.request.url)
    assert "from=501" in url
    assert "from_=" not in url


@respx.mock
@pytest.mark.asyncio
@patch("app.workers.cf_sync.asyncio.sleep", new_callable=AsyncMock)
async def test_cf_get_retries_on_200_failed_limit(mock_sleep):
    """CF rate-limits with HTTP 200 + status=FAILED + 'limit exceeded' — must retry, not abort."""
    import httpx

    from app.workers.cf_sync import _cf_get

    respx.get("https://codeforces.com/api/user.status").mock(
        side_effect=[
            Response(200, json={"status": "FAILED", "comment": "Call limit exceeded"}),
            Response(200, json={"status": "OK", "result": [{"id": 1}]}),
        ]
    )
    async with httpx.AsyncClient() as client:
        data = await _cf_get(client, "user.status", handle="tourist")
    assert data["status"] == "OK"


# ---------------------------------------------------------------------------
# Token format
# ---------------------------------------------------------------------------

def test_token_format():
    token = generate_verification_token()
    assert re.match(r"^PGS-[0-9A-F]{6}$", token), f"Unexpected token format: {token}"


def test_token_prefix():
    token = generate_verification_token()
    assert token.startswith(TOKEN_PREFIX)


# ---------------------------------------------------------------------------
# fetch_cf_user
# ---------------------------------------------------------------------------

@respx.mock
@pytest.mark.asyncio
async def test_fetch_cf_user_success():
    respx.get("https://codeforces.com/api/user.info").mock(
        return_value=Response(200, json={"status": "OK", "result": [{"handle": "tourist", "organization": ""}]})
    )
    user = await fetch_cf_user("tourist")
    assert user["handle"] == "tourist"


@respx.mock
@pytest.mark.asyncio
async def test_fetch_cf_user_not_found():
    respx.get("https://codeforces.com/api/user.info").mock(
        return_value=Response(400, json={"status": "FAILED", "comment": "handles: User with handle tourist not found"})
    )
    with pytest.raises(HTTPException) as exc:
        await fetch_cf_user("nonexistent_handle_xyz")
    assert exc.value.status_code == 404


# ---------------------------------------------------------------------------
# initiate_verification — 409 when handle already claimed
# ---------------------------------------------------------------------------

@respx.mock
@pytest.mark.asyncio
async def test_initiate_409_when_handle_verified_by_other_user():
    other_user_id = uuid.uuid4()
    current_user_id = uuid.uuid4()

    # Mock CF API — handle exists
    respx.get("https://codeforces.com/api/user.info").mock(
        return_value=Response(200, json={"status": "OK", "result": [{"handle": "tourist", "organization": ""}]})
    )

    # DB returns a verified row owned by another user
    claimed_row = MagicMock(spec=UserHandle)
    claimed_row.user_id = other_user_id

    db = AsyncMock()
    # First select (verified by other) returns the claimed row
    first_result = MagicMock()
    first_result.scalar_one_or_none.return_value = claimed_row
    db.execute = AsyncMock(return_value=first_result)

    with pytest.raises(HTTPException) as exc:
        await initiate_verification(db, current_user_id, "tourist", HandlePlatform.CODEFORCES)

    assert exc.value.status_code == 409


# ---------------------------------------------------------------------------
# confirm_verification — expired token
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_confirm_410_on_expired_token():
    user_id = uuid.uuid4()
    handle_id = uuid.uuid4()

    expired_row = MagicMock(spec=UserHandle)
    expired_row.id = handle_id
    expired_row.user_id = user_id
    expired_row.is_locked = False
    expired_row.lockout_expires_at = None
    expired_row.verification_token_expires_at = datetime.now(UTC) - timedelta(hours=1)

    db = AsyncMock()
    result = MagicMock()
    result.scalar_one_or_none.return_value = expired_row
    db.execute = AsyncMock(return_value=result)

    with pytest.raises(HTTPException) as exc:
        await confirm_verification(db, user_id, handle_id)

    assert exc.value.status_code == 410


# ---------------------------------------------------------------------------
# confirm_verification — locked handle
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_confirm_423_on_locked_handle():
    user_id = uuid.uuid4()
    handle_id = uuid.uuid4()

    locked_row = MagicMock(spec=UserHandle)
    locked_row.id = handle_id
    locked_row.user_id = user_id
    locked_row.is_locked = True
    locked_row.lockout_expires_at = datetime.now(UTC) + timedelta(hours=1)

    db = AsyncMock()
    result = MagicMock()
    result.scalar_one_or_none.return_value = locked_row
    db.execute = AsyncMock(return_value=result)

    with pytest.raises(HTTPException) as exc:
        await confirm_verification(db, user_id, handle_id)

    assert exc.value.status_code == 423


# ---------------------------------------------------------------------------
# confirm_verification — bad token increments attempt count
# ---------------------------------------------------------------------------

@respx.mock
@pytest.mark.asyncio
@patch("app.services.handle.asyncio.sleep", new_callable=AsyncMock)
async def test_confirm_increments_attempt_count_once_on_mismatch(mock_sleep):
    """A whole Verify click polls CF a few times but counts as exactly ONE attempt."""
    user_id = uuid.uuid4()
    handle_id = uuid.uuid4()

    row = MagicMock(spec=UserHandle)
    row.id = handle_id
    row.user_id = user_id
    row.handle = "tourist"
    row.is_locked = False
    row.lockout_expires_at = None
    row.verification_token = "PGS-AABBCC"
    row.verification_token_expires_at = datetime.now(UTC) + timedelta(minutes=20)
    row.verification_attempt_count = 1

    route = respx.get("https://codeforces.com/api/user.info").mock(
        return_value=Response(200, json={"status": "OK", "result": [{"handle": "tourist", "organization": "WRONG"}]})
    )

    db = AsyncMock()
    result = MagicMock()
    result.scalar_one_or_none.return_value = row
    db.execute = AsyncMock(return_value=result)

    with pytest.raises(HTTPException) as exc:
        await confirm_verification(db, user_id, handle_id)

    assert exc.value.status_code == 400
    # Polled multiple times, but the counter only moved by 1.
    assert route.call_count == CONFIRM_POLL_ATTEMPTS
    assert row.verification_attempt_count == 2
    assert exc.value.detail["attempts_remaining"] == MAX_VERIFY_ATTEMPTS - 2


@respx.mock
@pytest.mark.asyncio
@patch("app.services.handle.asyncio.sleep", new_callable=AsyncMock)
async def test_confirm_succeeds_when_org_appears_mid_poll(mock_sleep):
    """If CF reflects the token on a later poll, the same click verifies."""
    user_id = uuid.uuid4()
    handle_id = uuid.uuid4()

    row = MagicMock(spec=UserHandle)
    row.id = handle_id
    row.user_id = user_id
    row.handle = "tourist"
    row.is_locked = False
    row.lockout_expires_at = None
    row.verification_token = "PGS-AABBCC"
    row.verification_token_expires_at = datetime.now(UTC) + timedelta(minutes=20)
    row.verification_attempt_count = 0

    # First read still stale, second read shows the token.
    respx.get("https://codeforces.com/api/user.info").mock(
        side_effect=[
            Response(200, json={"status": "OK", "result": [{"handle": "tourist", "organization": ""}]}),
            Response(200, json={"status": "OK", "result": [{"handle": "tourist", "organization": "PGS-AABBCC"}]}),
        ]
    )

    db = AsyncMock()
    result = MagicMock()
    result.scalar_one_or_none.return_value = row
    db.execute = AsyncMock(return_value=result)

    out = await confirm_verification(db, user_id, handle_id)

    assert out.is_verified is True
    assert out.verification_token is None


# ---------------------------------------------------------------------------
# confirm_verification — lockout triggers at MAX_VERIFY_ATTEMPTS
# ---------------------------------------------------------------------------

@respx.mock
@pytest.mark.asyncio
@patch("app.services.handle.asyncio.sleep", new_callable=AsyncMock)
async def test_confirm_locks_on_max_failure(mock_sleep):
    user_id = uuid.uuid4()
    handle_id = uuid.uuid4()

    row = MagicMock(spec=UserHandle)
    row.id = handle_id
    row.user_id = user_id
    row.handle = "tourist"
    row.is_locked = False
    row.lockout_expires_at = None
    row.verification_token = "PGS-AABBCC"
    row.verification_token_expires_at = datetime.now(UTC) + timedelta(minutes=20)
    row.verification_attempt_count = MAX_VERIFY_ATTEMPTS - 1  # this call hits the limit

    respx.get("https://codeforces.com/api/user.info").mock(
        return_value=Response(200, json={"status": "OK", "result": [{"handle": "tourist", "organization": "WRONG"}]})
    )

    db = AsyncMock()
    result = MagicMock()
    result.scalar_one_or_none.return_value = row
    db.execute = AsyncMock(return_value=result)

    with pytest.raises(HTTPException) as exc:
        await confirm_verification(db, user_id, handle_id)

    assert exc.value.status_code == 400
    assert row.is_locked is True
    assert row.lockout_expires_at is not None
    assert exc.value.detail["attempts_remaining"] == 0


# ---------------------------------------------------------------------------
# initiate_verification — stable token (the core "never verifies" fix)
# ---------------------------------------------------------------------------

def _initiate_db_with_pending(existing_row):
    """AsyncMock DB whose selects yield: verified-by-other=None, supersede(noop),
    current-user-verified=None, current-user-pending=existing_row."""
    none_result = MagicMock()
    none_result.scalar_one_or_none.return_value = None
    pending_result = MagicMock()
    pending_result.scalar_one_or_none.return_value = existing_row
    noop_result = MagicMock()

    db = AsyncMock()
    db.execute = AsyncMock(side_effect=[none_result, noop_result, none_result, pending_result])
    return db


@respx.mock
@pytest.mark.asyncio
async def test_initiate_keeps_token_for_same_handle_while_alive():
    user_id = uuid.uuid4()

    respx.get("https://codeforces.com/api/user.info").mock(
        return_value=Response(200, json={"status": "OK", "result": [{"handle": "tourist", "organization": ""}]})
    )

    existing = MagicMock(spec=UserHandle)
    existing.user_id = user_id
    existing.handle = "tourist"
    existing.verification_token = "PGS-OLD123"
    existing.verification_token_expires_at = datetime.now(UTC) + timedelta(minutes=30)
    existing.verification_attempt_count = 3
    existing.is_locked = False
    existing.lockout_expires_at = None

    db = _initiate_db_with_pending(existing)

    out = await initiate_verification(db, user_id, "tourist", HandlePlatform.CODEFORCES)

    # Same token, same expiry, same attempt budget — nothing regenerated.
    assert out.verification_token == "PGS-OLD123"
    assert out.verification_attempt_count == 3
    db.commit.assert_not_awaited()


@respx.mock
@pytest.mark.asyncio
async def test_initiate_regenerates_token_when_handle_changes():
    user_id = uuid.uuid4()

    respx.get("https://codeforces.com/api/user.info").mock(
        return_value=Response(200, json={"status": "OK", "result": [{"handle": "newhandle", "organization": ""}]})
    )

    existing = MagicMock(spec=UserHandle)
    existing.user_id = user_id
    existing.handle = "oldhandle"
    existing.verification_token = "PGS-OLD123"
    existing.verification_token_expires_at = datetime.now(UTC) + timedelta(minutes=30)
    existing.verification_attempt_count = 3
    existing.is_locked = False
    existing.lockout_expires_at = None

    db = _initiate_db_with_pending(existing)

    out = await initiate_verification(db, user_id, "newhandle", HandlePlatform.CODEFORCES)

    # Different handle → fresh token, reset budget.
    assert out.handle == "newhandle"
    assert out.verification_token != "PGS-OLD123"
    assert out.verification_attempt_count == 0
    db.commit.assert_awaited()
