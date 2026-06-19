from fastapi import APIRouter, Cookie, Depends, Response
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.schemas.auth import TokenResponse
from app.services.auth import (
    decode_google_id_token,
    exchange_google_code,
    revoke_all_tokens,
    revoke_token,
    rotate_refresh_token,
    upsert_user,
    create_session,
)
from app.api.v1.deps import get_current_user
from app.models.user import User

router = APIRouter(prefix="/auth", tags=["auth"])

GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
REFRESH_COOKIE = "refresh_token"
COOKIE_MAX_AGE = 7 * 24 * 60 * 60  # 7 days in seconds


def _set_refresh_cookie(response: Response, raw_refresh: str) -> None:
    response.set_cookie(
        key=REFRESH_COOKIE,
        value=raw_refresh,
        httponly=True,
        secure=settings.is_production,
        samesite="strict",
        max_age=COOKIE_MAX_AGE,
        path="/api/v1/auth",
    )


def _clear_refresh_cookie(response: Response) -> None:
    response.delete_cookie(key=REFRESH_COOKIE, path="/api/v1/auth")


@router.get("/google")
async def google_login() -> RedirectResponse:
    """Redirect user to Google OAuth consent screen."""
    params = (
        f"?client_id={settings.GOOGLE_CLIENT_ID}"
        f"&redirect_uri={settings.GOOGLE_REDIRECT_URI}"
        f"&response_type=code"
        f"&scope=openid%20email%20profile"
        f"&access_type=offline"
    )
    return RedirectResponse(url=GOOGLE_AUTH_URL + params)


@router.get("/google/callback")
async def google_callback(
    code: str,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> RedirectResponse:
    """Exchange Google code, upsert user, issue tokens, redirect to frontend."""
    token_data = await exchange_google_code(code)
    google_payload = decode_google_id_token(token_data["id_token"])
    user = await upsert_user(db, google_payload)

    access_token, raw_refresh = await create_session(db, str(user.id))

    redirect = RedirectResponse(
        url=f"{settings.FRONTEND_URL}/auth/callback?token={access_token}"
    )
    _set_refresh_cookie(redirect, raw_refresh)
    return redirect


@router.post("/refresh", response_model=TokenResponse)
async def refresh(
    response: Response,
    refresh_token: str | None = Cookie(default=None, alias=REFRESH_COOKIE),
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    """Rotate refresh token and return new access token."""
    if not refresh_token:
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No refresh token",
        )

    new_access, new_refresh, _ = await rotate_refresh_token(db, refresh_token)
    _set_refresh_cookie(response, new_refresh)
    return TokenResponse(access_token=new_access)


@router.post("/logout", status_code=204)
async def logout(
    response: Response,
    refresh_token: str | None = Cookie(default=None, alias=REFRESH_COOKIE),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
) -> None:
    """Revoke current refresh token and clear cookie."""
    if refresh_token:
        await revoke_token(db, refresh_token)
    _clear_refresh_cookie(response)


@router.post("/logout-all", status_code=204)
async def logout_all(
    response: Response,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    """Revoke all refresh tokens for the user (all devices)."""
    await revoke_all_tokens(db, str(current_user.id))
    _clear_refresh_cookie(response)
