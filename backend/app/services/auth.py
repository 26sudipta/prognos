import hashlib
import logging
from datetime import UTC, datetime, timedelta

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

logger = logging.getLogger(__name__)

GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_TOKEN_INFO_URL = "https://oauth2.googleapis.com/tokeninfo"

# A refresh token that was just rotated stays usable for this long: two tabs sharing
# the httpOnly cookie can both send the same token in-flight, and the one that arrives
# just after the winner committed should get a fresh session, not a 401 → /login bounce.
# A rotated token replayed *after* this window is treated as stale/stolen and rejected.
ROTATION_GRACE = timedelta(seconds=30)


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


async def _issue_child(db: AsyncSession, user_id: str) -> tuple[str, str, str]:
    """Mint an access token + a fresh (unrevoked) refresh-token row.

    Flushes but does not commit — the caller commits, so the whole rotation lands in
    one transaction. Returns (access_token, raw_refresh, child_id).
    """
    access_token = create_access_token(user_id)
    raw_refresh = create_refresh_token()
    child = RefreshToken(
        user_id=user_id,
        token_hash=hash_token(raw_refresh),
        expires_at=refresh_token_expires_at(),
    )
    db.add(child)
    await db.flush()  # populate child.id for the rotation-chain link
    return access_token, raw_refresh, str(child.id)


async def rotate_refresh_token(
    db: AsyncSession, raw_refresh: str
) -> tuple[str, str, str]:
    """Validate a refresh token and issue a new pair, tolerating concurrent rotation.

    Returns (new_access_token, new_raw_refresh, user_id).

    Multi-tab safety: two tabs share one httpOnly cookie and can send the same token
    in-flight. Truly-simultaneous calls both read `revoked_at IS NULL` (neither's
    revoke is committed yet) and both rotate — each gets its own valid child. A call
    that arrives just after the winner committed sees the token already rotated; within
    ROTATION_GRACE that's a benign sibling refresh, so it's served a fresh pair instead
    of a 401. A rotated token replayed after the grace window, or a token revoked by
    logout (rotated_at is NULL), is rejected.
    """
    token_hash = hash_token(raw_refresh)
    now = datetime.now(UTC)

    result = await db.execute(
        select(RefreshToken).where(RefreshToken.token_hash == token_hash)
    )
    token_row = result.scalar_one_or_none()

    # Unknown token, or expired outright.
    if token_row is None or token_row.expires_at <= now:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token invalid or expired",
        )

    user_id = str(token_row.user_id)

    # Live token → normal rotation: revoke it, mint its child, link the chain.
    if token_row.revoked_at is None:
        new_access, new_refresh, child_id = await _issue_child(db, user_id)
        token_row.revoked_at = now
        token_row.rotated_at = now
        token_row.replaced_by_id = child_id
        await db.commit()
        return new_access, new_refresh, user_id

    # Already revoked. If it was rotated (not logged out) within the grace window AND the
    # child it rotated into is still live, this is a concurrent sibling refresh — hand it a
    # fresh pair rather than bounce the tab. The child-liveness check is what keeps
    # logout-all honest: `revoke_all_tokens` skips the already-revoked parent but revokes
    # the live child, so a replay inside the window after "log out everywhere" is denied
    # here instead of minting a fresh session. A normal multi-tab race leaves the child
    # alive, so it still passes.
    if token_row.rotated_at is not None and now - token_row.rotated_at <= ROTATION_GRACE:
        child = (
            await db.get(RefreshToken, token_row.replaced_by_id)
            if token_row.replaced_by_id is not None
            else None
        )
        if child is not None and child.revoked_at is None:
            new_access, new_refresh, _ = await _issue_child(db, user_id)
            await db.commit()
            return new_access, new_refresh, user_id

    # Logout-revoked, or a rotated token replayed after the grace window → reject.
    logger.warning(
        "refresh-token reuse rejected (user=%s rotated_at=%s)",
        token_row.user_id,
        token_row.rotated_at,
    )
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Refresh token invalid or expired",
    )


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
