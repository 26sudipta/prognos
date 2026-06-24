# PROGNOS — Implementation Plan

**Status:** Ready to Build  
**Last Updated:** 2026-06-18

> Living document. Update `PROGRESS.md` after every session. Never start Phase N+1 before Phase N is verified.

---

## Architecture Overview

**Stack:**
| Layer | Technology |
|---|---|
| Backend API | FastAPI (Python, async) |
| ORM / Migrations | SQLAlchemy 2.x + Alembic |
| Auth | Google OAuth 2.0 + JWT (python-jose) |
| Task Queue | Celery + Redis |
| Database | PostgreSQL 15 |
| Web Frontend | Next.js 14 (TypeScript, App Router) |
| UI | Tailwind CSS + shadcn/ui |
| Charts | Recharts |
| Python PM | uv |
| Deployment | Railway (web service + worker service + PostgreSQL plugin + Redis plugin) |

**Design rules:**

- Frontends are dumb — only read pre-computed data, never aggregate on request.
- Schema-first — Pydantic models defined before routes.
- All timestamps in UTC in DB; convert to local time client-side only.
- No Next.js Server Actions for core data fetching — pure REST.

---

## Repository Structure (Monorepo)

```
prognos/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   └── v1/
│   │   │       ├── routes/
│   │   │       │   ├── auth.py
│   │   │       │   ├── handles.py
│   │   │       │   ├── analytics.py
│   │   │       │   ├── contests.py
│   │   │       │   └── classrooms.py
│   │   │       └── __init__.py
│   │   ├── core/
│   │   │   ├── config.py         ← Pydantic Settings (reads .env)
│   │   │   ├── security.py       ← JWT issue/verify, token hashing
│   │   │   └── database.py       ← SQLAlchemy async engine + session factory
│   │   ├── models/               ← SQLAlchemy ORM table definitions
│   │   │   ├── user.py           ← users, refresh_tokens
│   │   │   ├── handle.py         ← user_handles
│   │   │   ├── analytics.py      ← submissions, submission_tags, daily_activity, tag_stats, rating_history
│   │   │   ├── signals.py        ← weakness_signals, recommendation_sets, recommendations
│   │   │   ├── contest.py        ← contests
│   │   │   └── classroom.py      ← classrooms, classroom_invites, classroom_memberships, classroom_leaderboard
│   │   ├── schemas/              ← Pydantic request/response models (mirrors models/ structure)
│   │   ├── services/
│   │   │   ├── auth.py           ← OAuth token exchange, user upsert
│   │   │   ├── analytics.py      ← weakness detection, recommendation generation
│   │   │   └── classroom.py      ← leaderboard cache rebuild, cohort analytics
│   │   ├── workers/
│   │   │   ├── celery_app.py     ← Celery app instance + beat schedule
│   │   │   ├── cf_sync.py        ← Codeforces incremental sync task
│   │   │   └── clist_sync.py     ← CLIST contest sync task
│   │   └── main.py               ← FastAPI app factory, router registration
│   ├── alembic/
│   │   ├── versions/
│   │   └── env.py
│   ├── tests/
│   │   ├── unit/
│   │   └── integration/
│   ├── Dockerfile
│   ├── pyproject.toml            ← uv-managed, includes dev deps
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── app/                  ← App Router: (auth)/login, (dashboard)/..., classrooms/...
│   │   ├── components/
│   │   │   ├── ui/               ← shadcn/ui primitives
│   │   │   ├── dashboard/        ← heatmap, streak, chart components
│   │   │   └── classroom/        ← leaderboard, invite, cohort components
│   │   ├── lib/
│   │   │   ├── api.ts            ← typed fetch wrapper with auto-refresh
│   │   │   └── auth.ts           ← token storage in memory, refresh logic
│   │   └── types/                ← TypeScript interfaces mirroring backend schemas
│   ├── package.json
│   └── .env.example
├── railway.toml                  ← Railway service config
├── CLAUDE.md
├── PROGRESS.md
├── requirement.md
└── implementation.md             ← this file
```

---

