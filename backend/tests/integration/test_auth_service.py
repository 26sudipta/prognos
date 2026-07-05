"""Integration tests for auth and user management service functions.

All tests hit a real DB (same async engine as the app). No mocking.
"""
import uuid
from datetime import UTC, datetime, timedelta

import pytest
import pytest_asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.refresh_token import RefreshToken
from app.models.user import User
from app.services.auth import (
    create_session,
    revoke_all_tokens,
    revoke_token,
    rotate_refresh_token,
    soft_delete_user,
    update_user_name,
    upsert_user,
)


# ---------------------------------------------------------------------------
# upsert_user
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_upsert_user_creates_new_user(db_session: AsyncSession):
    google_id = f"gid_{uuid.uuid4()}"
    payload = {
        "sub": google_id,
        "email": f"{uuid.uuid4()}@example.com",
        "name": "Alice Test",
        "picture": "https://example.com/avatar.jpg",
    }
    user = await upsert_user(db_session, payload)

    assert user.id is not None
    assert user.google_id == google_id
    assert user.email == payload["email"]
    assert user.name == "Alice Test"
    assert user.avatar_url == payload["picture"]
    assert user.is_active is True

    # Cleanup
    await db_session.delete(user)
    await db_session.commit()


@pytest.mark.asyncio
async def test_upsert_user_updates_existing_on_conflict(db_session: AsyncSession):
    google_id = f"gid_{uuid.uuid4()}"
    email = f"{uuid.uuid4()}@example.com"
    payload = {"sub": google_id, "email": email, "name": "Old Name", "picture": None}

    user = await upsert_user(db_session, payload)
    original_id = user.id

    # Second call — same google_id, different name/avatar
    updated_payload = {
        "sub": google_id,
        "email": email,
        "name": "New Name",
        "picture": "https://example.com/new.jpg",
    }
    user2 = await upsert_user(db_session, updated_payload)

    assert user2.id == original_id
    assert user2.name == "New Name"
    assert user2.avatar_url == "https://example.com/new.jpg"

    await db_session.delete(user2)
    await db_session.commit()


# ---------------------------------------------------------------------------
# create_session + rotate_refresh_token
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_create_session_issues_tokens(db_session: AsyncSession, test_user: User):
    access_token, raw_refresh = await create_session(db_session, str(test_user.id))

    assert isinstance(access_token, str) and len(access_token) > 20
    assert isinstance(raw_refresh, str) and len(raw_refresh) > 20

    # Verify token hash persisted in DB
    from app.core.security import hash_token
    result = await db_session.execute(
        select(RefreshToken).where(RefreshToken.token_hash == hash_token(raw_refresh))
    )
    row = result.scalar_one_or_none()
    assert row is not None
    assert row.user_id == test_user.id
    assert row.revoked_at is None
    assert row.expires_at > datetime.now(UTC)


@pytest.mark.asyncio
async def test_rotate_refresh_token_issues_new_pair_and_revokes_old(
    db_session: AsyncSession, test_user: User
):
    _, old_refresh = await create_session(db_session, str(test_user.id))
    new_access, new_refresh, user_id = await rotate_refresh_token(db_session, old_refresh)

    assert new_access != old_refresh
    assert new_refresh != old_refresh
    assert user_id == str(test_user.id)

    # Old token must be revoked
    from app.core.security import hash_token
    result = await db_session.execute(
        select(RefreshToken).where(RefreshToken.token_hash == hash_token(old_refresh))
    )
    old_row = result.scalar_one()
    assert old_row.revoked_at is not None

    # New token must be valid
    result2 = await db_session.execute(
        select(RefreshToken).where(RefreshToken.token_hash == hash_token(new_refresh))
    )
    new_row = result2.scalar_one_or_none()
    assert new_row is not None
    assert new_row.revoked_at is None


@pytest.mark.asyncio
async def test_rotate_refresh_token_rejects_invalid_token(db_session: AsyncSession):
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as exc_info:
        await rotate_refresh_token(db_session, "not-a-real-token")
    assert exc_info.value.status_code == 401


@pytest.mark.asyncio
async def test_rotate_refresh_token_rejects_already_revoked(
    db_session: AsyncSession, test_user: User
):
    from fastapi import HTTPException
    _, raw_refresh = await create_session(db_session, str(test_user.id))
    await revoke_token(db_session, raw_refresh)

    with pytest.raises(HTTPException) as exc_info:
        await rotate_refresh_token(db_session, raw_refresh)
    assert exc_info.value.status_code == 401


# ---------------------------------------------------------------------------
# revoke_token / revoke_all_tokens
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_revoke_token_marks_single_token_revoked(
    db_session: AsyncSession, test_user: User
):
    from app.core.security import hash_token
    _, raw_refresh = await create_session(db_session, str(test_user.id))
    await revoke_token(db_session, raw_refresh)

    result = await db_session.execute(
        select(RefreshToken).where(RefreshToken.token_hash == hash_token(raw_refresh))
    )
    row = result.scalar_one()
    assert row.revoked_at is not None


@pytest.mark.asyncio
async def test_revoke_all_tokens_revokes_every_session(
    db_session: AsyncSession, test_user: User
):
    # Issue 3 tokens
    for _ in range(3):
        await create_session(db_session, str(test_user.id))

    await revoke_all_tokens(db_session, str(test_user.id))

    result = await db_session.execute(
        select(RefreshToken).where(
            RefreshToken.user_id == test_user.id,
            RefreshToken.revoked_at.is_(None),
        )
    )
    assert result.scalars().all() == []


