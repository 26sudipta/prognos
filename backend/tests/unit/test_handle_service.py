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
    MAX_VERIFY_ATTEMPTS,
    TOKEN_PREFIX,
    confirm_verification,
    fetch_cf_user,
    generate_verification_token,
    initiate_verification,
)


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
        return_value=Response(200, json={"status": "OK", "result": [{"handle": "tourist", "lastName": ""}]})
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
        return_value=Response(200, json={"status": "OK", "result": [{"handle": "tourist", "lastName": ""}]})
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
async def test_confirm_increments_attempt_count_on_mismatch():
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

    respx.get("https://codeforces.com/api/user.info").mock(
        return_value=Response(200, json={"status": "OK", "result": [{"handle": "tourist", "lastName": "WRONG"}]})
    )

    db = AsyncMock()
    result = MagicMock()
    result.scalar_one_or_none.return_value = row
    db.execute = AsyncMock(return_value=result)

    with pytest.raises(HTTPException) as exc:
        await confirm_verification(db, user_id, handle_id)

    assert exc.value.status_code == 400
    assert row.verification_attempt_count == 2
    assert exc.value.detail["attempts_remaining"] == MAX_VERIFY_ATTEMPTS - 2


# ---------------------------------------------------------------------------
# confirm_verification — 5th failure triggers lockout
# ---------------------------------------------------------------------------

@respx.mock
@pytest.mark.asyncio
async def test_confirm_locks_on_5th_failure():
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
    row.verification_attempt_count = 4  # this call will be the 5th

    respx.get("https://codeforces.com/api/user.info").mock(
        return_value=Response(200, json={"status": "OK", "result": [{"handle": "tourist", "lastName": "WRONG"}]})
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
