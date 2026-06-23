"""Integration tests for handle verification — real DB, CF API mocked via respx."""
import uuid
from datetime import UTC, datetime, timedelta

import pytest
import pytest_asyncio
import respx
from httpx import Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.models.user_handle import HandlePlatform, HandleStatus, UserHandle
from app.services.handle import generate_verification_token

CF_OK = {"status": "OK", "result": [{"handle": "tourist", "organization": ""}]}
CF_WITH_TOKEN = lambda token: {"status": "OK", "result": [{"handle": "tourist", "organization": token}]}  # noqa: E731


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def _create_handle(
    db: AsyncSession,
    user_id: uuid.UUID,
    handle: str = "tourist",
    *,
    is_verified: bool = False,
    is_active: bool = True,
    token: str | None = None,
    expires_at: datetime | None = None,
) -> UserHandle:
    row = UserHandle(
        user_id=user_id,
        platform=HandlePlatform.CODEFORCES,
        handle=handle,
        status=HandleStatus.ACTIVE,
        is_verified=is_verified,
        is_active=is_active,
        verification_token=token,
        verification_token_expires_at=expires_at,
    )
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return row


# ---------------------------------------------------------------------------
# initiate_verification
# ---------------------------------------------------------------------------

@respx.mock
@pytest.mark.asyncio
async def test_initiate_creates_row_in_db(db_session: AsyncSession, test_user: User):
    respx.get("https://codeforces.com/api/user.info").mock(
        return_value=Response(200, json=CF_OK)
    )

    from app.services.handle import initiate_verification
    row = await initiate_verification(db_session, test_user.id, "tourist", HandlePlatform.CODEFORCES)

    assert row.id is not None
    assert row.handle == "tourist"
    assert row.platform == HandlePlatform.CODEFORCES
    assert row.verification_token is not None
    assert row.verification_token.startswith("PGS-")
    assert row.verification_token_expires_at > datetime.now(UTC)
    assert row.is_verified is False


@respx.mock
@pytest.mark.asyncio
async def test_initiate_supersedes_unverified_duplicate_from_other_user(
    db_session: AsyncSession, test_user: User
):
    # Another user has an unverified pending row for "tourist"
    other_user = User(
        email=f"other_{uuid.uuid4()}@test.com",
        google_id=f"gid_{uuid.uuid4()}",
        name="Other User",
    )
    db_session.add(other_user)
    await db_session.commit()
    await db_session.refresh(other_user)

    other_row = await _create_handle(db_session, other_user.id, "tourist", is_verified=False)

    respx.get("https://codeforces.com/api/user.info").mock(
        return_value=Response(200, json=CF_OK)
    )

    from app.services.handle import initiate_verification
    await initiate_verification(db_session, test_user.id, "tourist", HandlePlatform.CODEFORCES)

    # Other user's row should now be soft-deleted
    await db_session.refresh(other_row)
    assert other_row.is_active is False

    # Cleanup
    await db_session.delete(other_user)
    await db_session.commit()


@respx.mock
@pytest.mark.asyncio
async def test_initiate_updates_own_pending_row_not_duplicate(
    db_session: AsyncSession, test_user: User
):
    token_before = "PGS-AABBCC"
    existing = await _create_handle(
        db_session,
        test_user.id,
        "tourist",
        token=token_before,
        expires_at=datetime.now(UTC) + timedelta(minutes=5),
    )

    respx.get("https://codeforces.com/api/user.info").mock(
        return_value=Response(200, json=CF_OK)
    )

    from app.services.handle import initiate_verification
    updated = await initiate_verification(db_session, test_user.id, "tourist", HandlePlatform.CODEFORCES)

    # Same row, new token
    assert updated.id == existing.id
    assert updated.verification_token != token_before
    assert updated.verification_attempt_count == 0

    # No second active row was created
    result = await db_session.execute(
        select(UserHandle).where(
            UserHandle.user_id == test_user.id,
            UserHandle.is_active.is_(True),
        )
    )
    assert len(result.scalars().all()) == 1


# ---------------------------------------------------------------------------
# confirm_verification
# ---------------------------------------------------------------------------

@respx.mock
@pytest.mark.asyncio
async def test_confirm_happy_path(db_session: AsyncSession, test_user: User):
    token = generate_verification_token()
    row = await _create_handle(
        db_session,
        test_user.id,
        token=token,
        expires_at=datetime.now(UTC) + timedelta(minutes=25),
    )

    respx.get("https://codeforces.com/api/user.info").mock(
        return_value=Response(200, json=CF_WITH_TOKEN(token))
    )

    from app.services.handle import confirm_verification
    verified = await confirm_verification(db_session, test_user.id, row.id)

    assert verified.is_verified is True
    assert verified.verified_at is not None
    assert verified.verification_token is None
    assert verified.verification_token_expires_at is None


# ---------------------------------------------------------------------------
# list_handles / unlink
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_get_handles_returns_active_only(db_session: AsyncSession, test_user: User):
    active = await _create_handle(db_session, test_user.id, "tourist", is_verified=True, is_active=True)
    await _create_handle(db_session, test_user.id, "tourist2", is_active=False)

    from app.services.handle import list_handles
    handles = await list_handles(db_session, test_user.id)

    ids = [h.id for h in handles]
    assert active.id in ids
    assert all(h.is_active for h in handles)


@pytest.mark.asyncio
async def test_unlink_soft_deletes_row(db_session: AsyncSession, test_user: User):
    row = await _create_handle(db_session, test_user.id, "tourist", is_verified=True)

    from app.services.handle import unlink_handle
    await unlink_handle(db_session, test_user.id, row.id)

    await db_session.refresh(row)
    assert row.is_active is False

    # Row still exists in DB (not hard-deleted)
    result = await db_session.execute(select(UserHandle).where(UserHandle.id == row.id))
    assert result.scalar_one_or_none() is not None
