# Phase 1.3 — Google OAuth + JWT Backend
**Status:** DONE  
**Date:** 2026-06-20  
**Goal:** Implement the full server-side authentication system — Google OAuth 2.0 login, JWT issuance, token refresh with rotation, and logout — so that the frontend has a secure, stateless auth layer to build on.

---

## What Was Built

```
backend/app/
├── schemas/
│   ├── auth.py          ← TokenResponse (access_token + token_type)
│   └── user.py          ← UserMe (profile response shape)
├── services/
│   └── auth.py          ← all auth business logic (pure functions, no HTTP concerns)
├── api/v1/
│   ├── deps.py          ← get_current_user FastAPI dependency
│   └── routes/
│       ├── auth.py      ← 5 auth endpoints
│       └── users.py     ← GET /users/me
```

**Endpoints registered:**

| Method | Path | Auth required |
|---|---|---|
| `GET` | `/api/v1/auth/google` | No |
| `GET` | `/api/v1/auth/google/callback` | No |
| `POST` | `/api/v1/auth/refresh` | Refresh cookie |
| `POST` | `/api/v1/auth/logout` | Bearer + cookie |
| `POST` | `/api/v1/auth/logout-all` | Bearer |
| `GET` | `/api/v1/users/me` | Bearer |

---

## Concepts Explained

### 1. What Is OAuth 2.0 and Why Do We Use It?

**The problem:** We don't want to manage passwords. Storing passwords means handling hashing, breach response, reset flows, brute-force protection — all complex, all security-critical.

**The solution:** Delegate identity to Google. "I don't know who you are, but Google does. Prove to Google that you're you, and Google will tell me."

OAuth 2.0 is the protocol that makes this delegation work. It has several "flows" (ways of doing the exchange). We use the **Authorization Code Flow** — the most secure one.

---

### 2. The Authorization Code Flow — Step by Step

```
User                  Frontend             Backend              Google
 |                       |                    |                    |
 |-- clicks "Sign in" -->|                    |                    |
 |                       |-- GET /auth/google--->                  |
 |                       |                    |-- redirect ------->|
 |<-------------------------------------------redirect to Google--|
 |                       |                    |                    |
 |-- enters Google creds and approves ------->|                    |
 |                       |                    |<-- code -----------|
 |                       |                    |                    |
 |                       |                    |-- POST (code) ---->|
 |                       |                    |<-- id_token -------|
 |                       |                    |                    |
 |                       |                    |-- upsert user      |
 |                       |                    |-- issue JWT        |
 |                       |<-- redirect with token                  |
 |<-- lands on dashboard |                    |                    |
```

**Why not just send the user directly to Google with a redirect?**  
The frontend could technically do the entire redirect. But the "code exchange" step (trading the code for tokens) must happen **server-side** — because it requires your `GOOGLE_CLIENT_SECRET`, which must never be exposed to the browser.

This is the key security property of the Authorization Code Flow: the secret stays on the server.

---

### 3. `GET /auth/google` — The Redirect

```python
GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"

params = (
    f"?client_id={settings.GOOGLE_CLIENT_ID}"
    f"&redirect_uri={settings.GOOGLE_REDIRECT_URI}"
    f"&response_type=code"
    f"&scope=openid%20email%20profile"
    f"&access_type=offline"
)
return RedirectResponse(url=GOOGLE_AUTH_URL + params)
```

**Each parameter explained:**

