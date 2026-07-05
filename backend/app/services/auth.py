import hashlib
from datetime import UTC, datetime

import httpx
from fastapi import HTTPException, status
from jose import JWTError, jwt
from sqlalchemy import delete, func, select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    hash_token,
    refresh_token_expires_at,
)
from app.models.classroom import Classroom, ClassroomLeaderboard, ClassroomMembership
from app.models.refresh_token import RefreshToken
from app.models.user import User

GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_TOKEN_INFO_URL = "https://oauth2.googleapis.com/tokeninfo"


async def exchange_google_code(code: str) -> dict:
    """Exchange authorization code for Google ID token."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            GOOGLE_TOKEN_URL,
            data={
                "code": code,
                "client_id": settings.GOOGLE_CLIENT_ID,
                "client_secret": settings.GOOGLE_CLIENT_SECRET,
                "redirect_uri": settings.GOOGLE_REDIRECT_URI,
                "grant_type": "authorization_code",
            },
        )
    if response.status_code != 200:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to exchange code with Google",
        )
    return response.json()


def decode_google_id_token(id_token: str) -> dict:
    """Decode Google ID token without signature verification.

    Safe because we received the token directly from Google's token endpoint
    over HTTPS — we don't need to re-verify the signature.
    """
    try:
        return jwt.decode(
            id_token,
            key="",
            options={"verify_signature": False, "verify_aud": False, "verify_at_hash": False},
        )
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid Google ID token: {e}",
        )


async def verify_google_id_token(id_token_str: str) -> dict:
    """Verify a Google ID token that arrived FROM A CLIENT (mobile app).

    Unlike `decode_google_id_token` (which trusts a token fetched server↔Google
    over HTTPS and skips signature checks), this token is supplied by the device
    and MUST be fully verified. `verify_oauth2_token` checks the signature against
    Google's public keys, the expiry, the issuer, AND that the audience equals our
    client id — all in one call. The audience check is why the app must request the
    token with `serverClientId = GOOGLE_CLIENT_ID`.

    The google-auth verifier is synchronous (it fetches/caches Google's certs), so
    run it off the event loop.
    """
    from anyio import to_thread
    from google.auth.transport import requests as google_requests
    from google.oauth2 import id_token as google_id_token

    def _verify() -> dict:
        return google_id_token.verify_oauth2_token(
            id_token_str,
            google_requests.Request(),
            settings.GOOGLE_CLIENT_ID,
        )

    try:
        payload = await to_thread.run_sync(_verify)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid Google ID token: {e}",
        )

    # Belt-and-suspenders: verify_oauth2_token already enforces this, but assert
    # the issuer explicitly so a future library change can't loosen it silently.
    if payload.get("iss") not in ("accounts.google.com", "https://accounts.google.com"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Google ID token issuer",
        )
    return payload


async def upsert_user(db: AsyncSession, google_payload: dict) -> User:
    """Insert or update user based on google_id."""
    stmt = (
        insert(User)
        .values(
            google_id=google_payload["sub"],
            email=google_payload["email"],
            name=google_payload.get("name", ""),
            avatar_url=google_payload.get("picture"),
            is_active=True,
        )
        .on_conflict_do_update(
            index_elements=["google_id"],
            set_={
                "email": google_payload["email"],
                "name": google_payload.get("name", ""),
                "avatar_url": google_payload.get("picture"),
            },
        )
        .returning(User.id)
    )
    result = await db.execute(stmt)
    user_id = result.scalar_one()
    await db.commit()
    # Re-select after commit to avoid identity map returning stale data
    fresh = await db.execute(
        select(User).where(User.id == user_id),
        execution_options={"populate_existing": True},
    )
    return fresh.scalar_one()


async def create_session(db: AsyncSession, user_id: str) -> tuple[str, str]:
    """Issue access JWT and persist refresh token. Returns (access_token, raw_refresh_token)."""
    access_token = create_access_token(user_id)
    raw_refresh = create_refresh_token()

    db.add(
        RefreshToken(
            user_id=user_id,
            token_hash=hash_token(raw_refresh),
            expires_at=refresh_token_expires_at(),
        )
    )
    await db.commit()
    return access_token, raw_refresh


async def rotate_refresh_token(
    db: AsyncSession, raw_refresh: str
) -> tuple[str, str, str]:
    """Validate refresh token, revoke it, issue new pair.

    Returns (new_access_token, new_raw_refresh, user_id).
    """
    token_hash = hash_token(raw_refresh)
    now = datetime.now(UTC)

    result = await db.execute(
        select(RefreshToken).where(
            RefreshToken.token_hash == token_hash,
            RefreshToken.revoked_at.is_(None),
            RefreshToken.expires_at > now,
        )
    )
    token_row = result.scalar_one_or_none()

    if token_row is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token invalid or expired",
        )

    # Revoke old token
    token_row.revoked_at = now
    await db.flush()

    user_id = str(token_row.user_id)
    new_access, new_refresh = await create_session(db, user_id)
    return new_access, new_refresh, user_id


async def revoke_token(db: AsyncSession, raw_refresh: str) -> None:
    """Revoke a single refresh token (logout)."""
    token_hash = hash_token(raw_refresh)
    await db.execute(
        update(RefreshToken)
        .where(RefreshToken.token_hash == token_hash, RefreshToken.revoked_at.is_(None))
        .values(revoked_at=datetime.now(UTC))
    )
    await db.commit()


async def revoke_all_tokens(db: AsyncSession, user_id: str) -> None:
    """Revoke all refresh tokens for a user (logout-all)."""
    await db.execute(
        update(RefreshToken)
        .where(
            RefreshToken.user_id == user_id,
            RefreshToken.revoked_at.is_(None),
        )
        .values(revoked_at=datetime.now(UTC))
    )
    await db.commit()


async def update_user_name(db: AsyncSession, user_id: str, name: str) -> User:
    """Update user's display name."""
    await db.execute(update(User).where(User.id == user_id).values(name=name))
    await db.commit()
    result = await db.execute(
        select(User).where(User.id == user_id),
        execution_options={"populate_existing": True},
    )
    return result.scalar_one()


async def soft_delete_user(db: AsyncSession, user_id: str) -> None:
    """Soft-delete account: anonymize PII, revoke all sessions."""
    active_classrooms = await db.scalar(
        select(func.count()).where(
            Classroom.owner_id == user_id,
            Classroom.is_active.is_(True),
        )
    )
    if active_classrooms:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Delete your classrooms before deleting your account.",
        )

    hashed = hashlib.sha256(user_id.encode()).hexdigest()
    await db.execute(
        update(User)
        .where(User.id == user_id)
        .values(
            is_active=False,
            email=f"deleted_{hashed[:16]}@deleted.invalid",
            name="Deleted User",
            avatar_url=None,
            google_id=f"deleted_{hashed}",
        )
    )
    await db.execute(
        update(RefreshToken)
        .where(
            RefreshToken.user_id == user_id,
            RefreshToken.revoked_at.is_(None),
        )
        .values(revoked_at=datetime.now(UTC))
    )
    # Remove student memberships and their cached leaderboard rows
    await db.execute(
        delete(ClassroomLeaderboard).where(ClassroomLeaderboard.user_id == user_id)
    )
    await db.execute(
        delete(ClassroomMembership).where(ClassroomMembership.user_id == user_id)
    )
    await db.commit()