## Phase 1 — Foundation & Auth

**Goal:** Running stack. Google sign-in works. Codeforces handle can be verified. Nothing else.

### 1.1 Project Scaffolding

**Deliverables:**

- `backend/` FastAPI app with `GET /api/v1/health → 200 OK`
- `frontend/` Next.js app with placeholder home page
- `backend/pyproject.toml` — uv-managed, dependencies: `fastapi`, `uvicorn`, `sqlalchemy[asyncio]`, `asyncpg`, `alembic`, `pydantic-settings`, `python-jose[cryptography]`, `httpx`, `ruff` (dev)
- `backend/Dockerfile` — multi-stage build for Railway
- `railway.toml` — two services: `web` (uvicorn) and `worker` (celery)
- `backend/.env.example` — all required vars documented
- Alembic initialized and connected to DB via `DATABASE_URL`

**Environment variables (backend):**

```
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/prognos
REDIS_URL=redis://localhost:6379/0
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
GOOGLE_REDIRECT_URI=http://localhost:8000/api/v1/auth/google/callback
JWT_SECRET=
JWT_REFRESH_SECRET=
FRONTEND_URL=http://localhost:3000
```

---

### 1.2 Database Migration: Auth Tables

**Alembic migration creates:**

```sql
-- users
CREATE TABLE users (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  email VARCHAR(255) UNIQUE NOT NULL,
  google_id VARCHAR(255) UNIQUE NOT NULL,
  name VARCHAR(255) NOT NULL,
  avatar_url TEXT,
  is_active BOOLEAN NOT NULL DEFAULT true,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- refresh_tokens
CREATE TABLE refresh_tokens (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  token_hash VARCHAR(255) UNIQUE NOT NULL,
  expires_at TIMESTAMPTZ NOT NULL,
  revoked_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_refresh_tokens_user_id ON refresh_tokens(user_id);
```

---

### 1.3 Google OAuth + JWT Backend

**Endpoints:**
| Method | Path | Auth |
|---|---|---|
| GET | `/api/v1/auth/google` | Public |
| GET | `/api/v1/auth/google/callback` | Public |
| POST | `/api/v1/auth/refresh` | Cookie |
| POST | `/api/v1/auth/logout` | Bearer |
| POST | `/api/v1/auth/logout-all` | Bearer |
| GET | `/api/v1/users/me` | Bearer |

**Token strategy:**

- Access JWT: 15-minute expiry, signed with `JWT_SECRET`, returned in response body.
- Refresh JWT: 7-day expiry, SHA-256 hash stored in `refresh_tokens`, sent as `httpOnly; Secure; SameSite=Strict` cookie.
- On rotation: old refresh token marked `revoked_at = now()`, new token issued.

**Callback flow:**

1. Exchange `code` with Google using `httpx`.
2. Decode Google ID token, extract `sub` (google_id), `email`, `name`, `picture`.
3. `INSERT ... ON CONFLICT (google_id) DO UPDATE` on `users`.
4. Issue access JWT + refresh cookie.
5. Redirect to `FRONTEND_URL/dashboard`.

---

### 1.4 Auth Frontend

**Pages/components:**

- `/login` — "Continue with Google" button → `GET /api/v1/auth/google`
- Auth context provider — stores access token in memory (React state/context, never localStorage)
- Axios/fetch interceptor — on 401, silently calls `POST /api/v1/auth/refresh`, retries original request
- `<ProtectedRoute>` — wraps dashboard pages, redirects to `/login` if no token
- Navbar — shows `avatar_url` + `name` when authenticated

---

### 1.5 Database Migration: Handle Table

**Alembic migration creates:**

