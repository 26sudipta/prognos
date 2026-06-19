from datetime import UTC, datetime

import httpx
from fastapi import HTTPException, status
from jose import JWTError, jwt
from sqlalchemy import delete, select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    hash_token,
    refresh_token_expires_at,
)
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
            options={"verify_signature": False, "verify_aud": False},
        )
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid Google ID token: {e}",
        )


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
        .returning(User)
    )
    result = await db.execute(stmt)
    await db.commit()
    return result.scalar_one()


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
