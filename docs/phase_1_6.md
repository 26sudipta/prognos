# Phase 1.6 — Handle Verification Backend
**Status:** DONE  
**Date:** 2026-06-22  
**Goal:** Implement the Codeforces handle ownership verification system. Before PROGNOS can sync a user's competitive programming data, it must cryptographically prove the user owns the CF account they claim. This phase delivers the full backend: CF API integration, token challenge-response, lockout policy, and soft-delete unlinking.

---

## What Was Built

```
backend/
├── app/
│   ├── api/v1/
│   │   ├── __init__.py                     ← added handles router
│   │   └── routes/
│   │       └── handles.py                  ← 4 route handlers (new)
│   ├── schemas/
│   │   └── handle.py                       ← request/response Pydantic models (new)
│   └── services/
│       └── handle.py                       ← all business logic + CF API client (new)
└── tests/
    ├── unit/
    │   └── test_handle_service.py          ← 9 unit tests (new)
    └── integration/
        └── test_handle_routes.py           ← 6 integration tests (new)
```

**No new migration** — all columns were provisioned in Phase 1.5.

---

## Concepts Explained

### 1. Why Challenge-Response Ownership Proof

PROGNOS needs to link a user's account to a Codeforces profile before syncing their data. Anyone can type any handle — "tourist", "Um_nik", anyone's username. Without proof, a malicious user could claim another person's handle and see their private performance analytics or pollute a classroom leaderboard.

The proof mechanism: only the true owner of a CF account can write to its profile fields. We generate a one-time token, ask the user to paste it into their CF `lastName` field, then read it back via the CF API. A third party cannot do this — they don't have login access to the CF account.

This is the same pattern used by DNS ownership verification (TXT records) and domain-based email verification.

### 2. The 5-Step Flow and Where Code Lives

| Step | Actor | Code location |
|---|---|---|
| 1. User submits handle | Frontend | `POST /handles/verify/initiate` route |
| 2. Backend validates handle on CF | `services/handle.py` | `fetch_cf_user()` |
| 3. Backend generates token, stores in DB | `services/handle.py` | `initiate_verification()` |
| 4. User pastes token into CF profile | User, on codeforces.com | (no code — manual step) |
| 5. User triggers check, backend reads CF API | `services/handle.py` | `confirm_verification()` |

Steps 1–3 are one HTTP call (`POST /initiate`). Steps 4–5 span two HTTP calls with a human action in between.

### 3. Token Format: PGS-XXXXXX

```python
def generate_verification_token() -> str:
    return "PGS-" + secrets.token_hex(3).upper()
```

- `PGS-` — fixed prefix (PROGNOS project identifier)
- `secrets.token_hex(3)` — 3 random bytes → 6 hex characters, uppercase
- Result: `PGS-A3F7B2` — 10 characters total, always `[0-9A-F]`

Design choices:
- `secrets` module uses the OS CSPRNG — cryptographically unpredictable
- Hex-only character set avoids ambiguous characters (`O` vs `0`, `I` vs `1`, `l` vs `1`)
- The `PGS-` prefix makes it visually obvious in a CF profile that this is a PROGNOS token — users won't confuse it with existing data
- 6 hex characters = 16^6 = ~16.7 million possible values — large enough that brute-forcing the token within 30 minutes is infeasible, especially with the 5-attempt lockout

### 4. Handling Duplicate Handles: Three Scenarios

The most nuanced logic in `initiate_verification()` covers three cases for handle ownership conflicts:

**Case A — Another verified account owns this handle:**
```
Another user has: handle="tourist", is_verified=True, is_active=True
→ 409 Conflict. The handle is permanently claimed. Current user cannot proceed.
```

**Case B — Another account has this handle unverified (pending):**
```
Another user has: handle="tourist", is_verified=False, is_active=True
→ Supersede: set their row is_active=False, proceed for current user.
```
This is the "first verified owner wins" rule. An unverified pending claim is not a real claim — it might be abandoned or a mistake. The new initiator supersedes it. When they successfully verify, the handle is theirs.

**Case C — Current user already has a verified active handle for this platform:**
```
Current user has: platform="codeforces", is_verified=True, is_active=True
→ 422 Unprocessable. They must unlink their current handle first.
```
This prevents silently overwriting a working linked handle. The user must make an explicit decision.