```sql
CREATE TYPE platform_enum AS ENUM ('codeforces');
CREATE TYPE sync_status_enum AS ENUM ('idle', 'in_progress', 'completed', 'sync_error');
CREATE TYPE handle_status_enum AS ENUM ('active', 'suspended');

CREATE TABLE user_handles (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  platform platform_enum NOT NULL,
  handle VARCHAR(255) NOT NULL,
  is_verified BOOLEAN NOT NULL DEFAULT false,
  is_active BOOLEAN NOT NULL DEFAULT true,
  status handle_status_enum NOT NULL DEFAULT 'active',
  verification_token VARCHAR(50),
  verification_token_expires_at TIMESTAMPTZ,
  verification_attempt_count INT NOT NULL DEFAULT 0,
  is_locked BOOLEAN NOT NULL DEFAULT false,
  lockout_expires_at TIMESTAMPTZ,
  verified_at TIMESTAMPTZ,
  sync_status sync_status_enum NOT NULL DEFAULT 'idle',
  last_synced_at TIMESTAMPTZ,
  last_sync_error TEXT,
  last_manual_sync_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (user_id, platform, is_active)
);
```

---

### 1.6 Handle Verification Backend

**Endpoints:**
| Method | Path | Description |
|---|---|---|
| GET | `/api/v1/handles` | List user's handles + sync status |
| POST | `/api/v1/handles/verify/initiate` | Step 1–2: validate handle on CF, generate token |
| POST | `/api/v1/handles/verify/confirm` | Step 4–5: poll CF API, check lastName |
| DELETE | `/api/v1/handles/{id}` | Unlink handle (soft-delete, keep analytics data) |

**Initiate logic:**

1. Call `https://codeforces.com/api/user.info?handles={handle}` — 404 → reject.
2. Check no other verified account owns this handle → 409 if claimed.
3. Generate token: `"PGS-" + secrets.token_hex(3).upper()` (e.g. `PGS-A3F9C2`). Hex-only avoids ambiguous chars; `PGS-` prefix is visually distinct in a CF profile.
4. Store token + `expires_at = now() + 30min` in `user_handles`.
5. Return token + instructions.

**Confirm logic:**

1. Check token not expired (→ 410 Gone), handle not locked (→ 423 Locked).
2. Call CF `user.info` again, read `result[0].lastName`.
3. If `lastName == token` → mark verified, clear token.
4. Else → increment `verification_attempt_count`. If count ≥ 5 → set `is_locked = true`, `lockout_expires_at = now() + 1h`.
5. Return appropriate error with `attempts_remaining`.

---

### 1.7 Handle Verification Frontend

**UI states:**

- `NO_HANDLE` — form to enter CF handle + submit
- `PENDING` — shows token prominently, step-by-step instructions, "I've done it — Check now" button
- `SUCCESS` — "Handle verified!" confirmation, proceeds to dashboard
- `FAILED` — shows remaining attempts, retry button
- `LOCKED` — countdown to lockout expiry, option to start fresh after

---

### Phase 1 Verification Checklist

- [x] `GET /api/v1/health` → `200 OK` — health route wired in `routes/health.py`
- [x] Google OAuth full round-trip (redirect → callback → JWT → cookie) — `upsert_user`, `create_session`, cookie set via `_set_refresh_cookie`; verified by `test_upsert_user_*` + `test_create_session_*`
- [x] Silent token refresh works on 401 — `rotate_refresh_token` + dedup logic in `frontend/app/_lib/api.ts`; verified by `test_rotate_refresh_token_*`
- [x] Logout clears cookie and marks token revoked in DB — `revoke_token` + `_clear_refresh_cookie`; verified by `test_revoke_token_marks_single_token_revoked`
- [x] Handle verify happy path: initiate → paste token → confirm → `is_verified = true` — verified by `test_confirm_happy_path`
- [x] 5 failed confirms → `is_locked = true` — verified by `test_confirm_locks_on_5th_failure`
- [x] After lockout expiry, new initiate resets counter — lockout bypass check in `initiate_verification` + `test_initiate_updates_own_pending_row_not_duplicate`
- [x] Unverified user sees empty dashboard with handle-linking CTA — dashboard shows 3 placeholder cards + "Next step: Go to Handles to verify your Codeforces account" prompt (confirmed in `(dashboard)/dashboard/page.tsx`)
- [x] Verified user sees "Handle linked" status — SUCCESS state in `frontend/app/(dashboard)/handles/page.tsx`