| Param | Value | Why |
|---|---|---|
| `client_id` | Your Google OAuth app ID | Tells Google which app is requesting |
| `redirect_uri` | `localhost:8000/api/v1/auth/google/callback` | Where Google sends the user back after approval |
| `response_type=code` | `code` | Requests an authorization code (not a token directly — that's the less secure implicit flow) |
| `scope=openid email profile` | Three scopes | `openid` = ID token; `email` = user's email; `profile` = name, picture |
| `access_type=offline` | `offline` | Requests a refresh token from Google (we don't actually use Google's refresh token — we use our own — but this is standard practice) |

---

### 4. `GET /auth/google/callback` — The Code Exchange

This is the most important endpoint. Google redirects the user here with a one-time `code` in the query string.

```python
async def google_callback(code: str, response: Response, db: AsyncSession):
    # Step 1: Exchange code for tokens
    token_data = await exchange_google_code(code)

    # Step 2: Decode the ID token to get user info
    google_payload = decode_google_id_token(token_data["id_token"])

    # Step 3: Upsert user in DB
    user = await upsert_user(db, google_payload)

    # Step 4: Issue our own tokens
    access_token, raw_refresh = await create_session(db, str(user.id))

    # Step 5: Redirect to frontend with access token
    redirect = RedirectResponse(url=f"{FRONTEND_URL}/auth/callback?token={access_token}")
    _set_refresh_cookie(redirect, raw_refresh)
    return redirect
```

Each step is in its own service function — the route handler is just an orchestrator.

---

### 5. Google ID Token vs Google Access Token

When you exchange the code, Google returns two things:

| Token | What it is | What we use it for |
|---|---|---|
| `id_token` | A JWT signed by Google containing user identity | Extract `sub`, `email`, `name`, `picture` |
| `access_token` | A credential to call Google APIs on the user's behalf | **Not used** — we don't call Google APIs as the user |

We only care about the `id_token`. It contains everything we need to create or update the user record.

**Why decode without signature verification?**

```python
def decode_google_id_token(id_token: str) -> dict:
    return jwt.decode(
        id_token,
        key="",
        options={"verify_signature": False, "verify_aud": False},
    )
```

Normally you should verify a JWT's signature. But here we skip it — safely — because:

1. We received the `id_token` directly from `https://oauth2.googleapis.com/token` over HTTPS
2. That connection is already authenticated via TLS (the certificate proves we're talking to Google)
3. A man-in-the-middle cannot forge this token because they can't intercept an authenticated HTTPS connection

If we received the token from the user's browser (as in the implicit flow), we would need to verify the signature. But we don't — it came straight from Google's server to ours.

---

### 6. The Upsert — `ON CONFLICT DO UPDATE`

```python
stmt = (
    insert(User)
    .values(google_id=..., email=..., name=..., avatar_url=..., is_active=True)
    .on_conflict_do_update(
        index_elements=["google_id"],
        set_={"email": ..., "name": ..., "avatar_url": ...},
    )
    .returning(User)
)
```

**Why upsert instead of "check if exists, then insert or update"?**

The naive approach:
```python
user = await db.get(User, google_id=...)
if user:
    user.email = ...
else:
    db.add(User(...))
```

This has a **race condition**: two simultaneous logins from the same user (unlikely but possible) could both pass the `if user` check and both try to insert, causing a unique constraint violation.

The upsert is a single atomic SQL statement — no race condition possible. If the `google_id` already exists, update the profile fields. If not, insert. One round trip, always correct.

**Why don't we update `is_active` on conflict?**  
A soft-deleted user should not be automatically re-activated just by logging in. If `is_active = false`, the `get_current_user` dependency will reject their token — an admin would need to reactivate them.

---

### 7. Two-Token Strategy — Access + Refresh

This was designed in Phase 1.1 but this is where it gets implemented. Here's why the split matters:

```
Access Token                    Refresh Token
────────────                    ─────────────
Lives: 15 minutes               Lives: 7 days
Stored: browser memory (JS)     Stored: httpOnly cookie
Sent: Authorization header      Sent: automatically with cookie
Used: every API request         Used: only to get new access tokens
If stolen: useless in 15 min    If stolen: can get new access tokens
```

**The attack scenario this prevents:**

If you only had one long-lived token and it was stolen (via XSS, network sniff, etc.), the attacker has 7-day access. With two tokens:
- The access token expires in 15 minutes — window of attack is tiny
- The refresh token is `httpOnly` — JavaScript cannot read it, so XSS cannot steal it
- Even if the refresh token is stolen somehow, rotation detects it (see section 9)

---

### 8. The Refresh Cookie — Security Flags Explained

```python
response.set_cookie(
    key="refresh_token",
    value=raw_refresh,
    httponly=True,           # JS cannot read this cookie
    secure=settings.is_production,  # only sent over HTTPS in prod
    samesite="strict",       # never sent on cross-site requests
    max_age=7 * 24 * 60 * 60,
    path="/api/v1/auth",     # only sent to auth routes
)
```

Each flag is a separate layer of defense:

| Flag | What it does | Attack it prevents |
|---|---|---|
| `httponly=True` | Cookie invisible to `document.cookie` in JS | XSS — even if attacker injects script, they can't read the token |
| `secure=True` (prod) | Cookie only sent over HTTPS | Network sniffing / man-in-the-middle |
| `samesite="strict"` | Cookie not sent on requests from other domains | CSRF — attacker's site cannot trigger auth requests as the user |
| `path="/api/v1/auth"` | Cookie only attached to `/api/v1/auth/*` requests | Cookie not leaked to every API call — reduces exposure surface |

**Why `secure=False` in development?**  
`localhost` doesn't run HTTPS. `secure=True` would block the cookie entirely during dev. We use `settings.is_production` to toggle this.

---

### 9. Token Rotation — Why and How

Every time the frontend calls `POST /auth/refresh`, we don't just validate the old token — we **replace it**:

```python
async def rotate_refresh_token(db, raw_refresh):
    # 1. Find token in DB — must be un-revoked and un-expired
    token_row = await db.scalar(select(RefreshToken).where(...))
    if not token_row:
        raise 401

    # 2. Revoke the old token immediately
    token_row.revoked_at = now()

    # 3. Issue a brand new token
    new_access, new_refresh = await create_session(db, user_id)
    return new_access, new_refresh
```

**What this prevents:** Replay attacks.

Scenario without rotation:
- Attacker steals your 7-day refresh token from a network log
- They can use it anytime within 7 days — even after you've refreshed your own token

Scenario with rotation:
- Attacker steals the refresh token
- You use it first → it gets rotated → old token is revoked
- Attacker tries to use the old token → `401 Unauthorized` — it's already dead
- OR attacker uses it first → your next refresh call fails → you get logged out → you know something is wrong

---

### 10. `POST /auth/logout` vs `POST /auth/logout-all`

```python
# Logout (current device only)
async def revoke_token(db, raw_refresh):
    await db.execute(
        update(RefreshToken)
        .where(token_hash == hash(raw_refresh), revoked_at IS NULL)
        .values(revoked_at=now())
    )

# Logout-all (every device)
async def revoke_all_tokens(db, user_id):
    await db.execute(
        update(RefreshToken)
        .where(user_id == user_id, revoked_at IS NULL)
        .values(revoked_at=now())
    )
```

The `idx_refresh_tokens_user_id` index we created in Phase 1.2 makes `logout-all` fast — Postgres jumps directly to that user's tokens without scanning the entire table.

**Why not DELETE instead of UPDATE (revoked_at)?**  
Keeping revoked tokens with a timestamp is an audit trail. If you ever need to investigate "was this token used after revocation?" or "when did this session end?", the data is there. Storage cost is trivial.

---

### 11. The Redirect with Token in Query Param

```python
redirect = RedirectResponse(
    url=f"{FRONTEND_URL}/auth/callback?token={access_token}"
)
```

**Why a query param instead of a response body?**

The callback is a browser redirect — the user's browser follows it automatically. There is no "response body" for the frontend to read from a redirect. The browser just navigates to the new URL.

The frontend (`/auth/callback` page) reads the token from `window.location.search`, stores it in React state (memory), then immediately replaces the URL to remove the token from the address bar:

```javascript
const token = new URLSearchParams(window.location.search).get("token");
setAccessToken(token);
window.history.replaceState({}, "", "/dashboard"); // clean the URL
```

**Why not localStorage?**  
localStorage is readable by any JavaScript on the page — including injected scripts (XSS). Memory (React state) is not accessible outside the app's own JS.

---

### 12. `get_current_user` — The Auth Dependency

```python
bearer_scheme = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    user_id = decode_access_token(credentials.credentials)
    if not user_id:
        raise HTTPException(401, "Invalid or expired token")

    user = await db.scalar(select(User).where(User.id == user_id, User.is_active == True))
    if not user:
        raise HTTPException(401, "User not found or deactivated")
    return user
```

`HTTPBearer()` reads the `Authorization: Bearer <token>` header automatically. FastAPI's `Depends()` system means you add this to any route with one line:

```python
@router.get("/some-protected-route")
async def my_route(current_user: User = Depends(get_current_user)):
    # current_user is guaranteed to be a valid, active User
```

**Why check `is_active`?**  
When a user is soft-deleted, their existing access tokens (up to 15 min old) are still cryptographically valid JWTs. Checking `is_active` at the DB level means a deactivated user is immediately locked out — even if they have a fresh token.

---

### 13. Service Layer — Why Business Logic Lives in `services/`

The route handlers in `routes/auth.py` only do:
1. Parse input (query params, cookies, headers)
2. Call service functions
3. Build the HTTP response (set cookies, return JSON)

All actual logic — token hashing, DB queries, upsert logic, rotation — lives in `services/auth.py`.

**Why separate them?**

- **Testability:** You can test `rotate_refresh_token(db, token)` directly without spinning up an HTTP server. Route handlers are hard to test in isolation.
- **Reusability:** If a background job or a CLI script needs to create a session, it calls the service function — not an HTTP endpoint.
- **Readability:** Routes describe *what* the API surface is. Services describe *how* the business rules work. Mixed together, both become hard to understand.

---

### 14. Pydantic Schemas — The API Contract

```python
class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

class UserMe(BaseModel):
    id: uuid.UUID
    email: str
    name: str
    avatar_url: str | None
    is_active: bool
    model_config = {"from_attributes": True}
```

**Why `from_attributes = True` on `UserMe`?**

By default, Pydantic expects a dictionary as input. `from_attributes = True` lets it read from an ORM object directly:

```python
# Without from_attributes — would fail:
UserMe(user_orm_object)  # Pydantic can't read SQLAlchemy attributes

# With from_attributes — works:
UserMe.model_validate(user_orm_object)  # Pydantic reads .id, .email, etc.
```

**Why not return the ORM model directly?**

SQLAlchemy models expose everything — including internal fields you might not want to send to the client (`google_id`, `created_at`, future sensitive fields). The schema is a deliberate contract: "here is exactly what the API promises to return, nothing more."

---

## Verification

```bash
cd backend

# 1. Confirm all routes are registered
.venv/bin/python -c "
from app.main import app
schema = app.openapi()
for path in schema['paths']:
    print(path)
"
# → /api/v1/health
# → /api/v1/auth/google
# → /api/v1/auth/google/callback
# → /api/v1/auth/refresh
# → /api/v1/auth/logout
# → /api/v1/auth/logout-all
# → /api/v1/users/me

# 2. Start the server
.venv/bin/uvicorn app.main:app --reload

# 3. Test the redirect (should return 307 to Google)
curl -I http://localhost:8000/api/v1/auth/google
# → HTTP/1.1 307 Temporary Redirect
# → location: https://accounts.google.com/o/oauth2/v2/auth?...

# 4. Test a protected route without a token (should return 403)
curl http://localhost:8000/api/v1/users/me
# → {"detail": "Not authenticated"}

# 5. Full OAuth flow test
# → Set GOOGLE_CLIENT_ID + GOOGLE_CLIENT_SECRET + GOOGLE_REDIRECT_URI in .env
# → Open http://localhost:8000/api/v1/auth/google in browser
# → Complete Google login
# → Browser lands on frontend /auth/callback?token=eyJ...
```

---

## Key Takeaways

1. **Authorization Code Flow** — the `client_secret` never leaves the server. The browser only ever sees the one-time `code`, not the actual tokens from Google.
2. **ID token ≠ Access token** — we use Google's `id_token` for identity, not the `access_token`. We never call Google APIs as the user.
3. **Decode without verify is safe here** — because we got the token directly from Google's HTTPS endpoint, not from the user's browser.
4. **Upsert is atomic** — `ON CONFLICT DO UPDATE` eliminates the race condition in "check-then-insert" logic.
5. **Two tokens, two lifetimes** — 15-minute access token in memory + 7-day refresh token in `httpOnly` cookie. Short window for theft, long session for UX.
6. **Five cookie flags** — `httponly`, `secure`, `samesite=strict`, `path=/api/v1/auth`, `max_age`. Each blocks a different attack vector.
7. **Token rotation** — every refresh call invalidates the old token. Stolen tokens self-destruct as soon as the real user refreshes.
8. **Service layer** — routes handle HTTP, services handle business logic. Never mix them.
9. **`is_active` check in dependency** — valid JWT ≠ valid user. Always verify the user still exists and is active in the DB.
10. **Pydantic schemas are the API contract** — they define exactly what the client receives, independent of what the ORM model looks like internally.

---

## Next: Phase 1.4 — Auth Frontend

Build the Next.js login page, auth context provider (token in memory), silent token refresh interceptor, and protected route wrapper.
