import asyncio
import secrets
import uuid
from datetime import UTC, datetime, timedelta

import httpx
from fastapi import HTTPException, status
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user_handle import HandlePlatform, HandleStatus, UserHandle

CF_USER_INFO_URL = "https://codeforces.com/api/user.info"
TOKEN_PREFIX = "PGS-"
TOKEN_EXPIRY_MINUTES = 60
MAX_VERIFY_ATTEMPTS = 10
LOCKOUT_HOURS = 0.25  # 15 minutes — soft cooldown, not a punishment

# A single "Verify" click polls Codeforces a few times before giving up, so that the
# common case (user just pasted the token and CF hasn't reflected it yet) succeeds
# without surfacing an error or burning an attempt. The whole click counts as at most
# one attempt regardless of how many inner reads we make.
#
# The total request time is bounded so it stays under the production gateway budget
# (Vercel rewrite → Render): worst case = ATTEMPTS * CF_TIMEOUT + (ATTEMPTS-1) * DELAY
# = 3*6 + 2*2.5 = 23s; nominal (fast CF reads) ≈ 5–6s.
CONFIRM_POLL_ATTEMPTS = 3
CONFIRM_POLL_DELAY_SECONDS = 2.5
CONFIRM_CF_TIMEOUT_SECONDS = 6.0


def generate_verification_token() -> str:
    return TOKEN_PREFIX + secrets.token_hex(3).upper()


async def fetch_cf_user(handle: str, timeout: float = 10.0) -> dict:
    async with httpx.AsyncClient(timeout=timeout) as client:
        resp = await client.get(CF_USER_INFO_URL, params={"handles": handle})
    data = resp.json()
    if resp.status_code != 200 or data.get("status") != "OK":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Codeforces handle '{handle}' not found",
        )
    return data["result"][0]


async def list_handles(db: AsyncSession, user_id: uuid.UUID) -> list[UserHandle]:
    result = await db.execute(
        select(UserHandle).where(
            UserHandle.user_id == user_id,
            UserHandle.is_active.is_(True),
        )
    )
    return list(result.scalars().all())


async def initiate_verification(
    db: AsyncSession,
    user_id: uuid.UUID,
    handle: str,
    platform: HandlePlatform,
) -> UserHandle:
    # Step 1: validate handle exists on CF
    await fetch_cf_user(handle)

    now = datetime.now(UTC)

    # Step 2: reject if another verified account already owns this handle
    result = await db.execute(
        select(UserHandle).where(
            UserHandle.handle == handle,
            UserHandle.platform == platform,
            UserHandle.is_verified.is_(True),
            UserHandle.is_active.is_(True),
            UserHandle.user_id != user_id,
        )
    )
    if result.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This handle is already claimed by another account",
        )

    # Step 3: supersede unverified pending handle belonging to another user
    await db.execute(
        update(UserHandle)
        .where(
            UserHandle.handle == handle,
            UserHandle.platform == platform,
            UserHandle.is_verified.is_(False),
            UserHandle.is_active.is_(True),
            UserHandle.user_id != user_id,
        )
        .values(is_active=False)
    )

    # Step 4: reject if current user already has a verified active handle for this platform
    result = await db.execute(
        select(UserHandle).where(
            UserHandle.user_id == user_id,
            UserHandle.platform == platform,
            UserHandle.is_verified.is_(True),
            UserHandle.is_active.is_(True),
        )
    )
    if result.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="You already have a verified handle for this platform. Unlink it first.",
        )

    token = generate_verification_token()
    expires_at = now + timedelta(minutes=TOKEN_EXPIRY_MINUTES)

    # Step 5: update in-place if current user has an unverified pending handle for this platform
    result = await db.execute(
        select(UserHandle).where(
            UserHandle.user_id == user_id,
            UserHandle.platform == platform,
            UserHandle.is_verified.is_(False),
            UserHandle.is_active.is_(True),
        )
    )
    existing = result.scalar_one_or_none()

    if existing is not None:
        # Block re-initiate while lockout is still active
        if existing.is_locked and existing.lockout_expires_at and existing.lockout_expires_at > now:
            raise HTTPException(
                status_code=status.HTTP_423_LOCKED,
                detail="Handle is locked due to too many failed attempts. Try again after the lockout expires.",
            )

        # Stable token: if the user re-initiates the same handle while the existing
        # token is still alive, return it untouched — same token, same expiry, same
        # attempt count. Regenerating here is the root cause of the "never verifies"
        # loop: the user pasted the old token into CF, and a fresh one would never
        # match. Resetting attempt_count would also turn re-initiate into a lockout
        # bypass, so leave it alone too.
        same_handle = existing.handle == handle
        token_alive = (
            existing.verification_token is not None
            and existing.verification_token_expires_at is not None
            and existing.verification_token_expires_at > now
        )
        if same_handle and token_alive:
            return existing

        # Handle changed or token is dead → issue a fresh one and reset the budget.
        existing.handle = handle
        existing.verification_token = token
        existing.verification_token_expires_at = expires_at
        existing.verification_attempt_count = 0
        existing.is_locked = False
        existing.lockout_expires_at = None
        await db.commit()
        await db.refresh(existing)
        return existing

    # Step 6: create new row
    row = UserHandle(
        user_id=user_id,
        platform=platform,
        handle=handle,
        status=HandleStatus.ACTIVE,
        verification_token=token,
        verification_token_expires_at=expires_at,
    )
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return row