```python
# All three checks happen in sequence inside initiate_verification():
# 1. CF API call
# 2. Check Case A → 409
# 3. Handle Case B → soft-delete their row
# 4. Check Case C → 422
# 5. Create or update row
```

### 5. Update In-Place vs. Create New Row

When a user re-initiates (e.g. the token expired and they want a fresh one), the service does **not** create a second row. It finds the existing unverified active row for this user+platform and updates it:

```python
existing.handle = handle
existing.verification_token = new_token
existing.verification_token_expires_at = new_expiry
existing.verification_attempt_count = 0
existing.is_locked = False
```

Why: the partial unique index (`UNIQUE (user_id, platform) WHERE is_active = true`) would reject a second INSERT anyway. But beyond the constraint, it's semantically correct — re-initiating is a refresh of an in-progress flow, not a new entity. The same row tracks the full history of the attempt.

### 6. Token Expiry vs. Lockout — Two Independent Blocks

There are two distinct failure modes a `confirm` call can hit before even touching the CF API:

| Check | HTTP code | What it means |
|---|---|---|
| `is_locked = True` AND `lockout_expires_at > now` | **423 Locked** | Too many wrong tokens — hard block, wait for expiry |
| `verification_token_expires_at < now` | **410 Gone** | 30-minute window passed — re-initiate to get a new token |

The lockout check runs **before** the expiry check. Reason: a locked handle should be locked regardless of whether the token also happens to be expired. The user needs to wait out the lockout, then re-initiate to get a fresh token.

Expiry does **not** count against the attempt limit (per the spec). If a user lets the token window lapse, they get a fresh 5 attempts with the new token.

---

## Updates

### 2026-06-23 — Verification field changed to Organization; token window extended

**What changed:**

| # | Before | After | Why |
|---|---|---|---|
| Proof field | `lastName` (CF API) | `organization` (CF API) | `lastName` is a real-name field users don't want overwritten. `organization` is a scratch field purpose-built for this. |
| Fallbacks | none | `firstName`, `lastName` as silent fallbacks | Belt-and-suspenders; catches future CF settings renames. |
| Token window | 30 minutes | **60 minutes** | Users who are new to CF settings need more time to find the field and navigate back. |
| Comparison | `last_name == token` | `cf_org.strip() == token` | `.strip()` prevents CF from silently adding trailing whitespace causing a mismatch. |
| Frontend URL | `codeforces.com/settings/general` | `codeforces.com/settings/social` | Last Name and Organization fields live in Social, not General. The wrong URL was the root cause of user confusion in testing. |

**Files changed:**
- `backend/app/services/handle.py` — `confirm_verification()` now reads `organization`; `.strip()` added; `TOKEN_EXPIRY_MINUTES` = 60
- `frontend/app/(dashboard)/handles/page.tsx` — URL corrected; instructions updated to say "Organization field"

**Live verification test (2026-06-23):**
```
CF API user.info → organization: "PGS-E7BC86"
DB token         → "PGS-E7BC86"
POST /handles/verify/confirm → 200 OK
{ "handle": "sudiptadas", "verified_at": "..." }
```

### 7. The 400 Response with Structured Error Detail

When a token doesn't match, the response is:
```json
HTTP 400
{
  "detail": {
    "message": "Token not found in Codeforces profile lastName field",
    "attempts_remaining": 3
  }
}
```

`attempts_remaining` is surfaced so the frontend can tell the user how many tries they have left without them needing to guess. FastAPI propagates the dict as the `detail` field of its standard error response.

On the 5th failure:
```python
row.is_locked = True
row.lockout_expires_at = now + timedelta(hours=1)
```
`attempts_remaining` is returned as `0`, signalling to the frontend to switch to the locked UI state.

### 8. CF API Integration Pattern

```python
CF_USER_INFO_URL = "https://codeforces.com/api/user.info"

async def fetch_cf_user(handle: str) -> dict:
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get(CF_USER_INFO_URL, params={"handles": handle})
    data = resp.json()
    if resp.status_code != 200 or data.get("status") != "OK":
        raise HTTPException(status_code=404, detail=f"Codeforces handle '{handle}' not found")
    return data["result"][0]
```