# ---------------------------------------------------------------------------
# update_user_name
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_update_user_name_persists_change(db_session: AsyncSession, test_user: User):
    updated = await update_user_name(db_session, str(test_user.id), "Renamed User")
    assert updated.name == "Renamed User"

    # Verify in DB
    result = await db_session.execute(select(User).where(User.id == test_user.id))
    fresh = result.scalar_one()
    assert fresh.name == "Renamed User"


# ---------------------------------------------------------------------------
# soft_delete_user
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_soft_delete_anonymizes_pii_and_deactivates(
    db_session: AsyncSession, test_user: User
):
    original_email = test_user.email
    original_google_id = test_user.google_id
    _, raw_refresh = await create_session(db_session, str(test_user.id))

    await soft_delete_user(db_session, str(test_user.id))
    # refresh() always hits the DB, bypassing the identity map cache
    await db_session.refresh(test_user)

    assert test_user.is_active is False
    assert test_user.email != original_email
    assert test_user.email.endswith("@deleted.invalid")
    assert test_user.google_id != original_google_id
    assert test_user.google_id.startswith("deleted_")
    assert test_user.name == "Deleted User"
    assert test_user.avatar_url is None


@pytest.mark.asyncio
async def test_soft_delete_revokes_all_sessions(
    db_session: AsyncSession, test_user: User
):
    _, raw1 = await create_session(db_session, str(test_user.id))
    _, raw2 = await create_session(db_session, str(test_user.id))

    await soft_delete_user(db_session, str(test_user.id))

    result = await db_session.execute(
        select(RefreshToken).where(
            RefreshToken.user_id == test_user.id,
            RefreshToken.revoked_at.is_(None),
        )
    )
    assert result.scalars().all() == []


# ---------------------------------------------------------------------------
# Mobile auth (M1): verify_google_id_token + /auth/google/mobile + refresh/mobile
# ---------------------------------------------------------------------------

import app.services.auth as auth_service  # noqa: E402
from app.api.v1.routes.auth import google_mobile, refresh_mobile  # noqa: E402
from app.schemas.auth import GoogleMobileRequest, MobileRefreshRequest  # noqa: E402


def _patch_google_verify(monkeypatch, payload=None, raises=False):
    """Patch the google-auth verification boundary (not our wrapper)."""
    def fake(token, request, audience):
        if raises:
            raise ValueError("Token has wrong audience")
        return payload
    monkeypatch.setattr("google.oauth2.id_token.verify_oauth2_token", fake)


@pytest.mark.asyncio
async def test_verify_google_id_token_valid(monkeypatch):
    payload = {"sub": "g1", "email": "a@b.com", "iss": "accounts.google.com"}
    _patch_google_verify(monkeypatch, payload=payload)
    result = await auth_service.verify_google_id_token("any-token")
    assert result["sub"] == "g1"


@pytest.mark.asyncio
async def test_verify_google_id_token_invalid_signature_or_audience_401(monkeypatch):
    from fastapi import HTTPException
    _patch_google_verify(monkeypatch, raises=True)
    with pytest.raises(HTTPException) as exc:
        await auth_service.verify_google_id_token("forged")
    assert exc.value.status_code == 401


@pytest.mark.asyncio
async def test_verify_google_id_token_bad_issuer_401(monkeypatch):
    from fastapi import HTTPException
    _patch_google_verify(monkeypatch, payload={"sub": "g", "email": "e", "iss": "evil.com"})
    with pytest.raises(HTTPException) as exc:
        await auth_service.verify_google_id_token("x")
    assert exc.value.status_code == 401


@pytest.mark.asyncio
async def test_google_mobile_endpoint_issues_pair_via_verifying_path(
    db_session: AsyncSession, monkeypatch
):
    # A bogus id_token that would fail real decoding — only the *verifying* path,
    # patched here, lets it through. Proves the endpoint uses verify, not decode.
    gid = f"gid_{uuid.uuid4()}"
    payload = {
        "sub": gid,
        "email": f"{uuid.uuid4()}@example.com",
        "name": "Mobile User",
        "picture": None,
        "iss": "accounts.google.com",
    }
    _patch_google_verify(monkeypatch, payload=payload)

    resp = await google_mobile(GoogleMobileRequest(id_token="opaque"), db_session)

    assert resp.access_token and resp.refresh_token
    assert resp.expires_in > 0
    from app.core.security import hash_token
    row = (
        await db_session.execute(
            select(RefreshToken).where(RefreshToken.token_hash == hash_token(resp.refresh_token))
        )
    ).scalar_one_or_none()
    assert row is not None and row.revoked_at is None

    # cleanup the created user
    user = (await db_session.execute(select(User).where(User.google_id == gid))).scalar_one()
    await db_session.delete(user)
    await db_session.commit()


@pytest.mark.asyncio
async def test_refresh_mobile_rotates_and_returns_pair(db_session: AsyncSession, test_user: User):
    _, raw = await create_session(db_session, str(test_user.id))
    resp = await refresh_mobile(MobileRefreshRequest(refresh_token=raw), db_session)

    assert resp.access_token and resp.refresh_token != raw and resp.expires_in > 0
    from app.core.security import hash_token
    old = (
        await db_session.execute(
            select(RefreshToken).where(RefreshToken.token_hash == hash_token(raw))
        )
    ).scalar_one()
    assert old.revoked_at is not None  # rotation revoked the old token