---

## Phase 2 — Personal Analytics Engine

**Goal:** Real dashboard data for a verified user — heatmap, streaks, tags, rating trend, recommendations.

### 2.1 Celery + CF Sync Worker

**New DB tables (Alembic migration):**

```
submissions          ← cf_submission_id, problem_id, verdict, submitted_at (UTC), ...
submission_tags      ← submission_id FK, tag
daily_activity       ← user_handle_id FK, activity_date, submission_count
tag_stats            ← user_handle_id FK, tag, solved_count, attempt_count, acceptance_rate, ...
rating_history       ← user_handle_id FK, cf_contest_id, old_rating, new_rating, delta, contest_time
```

**Sync task (`cf_sync.py`):**

1. Fetch submissions where `submissionId > max(cf_submission_id)` (incremental). Full fetch if first sync.
2. Sleep 2s between paginated API calls.
3. Post-sync pipeline (in order): recompute `daily_activity` → `tag_stats` → `rating_history` → `weakness_signals` → `recommendations`.
4. Update `user_handles.sync_status`, `last_synced_at`.

**Manual sync endpoint:** `POST /api/v1/handles/{id}/sync`

- Returns 429 if `now() - last_manual_sync_at < 30 minutes`.

---

### 2.2 Analytics API

| Method | Path                               | Returns                                                                          |
| ------ | ---------------------------------- | -------------------------------------------------------------------------------- |
| GET    | `/api/v1/analytics/dashboard`      | heatmap grid (365 days), current_streak, longest_streak, total_solved, cf_rating |
| GET    | `/api/v1/analytics/tags`           | array of tag_stats rows                                                          |
| GET    | `/api/v1/analytics/rating-history` | array of {contest_name, new_rating, contest_time}                                |

All reads from derived tables. No raw aggregation.

---

### 2.3 Weakness + Recommendations Engine

**New DB tables:**

```
weakness_signals     ← user_handle_id FK, tag, signal_type, score, reason, computed_at
recommendation_sets  ← user_id FK, generated_at
recommendations      ← recommendation_set_id FK, problem_id, problem_name, tag, difficulty, url, reason, position
```

**Weakness rules:**

- Neglected: `last_activity_at < now() - 14d` AND `solved_count >= 1`
- Low success: `attempt_count >= 5` AND `acceptance_rate < 0.50`
- Under-practiced: `solved_count < 5`

**Recommendation algorithm:**

1. Sort `weakness_signals` by score desc. Take top 5 distinct tags.
2. For each tag: query CF problem set (cached) — filter by tag + difficulty in `[user_rating - 100, user_rating + 300]` + exclude solved.
3. If no match: expand band ±200, retry once.
4. Return 1 problem per tag (max 5 total).

**Endpoints:**
| Method | Path | |
|---|---|---|
| GET | `/api/v1/analytics/weakness` | Current signals |
| GET | `/api/v1/analytics/recommendations` | Latest recommendation set |
| POST | `/api/v1/analytics/recommendations/refresh` | Regenerate (no cooldown — local compute) |

---

### 2.4 Dashboard UI

- Activity heatmap (GitHub-style, 52-week grid, client-side UTC→local)
- Streak cards (current / longest)
- Rating trend line chart (Recharts, time-series)
- Skill matrix table (tag, solved, attempts, acceptance %)
- Weakness signals list (color-coded by type)
- 5 recommended problems (card per problem, tag + difficulty + reason + link)
- Sync status pill + "Sync now" button (disabled during cooldown)

### Phase 2 Verification Checklist

- [ ] Celery worker picks up task and completes full CF sync
- [ ] `daily_activity` populated correctly (group by UTC date)
- [ ] `tag_stats.acceptance_rate` computed correctly
- [ ] Neglected/low-success/under-practiced rules fire correctly
- [ ] Exactly 5 recommendations generated; none already solved by user
- [ ] Manual sync `POST` returns 429 within 30-min window
- [ ] Heatmap renders correctly in browser with real data

---

## Phase 3 — Contest Discovery

