from pydantic import BaseModel


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class GoogleMobileRequest(BaseModel):
    """Google ID token obtained by native Google Sign-In on the device."""

    id_token: str


class MobileRefreshRequest(BaseModel):
    """Refresh token sent in the body by the mobile client (no cookie transport)."""

    refresh_token: str


class MobileTokenResponse(BaseModel):
    """Full token pair returned in the body — the mobile client stores the
    refresh token itself (Keystore/Keychain) since it cannot use httpOnly cookies."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # access-token lifetime in seconds