async def confirm_verification(
    db: AsyncSession,
    user_id: uuid.UUID,
    handle_id: uuid.UUID,
) -> UserHandle:
    result = await db.execute(
        select(UserHandle).where(
            UserHandle.id == handle_id,
            UserHandle.is_active.is_(True),
        )
    )
    row = result.scalar_one_or_none()

    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Handle not found")
    if row.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your handle")

    now = datetime.now(UTC)

    # Check lockout before expiry — locked is a harder block
    if row.is_locked and row.lockout_expires_at and row.lockout_expires_at > now:
        raise HTTPException(
            status_code=status.HTTP_423_LOCKED,
            detail="Handle is locked due to too many failed attempts. Try again later.",
        )

    if row.verification_token_expires_at is None or row.verification_token_expires_at < now:
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail="Verification token has expired. Please re-initiate.",
        )

    # Poll CF for the organization field. Codeforces can take a little while to reflect
    # a profile change, so a single read right after the user pastes the token often
    # misses it. Retry a few times within this one request and succeed as soon as any
    # read matches — the user only had to click once.
    expected = row.verification_token
    matched = False
    for poll in range(CONFIRM_POLL_ATTEMPTS):
        cf_user = await fetch_cf_user(row.handle, timeout=CONFIRM_CF_TIMEOUT_SECONDS)
        cf_org = cf_user.get("organization", "").strip()
        if cf_org == expected:
            matched = True
            break
        if poll < CONFIRM_POLL_ATTEMPTS - 1:
            await asyncio.sleep(CONFIRM_POLL_DELAY_SECONDS)

    if matched:
        row.is_verified = True
        row.verified_at = now
        row.verification_token = None
        row.verification_token_expires_at = None
        row.verification_attempt_count = 0
        await db.commit()
        await db.refresh(row)
        return row

    # Token still not visible after the poll — count the whole click as ONE attempt.
    row.verification_attempt_count += 1
    if row.verification_attempt_count >= MAX_VERIFY_ATTEMPTS:
        row.is_locked = True
        row.lockout_expires_at = now + timedelta(hours=LOCKOUT_HOURS)

    await db.commit()

    attempts_remaining = max(0, MAX_VERIFY_ATTEMPTS - row.verification_attempt_count)
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail={
            "message": "Token not found in Codeforces profile Organization field",
            "attempts_remaining": attempts_remaining,
        },
    )


async def get_handle_for_user(
    db: AsyncSession,
    user_id: uuid.UUID,
    handle_id: uuid.UUID,
) -> UserHandle:
    result = await db.execute(
        select(UserHandle).where(
            UserHandle.id == handle_id,
            UserHandle.is_active.is_(True),
        )
    )
    row = result.scalar_one_or_none()
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Handle not found")
    if row.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your handle")
    return row


async def unlink_handle(
    db: AsyncSession,
    user_id: uuid.UUID,
    handle_id: uuid.UUID,
) -> None:
    result = await db.execute(
        select(UserHandle).where(
            UserHandle.id == handle_id,
            UserHandle.is_active.is_(True),
        )
    )
    row = result.scalar_one_or_none()

    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Handle not found")
    if row.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your handle")

    row.is_active = False
    await db.commit()