Key decisions:
- `httpx.AsyncClient` — non-blocking, consistent with the rest of the async FastAPI stack
- `timeout=10.0` — CF API can be slow; 10s is generous but avoids hanging forever
- Check both HTTP status code AND `data["status"] == "OK"` — CF returns 200 with `status: FAILED` for invalid handles
- Returns `result[0]` — CF returns a list even for single-handle lookups; `result[0]` is always the requested user

The same `fetch_cf_user()` is called from both `initiate` (to verify the handle exists) and `confirm` (to read the `lastName` field). Two separate HTTP calls, intentional — the CF profile may have been updated between the two requests.

### 9. Test Architecture: Unit + Integration Split

**Unit tests** (`tests/unit/test_handle_service.py`) — 9 tests:
- No database, no real HTTP calls
- CF API mocked with `respx` (`@respx.mock` decorator)
- DB mocked with `AsyncMock` / `MagicMock`
- Tests: token format, CF 404 propagation, 409 conflict detection, 410 expiry, 423 lockout, attempt increment, 5th-failure lockout trigger

**Integration tests** (`tests/integration/test_handle_routes.py`) — 6 tests:
- Real PostgreSQL database (via `db_session` fixture from `conftest.py`)
- CF API mocked with `respx` — we don't want real network calls in CI
- Tests: row creation in DB, supersede behavior, in-place update, happy-path confirm, active-only list, soft-delete

Why mock CF even in integration tests: Codeforces is an external service with rate limits and potential downtime. Tests must be deterministic and fast. The CF API integration is separately validated by the unit tests for `fetch_cf_user()`.

---

## Verification

```bash
cd backend

# 1. Run all tests
.venv/bin/python -m pytest tests/ -v
# 19 passed in ~0.76s

# 2. Start the dev server
.venv/bin/uvicorn app.main:app --reload

# 3. Initiate verification (replace Bearer token with real JWT from login)
curl -X POST http://localhost:8000/api/v1/handles/verify/initiate \
  -H "Authorization: Bearer <your_access_token>" \
  -H "Content-Type: application/json" \
  -d '{"handle": "your_cf_handle", "platform": "codeforces"}'
# Response 201:
# {"handle_id": "...", "handle": "...", "token": "PGS-A3F7B2", "expires_at": "..."}

# 4. Paste the token into your CF profile lastName field on codeforces.com

# 5. Confirm
curl -X POST http://localhost:8000/api/v1/handles/verify/confirm \
  -H "Authorization: Bearer <your_access_token>" \
  -H "Content-Type: application/json" \
  -d '{"handle_id": "<handle_id from step 3>"}'
# Response 200:
# {"handle_id": "...", "handle": "...", "platform": "codeforces", "verified_at": "..."}

# 6. List your handles
curl http://localhost:8000/api/v1/handles \
  -H "Authorization: Bearer <your_access_token>"
# Response: [{"id": "...", "is_verified": true, ...}]
```

---

## Key Takeaways

- **Challenge-response is the correct ownership proof pattern for third-party accounts.** Ask the user to write a unique token to a field only they can write, then read it back — no passwords, no OAuth from the third party required.
- **Two calls to the CF API are intentional.** `initiate` checks the handle exists; `confirm` reads the `lastName`. They're separate because the CF profile may have been updated between the two requests.
- **Lockout and expiry are independent failure modes with different semantics.** Lockout = punishment for wrong tokens (hard block). Expiry = natural timeout (soft, no penalty, re-initiate to reset).
- **Always check both HTTP status AND CF's `status` field.** CF returns 200 OK for "handle not found" errors with `status: FAILED` in the JSON body.
- **`respx` is the right tool for mocking `httpx` in tests.** It integrates with pytest via a decorator and intercepts at the transport layer — no patching needed.
- **Re-initiate updates in place, not a new row.** The partial unique index would block a duplicate anyway, but the update-in-place is also the correct semantic: it's one ongoing verification attempt, not a new entity.

---

## Next

**Phase 1.7 — Handle Verification Frontend:** implement the 5-state UI (`NO_HANDLE → PENDING → SUCCESS / FAILED / LOCKED`) that drives users through the verification flow.
