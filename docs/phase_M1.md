# Phase M1 — Mobile Auth (Google Sign-In)

**Status:** Built & statically verified — 2026-07-03. Live device sign-in gated on the user
creating the Google OAuth clients (below).

## What Was Built

Native Google Sign-In → verified backend token exchange → session that survives app restart and
auto-refreshes on 401. This unlocks every authenticated screen after it.

```
backend/
  app/services/auth.py            # + verify_google_id_token()  (verifies, unlike decode_*)
  app/api/v1/routes/auth.py       # + POST /auth/google/mobile, POST /auth/refresh/mobile
  app/schemas/auth.py             # + GoogleMobileRequest, MobileRefreshRequest, MobileTokenResponse
  pyproject.toml                  # + google-auth, requests
  tests/integration/test_auth_service.py  # +5 tests (verify boundary, endpoints)

mobile/lib/
  core/config/app_config.dart     # + googleServerClientId (the web client id)
  core/auth/
    app_user.dart                 # profile model (GET /users/me)
    token_store.dart              # in-memory access-token holder
    auth_api.dart                 # googleMobile / refreshMobile / me
    auth_repository.dart          # google_sign_in v7 orchestration + storage
    auth_controller.dart          # AsyncNotifier<AppUser?> — restore/signIn/signOut
  core/network/
    auth_interceptor.dart         # Bearer inject + one-shot refresh-on-401
    dio_client.dart               # bare authDioProvider + authed dioProvider
  ui/auth/
    login_screen.dart             # "Continue with Google"
    auth_gate.dart                # splash → login | shell
  ui/shell/home_shell.dart        # now shows user + sign-out
```

## Concepts Explained

### 1. Why a *verifying* endpoint (the security crux)
The web callback uses `decode_google_id_token`, which **skips signature verification** — safe only
because that token came straight from Google over a server↔Google HTTPS exchange. The mobile token
arrives **from the device**, so it must be fully verified. `verify_google_id_token` uses
`google.oauth2.id_token.verify_oauth2_token(token, Request(), GOOGLE_CLIENT_ID)`, which in one call
checks the **signature** (against Google's public keys), **expiry**, **issuer**, and **audience**.
Copying the no-verify path would have been an auth bypass — a test asserts the endpoint uses the
verifying path (patching the google-auth boundary lets an otherwise-bogus token through only there).

### 2. The audience must line up end-to-end
`verify_oauth2_token` requires `aud == GOOGLE_CLIENT_ID`. The app requests the ID token with
`serverClientId = <web client id>`, which makes the token's audience that web client id — the same
value already in the backend's `GOOGLE_CLIENT_ID` (verified identical). `serverClientId` must be set
on **both** Android and iOS, or the audience becomes the native client id and every sign-in 401s.
The single-audience check is kept strict on purpose (widening it would weaken verification).

### 3. Token transport: body, not cookie
Native apps can't use `httpOnly` cookies, so `/auth/google/mobile` and `/auth/refresh/mobile`
return the pair **in the body**. The app keeps the **access token in memory** and the **refresh
token in the OS keystore** (`flutter_secure_storage`). Refresh **rotates** (old token revoked), so
the interceptor persists the new refresh token on every refresh — a launch-time restore otherwise
breaks. All token creation/rotation reuses the existing `create_session` / `rotate_refresh_token`.

### 4. google_sign_in v7 (breaking change) — read, don't guess
v7 replaced the old `GoogleSignIn().signIn()` with `GoogleSignIn.instance` +
`initialize(serverClientId:)` + `authenticate()`, and split authentication (`idToken`) from
authorization. The code was written against the **installed package's actual source**, and
cancellation is handled cleanly (`GoogleSignInException.code == canceled` → treated as "not signed
in", not an error).

### 5. Two Dio clients avoid refresh recursion
`authDioProvider` (bare) serves the auth endpoints; `dioProvider` (with `AuthInterceptor`, a
`QueuedInterceptor` so concurrent 401s trigger one refresh) serves all M2+ data calls. The
interceptor injects the Bearer, and on a 401 refreshes once, retries the original request, and on
refresh failure clears the session so the gate routes back to login.

## ⚠️ Your one manual step (unblocks live sign-in)
Create two OAuth clients in the **same Google Cloud project** (Credentials → Create OAuth client ID):
- **Android** — package `io.prognos.prognos`, SHA-1 `9B:4F:4A:42:11:3F:C5:9A:B3:70:EB:C1:1C:37:C9:D3:89:21:84:11`
- **iOS** — bundle `io.prognos.prognos`

No secrets are produced; the existing **Web** client id is the audience (already configured). Until
the Android client exists, `authenticate()` will fail on device.

## Verification

```bash
# Backend
cd backend && .venv/bin/python -m pytest -q tests/integration/test_auth_service.py   # 16 passed
# Flutter
cd mobile && flutter analyze   # clean
flutter test                   # 3 passed (login gate, shell, CF ladder)
flutter build apk --debug --dart-define=API_BASE_URL=https://prognos-api.onrender.com
```

- Backend: valid token → pair issued + refresh row created; forged/expired → 401; bad issuer → 401;
  refresh/mobile rotates and revokes the old token.
- **Live (after OAuth clients exist):** sign in on the emulator → lands on the shell showing your
  name; kill & reopen → silent restore (no re-login); tap sign-out → back to login.

## Key Takeaways
- Device-supplied identity tokens must be **fully verified**; the audience must match the app's
  `serverClientId` exactly, on both platforms.
- Refresh **rotation** means the client must persist the new refresh token every time.
- Pin third-party API usage to the **installed package's source**, not memory — google_sign_in v7
  was a breaking change.

## Next
**M2 — Contests + offline cache:** the first tab with real data (contest list/calendar from
`GET /contests`, cached in `drift`, background refresh via `workmanager`), feeding M3 reminders.