**Goal:** Browseable, filterable contest list and calendar from CLIST.

### 3.1 CLIST Sync Worker

- Register at clist.by for a free API key (add to `.env` as `CLIST_API_KEY`).
- Celery beat task: every 4 hours, fetch contests for next 30 days.
- Upsert into `contests` on `clist_id`.
- Store `last_synced_at` in a `sync_metadata` table or a dedicated row.

### 3.2 Contest API

- `GET /api/v1/contests` — query params: `platform` (repeatable), `from`, `to`, `limit`, `offset`
- `GET /api/v1/contests/calendar` — same filters, response grouped by date

### 3.3 Contest UI

- Contest list: platform badge, name, start/end time (local), duration, link
- Platform filter chips (dynamic from distinct DB values)
- Week/month calendar toggle (color-coded by platform)
- Countdown timer (live, client-side)
- Stale data banner: shown if `now() - last_synced_at > 8 hours`

### Phase 3 Verification Checklist

- [ ] CLIST Celery task runs on schedule and populates `contests`
- [ ] Filtering by platform returns correct subset
- [ ] All times displayed in user's local timezone
- [ ] Stale banner appears correctly

---

## Phase 4 — Classroom System

**Goal:** Teachers create classrooms; students join and see a transparent leaderboard.

### 4.1 DB Tables

```
classrooms              ← name, owner_id FK, is_active
classroom_invites       ← classroom_id FK, token, expires_at, revoked_at
classroom_memberships   ← classroom_id FK, user_id FK, role (teacher/student), invite_id FK
classroom_leaderboard   ← precomputed cache (classroom_id, user_id, cf_rating, solved_count, streaks, ...)
```

### 4.2 Backend

- Full CRUD per requirement.md §9.6
- Invite: multi-use, 7-day expiry, revocable (does not remove existing members)
- Join: requires `is_verified = true` on handle, else 403
- Leaderboard cache rebuild: Celery beat task every 60 minutes
- Teacher-only endpoints: cohort analytics, member removal

### 4.3 Frontend

- Create classroom form
- Invite link share (copy to clipboard + QR optional)
- Leaderboard table (sorted by CF rating desc)
- Student join page (`/join/{token}`)
- Teacher: cohort analytics panel (top weak tags by class average)
- Student: "My Classrooms" sidebar + leave button

### Phase 4 Verification Checklist

- [ ] Classroom create/delete works
- [ ] Invite link generates, works multi-use, expires after 7 days, revocation works
- [ ] Student join blocked without verified handle
- [ ] Leaderboard displays all members sorted by rating
- [ ] Removed/left student disappears from leaderboard immediately
- [ ] Cohort analytics correctly aggregates weakness signals

---

## Phase 5 — Mobile Companion [V2.0 — Not Yet Planned]

Flutter app. Starts only after Phase 4 is verified and signed off.
Scope: contest discovery, local alarms (`flutter_local_notifications` + `workmanager`), quick dashboard, offline SQLite cache.

---

## Phase 6 — AI Layer [V3.0 — Not Yet Planned]

LLM coaching. Reads pre-formatted JSON weakness/performance vectors from Phase 2 engine.
Starts after Phase 5 or as a parallel track.

---

## Railway Deployment Config

Two services in `railway.toml`:

**`web`** — FastAPI via uvicorn:

```
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

**`worker`** — Celery:

```
celery -A app.workers.celery_app worker --loglevel=info
```

**`beat`** — Celery beat scheduler (can run alongside worker or as separate service):

```
celery -A app.workers.celery_app beat --loglevel=info
```

Railway provides: PostgreSQL plugin + Redis plugin. Connection strings injected as env vars automatically.

---

## Execution Protocol (from CLAUDE.md)

1. **One slice at a time.** Phase N+1 only after Phase N checklist is fully green.
2. **Design before code.** For each task: schema → API contract → logic flow → approval → implement.
3. **Update `PROGRESS.md`** at the end of every session (mark DONE/IN_PROGRESS/TODO, log decisions).
4. **No guessing.** If something is undefined, ask. Do not assume.
