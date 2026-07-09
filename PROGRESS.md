# PROGRESS.md — Implementation Log

## Current Status: LIVE & COMPLETE — web app deployed free (Vercel + Render + Neon + cron-job.org).
**Last Updated:** 2026-07-09 (Phase 5.3 — PWA: installable web app, iOS strategy)

---

## Phase 5.3 — PWA: Installable Web App [DONE]
**Completed:** 2026-07-09

**What was built:**
- `frontend/app/manifest.ts` — Next.js metadata route serving `/manifest.webmanifest`
  (standalone display, `start_url /dashboard`, brand colors `#070B14`)
- `frontend/public/sw.js` — minimal service worker: network-first navigations with inline
  branded offline fallback; cache-first for `/_next/static/` + `/icons/`; **never touches `/api/`**
- `frontend/app/_components/pwa-register.tsx` — SW registration, production only
- `frontend/app/_components/ios-install-hint.tsx` — dismissible Add-to-Home-Screen banner
  (iOS/iPadOS detection incl. iPad-as-Mac, standalone check, 3s delay, localStorage dismiss)
- Icon set generated via Pillow (matches favicon: indigo #6366F1 + white trend-line):
  `public/icons/icon-{192,512}.png`, maskable 512, `app/apple-icon.png` (180, full-bleed)
- `layout.tsx`: `appleWebApp` metadata + `themeColor` viewport; landing page copy updated

**Decision:** PWA chosen as the iOS strategy — user won't pay Apple's $99/yr; iOS blocks
sideloading entirely. Android keeps the native APK (alarms + widget); iPhone users install
the web app from Safari. Contest reminders stay Android-only until Web Push (iOS 16.4+) is
added later (needs push-subscriptions table + cron send worker).

**Verified:** `npm run build` clean; prod server smoke test — manifest JSON, `<link rel="manifest">`,
theme-color + apple-* meta tags in head, `sw.js` and icons all 200. See `docs/phase_5_3.md`.

---

## Open-Sourcing & Licensing [DONE]
**Completed:** 2026-07-08

- `README.md` — professional public-facing readme: hero + badges, features, Mermaid
  architecture diagram, key-decisions table, tech stack, quickstart, structure, roadmap.
  All numbers real (127 tests, ~2,020 req/s p95 11 ms from the actual `ab` load test).
- `LICENSE` — **AGPL-3.0** (official text via GitHub licenses API).
- `CONTRIBUTING.md` — contributor workflow + code style + **CLA clause** granting the
  maintainer the right to relicense contributions.

**Decision:** AGPL-3.0 over MIT/BUSL — user wants open contributions but no commercial
reuse by third parties, with the option to later form an org/startup and dual-license.
AGPL is contributor-friendly ("true open source") while commercially radioactive to
copycats; the CLA keeps future relicensing possible without chasing past contributors.
Pushed to `main` in commit `b32013b`.

---

## Deliverable — CSE-3644 OBE Project Report [DONE]
- Full industry-style engineering report: **80 pages, 25 figures, 38 tables**, 18 sections +
  6 appendices, mapping PROGNOS onto the OBE/BAETE framework (CLO1–7, PLO2–7, EP1/2/4/6/7,
  Bloom's C4–C6/A4) and covering the whole project past/present/future.
- Generated via `docs/report/build_report.py` (python-docx) + `docs/report/diagrams.py`
  (matplotlib, 25 figures) + `measure_toc.py` (two-pass: static TOC + List of Figures + List of
  Tables, all page numbers verified). Output: `docs/report/PROGNOS_Project_Report.docx` (80 pages)
  + verification PDF. Driven by `docs/report/REPORT_GENERATION_PROMPT.md`.
- All empirical claims are real: **127 tests passing** (pytest), **load test** via real
  `ab -n 2000 -c 20` on a local instance (~2,020 req/s, 0 failed, p95 11 ms). Capacity chapter
  derives user limits with shown arithmetic. No fabricated studies/numbers.
- Honest status framing: Android app = approved **design** (Kotlin/Compose, on-device reminders),
  AI layer = **roadmap**; web platform/tests/deployment stated as delivered. Survey (n=20)
  labelled indicative.
- Human voice verified: 19 em dashes across 14.4k words, zero banned buzzwords. Cover carries the
  official IIUC crest. Team should sanity-check the §3 survey figures before submitting.
  See `docs/phase_report.md`.

---

## Phase 1 — Foundation & Auth

### 1.1 Project Scaffolding [DONE]
**Completed:** 2026-06-19

**What was built:**
- `backend/` — FastAPI skeleton with `GET /api/v1/health` (verified: returns 200 OK)
- `frontend/` — Next.js 16 (TypeScript, App Router, Tailwind CSS)
- `backend/pyproject.toml` — uv-managed, all Phase 1 dependencies installed
- `backend/app/core/config.py` — Pydantic Settings (reads .env)
- `backend/app/core/database.py` — SQLAlchemy async engine + session factory
- `backend/app/core/security.py` — JWT issue/verify, refresh token hashing
- `backend/app/api/v1/__init__.py` — central router registry
- `backend/app/main.py` — FastAPI app factory with CORS
- `backend/alembic/` — migration environment configured (env.py, alembic.ini)
- `backend/Dockerfile` — multi-stage build for Railway
- `railway.toml` — web + worker service definitions
- `backend/.env.example` — all required vars documented
- `.gitignore` — venv, node_modules, .env excluded

**Technical decisions:**
- Python package manager: `uv` (Rust-based, 10-100x faster than pip)
- SQLAlchemy async mode with `asyncpg` driver (non-blocking DB queries)
- Swagger docs disabled in production (`docs_url=None` when `ENVIRONMENT=production`)
- CORS restricted to `FRONTEND_URL` env var (not wildcard `*`)
- Refresh tokens stored as SHA-256 hash in DB (never raw token)
- Access JWT: 15 min expiry | Refresh JWT: 7 days, httpOnly cookie

### 1.2 Database: Auth Tables [DONE]
**Completed:** 2026-06-19

**What was built:**
- `backend/app/models/base.py` — `TimestampMixin` (created_at + updated_at with server_default + onupdate)
- `backend/app/models/user.py` — `User` ORM model (SQLAlchemy 2.0 `Mapped` style)
- `backend/app/models/refresh_token.py` — `RefreshToken` ORM model
- `backend/app/models/__init__.py` — re-exports both models so Alembic autogenerate always sees them
- `backend/alembic/versions/001_create_auth_tables.py` — migration: creates `users` + `refresh_tokens` tables, index on `refresh_tokens.user_id`
- `backend/alembic/env.py` — updated to import `app.models` so metadata is populated

**Technical decisions:**
- Migration written manually (not autogenerated) because local DB credentials in `.env` didn't match; migration verified via `ScriptDirectory.walk_revisions()` — it parses correctly
- `RefreshToken` has no `updated_at` — tokens are write-once; revocation sets `revoked_at` only
- `users → refresh_tokens` FK uses `ON DELETE CASCADE` to avoid orphaned tokens on hard-delete
- `refresh_tokens.user_id` has an explicit index (`idx_refresh_tokens_user_id`) for `logout-all` queries
- `User.refresh_tokens` relationship uses `lazy="noload"` — tokens are never needed eagerly
### 1.3 Google OAuth + JWT Backend [DONE]
**Completed:** 2026-06-20

**What was built:**
- `backend/app/schemas/auth.py` — `TokenResponse` Pydantic schema
- `backend/app/schemas/user.py` — `UserMe` Pydantic schema
- `backend/app/services/auth.py` — all auth business logic (upsert user, create/rotate/revoke tokens)
- `backend/app/api/v1/deps.py` — `get_current_user` FastAPI dependency (Bearer token → User)
- `backend/app/api/v1/routes/auth.py` — 5 auth endpoints
- `backend/app/api/v1/routes/users.py` — `GET /users/me`
- `backend/app/api/v1/__init__.py` — wired auth + users routers

**Endpoints live:**
- `GET  /api/v1/auth/google` — redirect to Google consent
- `GET  /api/v1/auth/google/callback` — exchange code, upsert user, issue tokens
- `POST /api/v1/auth/refresh` — rotate refresh token, return new access JWT
- `POST /api/v1/auth/logout` — revoke current token, clear cookie
- `POST /api/v1/auth/logout-all` — revoke all tokens for user
- `GET  /api/v1/users/me` — return current user profile

**Technical decisions:**
- Google ID token decoded with `python-jose` (no `verify_signature`) — safe because token was received directly from Google's token endpoint over HTTPS
- Access token returned as query param on redirect (`/auth/callback?token=...`) — only way frontend can receive it from a browser redirect
- Refresh cookie scoped to `path=/api/v1/auth` — cookie only sent on auth routes, not every API request
- `get_current_user` dependency checks `is_active=True` — soft-deleted users cannot authenticate
### 1.4 Auth Frontend [DONE]
**Completed:** 2026-06-20

**What was built:**
- `frontend/app/globals.css` — full design token system (Tailwind v4 @theme, dark palette, shimmer skeleton, flame pulse animation)
- `frontend/app/layout.tsx` — root layout with Inter + JetBrains Mono fonts, AuthProvider wrapper
- `frontend/app/_lib/api.ts` — fetch wrapper: attaches Bearer token, auto-refreshes on 401 (deduplicated), retries original request
- `frontend/app/_components/auth-provider.tsx` — React context: token in memory, user profile, session restore on mount via refresh cookie
- `frontend/app/_components/sidebar.tsx` — collapsible sidebar with nav, user avatar, logout button
- `frontend/app/(auth)/login/page.tsx` — full-screen login page, "Continue with Google" button
- `frontend/app/(auth)/callback/page.tsx` — reads ?token= from URL, stores in context, cleans URL, redirects to /dashboard
- `frontend/app/(dashboard)/layout.tsx` — protected layout: checks auth, shows loading spinner, redirects to /login if no token
- `frontend/app/(dashboard)/dashboard/page.tsx` — placeholder dashboard with welcome message
- `frontend/app/page.tsx` — redirects / → /dashboard

**Technical decisions:**
- Token stored in React state (memory), never localStorage — XSS cannot read it
- Session restore on mount via `POST /auth/refresh` with httpOnly cookie — users stay logged in across page refreshes
- `useSearchParams()` wrapped in `<Suspense>` on callback page — required by Next.js 16 for static export
- API client uses deduplication for concurrent 401s — only one refresh call fires even if multiple requests fail simultaneously
- Packages added: `framer-motion`, `lucide-react`
### 1.5 Database: Handle Table [DONE]

**Files created/modified:**
- `backend/app/models/user_handle.py` — `UserHandle` model with `HandlePlatform`, `HandleStatus`, `HandleSyncStatus` enums
- `backend/alembic/versions/002_add_user_handles.py` — migration creating table + 3 PG enum types + 2 indexes
- `backend/app/models/user.py` — added `handles` relationship
- `backend/app/models/__init__.py` — exported `UserHandle`
- `backend/tests/conftest.py` — async DB session + test_user fixture
- `backend/tests/unit/test_user_handle_model.py` — enum values + model instantiation
- `backend/tests/integration/test_user_handle_constraints.py` — partial unique index behavior

**Technical decisions:**
- `UNIQUE(user_id, platform, is_active)` as written in requirement.md would block multiple soft-deleted rows for the same user+platform. Implemented as partial unique index `UNIQUE (user_id, platform) WHERE is_active = true` instead.
- `sa.Enum(..., values_callable=lambda x: [e.value for e in x])` required on all three enum columns to store lowercase values (`.value`) instead of Python enum names (`.name`).
- Enum types created by SA inside `op.create_table()` (not via `op.execute()`); manual `op.execute()` caused double-creation because `env.py` imports `app.models` and SA fired DDL listeners from both paths.
- pytest + pytest-asyncio added as dev dependencies (`uv add --dev`).

### 1.6 Handle Verification Backend [DONE]
**Completed:** 2026-06-22

**Files created/modified:**
- `backend/app/schemas/handle.py` — `HandleInitiateRequest/Response`, `HandleConfirmRequest`, `HandleVerifiedResponse`, `HandleResponse`
- `backend/app/services/handle.py` — `initiate_verification`, `confirm_verification`, `list_handles`, `unlink_handle`, `fetch_cf_user`, `generate_verification_token`
- `backend/app/api/v1/routes/handles.py` — 4 route handlers
- `backend/app/api/v1/__init__.py` — wired handles router
- `backend/tests/unit/test_handle_service.py` — 9 unit tests (respx mocked CF API)
- `backend/tests/integration/test_handle_routes.py` — 6 integration tests (real DB, respx mocked CF API)

**Technical decisions:**
- Token format `PGS-XXXXXX` where X is uppercase hex (6 chars). Hex-only avoids ambiguous characters; `PGS-` prefix is visually distinct in a CF profile.
- Token stored in `user_handles.verification_token`; CF `organization` field used as the writable proof field (updated 2026-06-23 from original `lastName` — see Phase 1.6 Updates). `firstName` and `lastName` kept as silent fallbacks.
- Re-initiate updates the existing unverified row in-place (resets token + attempts); does NOT create a duplicate (partial unique index would reject it anyway).
- Lockout check runs before expiry check — a locked handle is blocked regardless of token expiry state.
- `respx` added as dev dependency for mocking `httpx.AsyncClient` in tests without patching.
- 400 response for token mismatch returns structured `{"message": ..., "attempts_remaining": N}` so frontend can display remaining attempts.

### 1.7 Handle Verification Frontend [DONE]
**Completed:** 2026-06-23

**Files created/modified:**
- `frontend/app/_lib/handles.ts` — typed API client with `ApiError` class carrying `status` + `attemptsRemaining`
- `frontend/app/(dashboard)/handles/page.tsx` — 5-state wizard: `LOADING → NO_HANDLE → PENDING → FAILED → LOCKED → SUCCESS`
- `frontend/app/_components/sidebar.tsx` — Handles nav item enabled
- `backend/app/schemas/handle.py` — `HandleResponse` now includes `is_locked` + `lockout_expires_at` for state restoration
- `backend/app/services/handle.py` — lockout bypass bug fixed: re-initiate blocked during active lockout

**Technical decisions:**
- 3-step stepper (Enter Handle → Copy Token → Verify) collapsed from 5 internal steps — research confirmed users abandon multi-step wizards past 3 visible steps.
- Token display: `font-mono tracking-widest select-none` + one-click copy with `AnimatePresence` icon swap (no toast).
- `useCountdown(target: Date | null)` hook shared between token expiry (PENDING) and lockout timer (LOCKED).
- LOCKED state uses `warning-400` (amber) not `danger-400` (red) — lockout is a temporary queue, not an error state.
- Success copy: "Handle verified." (period not exclamation mark) — confident finality, not marketing enthusiasm.
- State restoration on page reload: `GET /handles` response drives `LOCKED` restore via `lockout_expires_at`; PENDING restores as `NO_HANDLE` (re-initiate gives fresh token, no harm).

### 1.8 User Account Management [DONE]
**Completed:** 2026-06-24

**Files created/modified:**
- `backend/app/schemas/user.py` — added `UserUpdateRequest` schema (`name` field, 1-255 chars)
- `backend/app/services/auth.py` — added `update_user_name`, `soft_delete_user`; fixed `upsert_user` to re-select with `populate_existing=True` after commit
- `backend/app/api/v1/routes/users.py` — added `PATCH /users/me`, `DELETE /users/me`
- `backend/tests/integration/test_auth_service.py` — 11 new integration tests (upsert, session lifecycle, token revocation, update name, soft delete)

**Endpoints added:**
- `PATCH /api/v1/users/me` — updates display name; returns updated `UserMe`
- `DELETE /api/v1/users/me` — soft-deletes account: `is_active=false`, PII anonymized (email/google_id/name/avatar replaced), all refresh tokens revoked, refresh cookie cleared

**Technical decisions:**
- PII anonymization: `email → deleted_{sha256[:16]}@deleted.invalid`, `google_id → deleted_{sha256}`. SHA-256 of the user_id preserves uniqueness constraint while removing original values.
- Teacher classroom check (`→ 409 Conflict`) deferred to Phase 4 when classrooms are built — stub comment left in route handler.
- `upsert_user` changed from `returning(User)` to `returning(User.id)` + fresh `select(populate_existing=True)` to avoid SQLAlchemy identity map returning stale data when the same session has a pre-existing cached object.
- Service integration tests added for: `upsert_user` (create + conflict update), `create_session`, `rotate_refresh_token` (happy path + rejection), `revoke_token`, `revoke_all_tokens`, `update_user_name`, `soft_delete_user`.

**Spec alignment fixes (audit findings):**
- Token prefix updated in `requirement.md` and `implementation.md` from `CS-` → `PGS-` to match the actual implementation decision documented in Phase 1.6.

---

## Phase 2 — Personal Analytics Engine [IN_PROGRESS]

### 2.1 Celery + CF Sync Worker [DONE]
**Completed:** 2026-06-24

**Files created/modified:**
- `backend/app/models/analytics.py` — `Submission`, `SubmissionTag`, `DailyActivity`, `TagStats`, `RatingHistory`
- `backend/app/models/signals.py` — `WeaknessSignal`, `RecommendationSet`, `Recommendation`
- `backend/app/models/__init__.py` — exports all new models
- `backend/alembic/versions/003_add_analytics_tables.py` — 8 tables + `weakness_signal_type` enum
- `backend/app/workers/celery_app.py` — Celery instance + beat schedule (sync all handles every 6h)
- `backend/app/workers/cf_sync.py` — full sync pipeline: fetch → daily_activity → tag_stats → rating_history → weakness_signals → recommendations
- `backend/app/schemas/handle.py` — `SyncResponse` schema added
- `backend/app/services/handle.py` — `get_handle_for_user` helper added
- `backend/app/api/v1/routes/handles.py` — `POST /handles/{id}/sync` manual sync endpoint
- `backend/tests/unit/test_weakness_signals.py` — 5 unit tests (neglected/low_success/under_practiced rules)
- `backend/tests/integration/test_sync_endpoint.py` — 7 integration tests (cooldown logic, 403/404 ownership)
- `docs/phase_2_1.md` — phase documentation

**Technical decisions:**
- Incremental sync uses `max(cf_submission_id)` as cursor — integer IDs are unambiguous vs. timestamp-based.
- `daily_activity` and `tag_stats` are fully recomputed on each sync (DELETE + reinsert) — handles CF verdict changes; keeps logic simple.
- CF problemset cached in Redis (`cf:problemset:all`, 6h TTL) — avoids per-sync API call for recommendations.
- Manual sync timestamp committed before task dispatch to block concurrent duplicate requests.
- Weakness signals use mutually exclusive `if/elif/elif`: neglected > low_success > under_practiced.
- All 42 tests passing.

### 2.2 Analytics API [DONE]
**Completed:** 2026-06-25

**Files created/modified:**
- `backend/app/schemas/analytics.py` — `HeatmapDay`, `DashboardResponse`, `TagStatsResponse`, `RatingHistoryResponse`
- `backend/app/services/analytics.py` — `get_dashboard`, `get_tag_stats`, `get_rating_history` + `_compute_streaks`
- `backend/app/api/v1/routes/analytics.py` — 3 GET route handlers
- `backend/app/api/v1/__init__.py` — analytics router wired in
- `backend/tests/integration/test_analytics_routes.py` — 16 tests (streak unit + dashboard/tags/rating integration)
- `docs/phase_2_2.md` — phase documentation

**Endpoints added:**
- `GET /api/v1/analytics/dashboard` — heatmap (365 days, non-zero days only), current_streak, longest_streak, total_solved (all-time), cf_rating
- `GET /api/v1/analytics/tags` — tag_stats sorted by solved_count DESC
- `GET /api/v1/analytics/rating-history` — rating_history sorted by contest_time ASC

**Technical decisions:**
- Streaks computed at read time from `daily_activity` (≤1825 rows for 5 years) — no denormalized column needed; value is always accurate.
- Grace-day logic: if today has 0 solved, streak counts from yesterday (requirement §D.2). Previous "no grace-day" decision reversed in Phase 2 QA audit.
- Heatmap scoped to 365 days; total_solved and streaks are all-time — different scopes are intentional.
- `cf_rating` derived from `rating_history.new_rating ORDER BY contest_time DESC LIMIT 1` — same source as sync worker.
- No handle → graceful empty/zero response (not 404).
- All 58 tests passing.
### 2.3 Weakness + Recommendations Engine [DONE]
**Completed:** 2026-06-25

**Files created/modified:**
- `backend/app/schemas/analytics.py` — added `WeaknessSignalResponse`, `RecommendationResponse`, `RecommendationSetResponse`
- `backend/app/services/analytics.py` — added `get_weaknesses`, `get_recommendations`
- `backend/app/api/v1/routes/analytics.py` — 2 new GET route handlers
- `backend/tests/integration/test_weaknesses_recommendations.py` — 8 integration tests
- `docs/phase_2_3.md` — phase documentation

**Endpoints added:**
- `GET /api/v1/analytics/weaknesses` — weakness_signals for user's handles, sorted by score DESC; `[]` when no handle or no signals
- `GET /api/v1/analytics/recommendations` — most recent recommendation_set with nested recommendations sorted by position; `null` when no set exists

**Technical decisions:**
- WeaknessSignal queried via handle_ids (per-handle granularity); RecommendationSet queried directly by user_id (user-level granularity) — mirrors the schema design from Phase 2.1.
- `/recommendations` returns `null` (not `[]`) for no-data: communicates "sync hasn't run yet" vs. "exists but empty".
- `recommendations` child list loaded via `selectin` (ORM relationship), sorted in-memory by `position` — avoids modifying relationship declaration just for ordering.
- All 66 tests passing.
### 2.4 Dashboard UI [DONE]
**Completed:** 2026-06-23

**Files created/modified:**
- `frontend/app/_lib/analytics.ts` — types + 5 typed fetch functions for all analytics endpoints
- `frontend/app/(dashboard)/dashboard/page.tsx` — orchestrator: parallel fetches, independent loading states, no-handle detection
- `frontend/app/(dashboard)/dashboard/_components/stat-strip.tsx` — 4 stat cards; CF rating in Codeforces color ladder; `.animate-flame` on current streak
- `frontend/app/(dashboard)/dashboard/_components/activity-heatmap.tsx` — 52×7 GitHub-style heatmap; 5-level intensity scale; hover tooltip
- `frontend/app/(dashboard)/dashboard/_components/rating-chart.tsx` — Recharts LineChart; Y-axis clamped to [min−50, max+50]; custom tooltip with contest name + delta + rank
- `frontend/app/(dashboard)/dashboard/_components/tag-stats.tsx` — horizontal bar list; top 15 tags; relative bar width vs. max solved_count
- `frontend/app/(dashboard)/dashboard/_components/weakness-cards.tsx` — per-signal cards; color-coded by type (danger/warning/accent); API score-DESC ordering preserved
- `frontend/app/(dashboard)/dashboard/_components/recommendations.tsx` — problem list; difficulty badge in CF color ladder; null state ("Sync hasn't run yet.") with CTA to /handles
- `docs/phase_2_4.md` — phase documentation

**Technical decisions:**
- 5 independent `useState` variables (not a single `Promise.all`) so each section loads independently — stat cards appear before the slow recommendations endpoint resolves.
- `undefined | null | T` sentinel pattern: `undefined` = loading, `null` = loaded-but-empty, `T` = has data. Eliminates companion `isLoading` booleans.
- No-handle detection: reads `has_verified_handle` field from `DashboardResponse` directly (updated in QA audit — old proxy heuristic false-positived for verified users with all-WA submissions).
- Heatmap cell: `w-3.5 h-3.5` (14px) + `gap-[3px]` → 52×17−3 = 881px + 32px labels = 913px, fits 992px usable width at 1280px viewport.
- Rating chart Y-axis: manual `domain={[min−50, max+50]}` — avoids Recharts auto-scale producing unintuitive non-round tick values.
- CF color ladder intentionally duplicated in stat-strip + recommendations (2 call sites) rather than extracted — no premature util abstraction.
- `recharts ^3.8.1` added as a dependency.
- All TypeScript clean (0 errors); production build passes.

### 2.5 Phase 2 QA Audit [DONE]
**Completed:** 2026-06-23

Full audit of Phase 2 against `requirement.md` and `implementation.md`. All issues found and resolved in one session.

**Fixes applied:**

| Severity | Item | Fix |
|---|---|---|
| Critical | Streak grace-day missing | `_compute_streaks()` starts from yesterday when today has 0 solved |
| High | `POST /analytics/recommendations/refresh` not built | Implemented in `services/analytics.py` + route |
| High | `noHandleLinked()` false-positive (all-WA users) | `has_verified_handle: bool` added to `DashboardResponse` |
| Medium | Heatmap tooltip said "submissions", value is `solved_count` | Label changed to "solved" |
| Medium | `rating_history` missing unique constraint | Migration 004: `UNIQUE(user_handle_id, cf_contest_id)` |
| Medium | `weakness_signals` missing unique constraint | Migration 004: `UNIQUE(user_handle_id, tag, signal_type)` |
| Medium | `on_conflict_do_nothing()` had no `index_elements` | Added `index_elements=["user_handle_id", "cf_contest_id"]` |
| Low | Difficulty band not clamped to [800, 3500] | `max(800, low)` / `min(3500, high)` in `_pick_problem()` |

**Handle verification fixes (same session):**
- Verification field: `lastName` → `organization` (users don't want their name overwritten)
- Frontend URL corrected: `settings/general` → `settings/social`
- Token expiry extended: 30 min → 60 min
- Comparison uses `.strip()` to handle CF whitespace edge cases

**Files changed:** 9 backend files, 4 frontend files, 1 new migration (004)
**Test count:** 67 passed (was 66)
**Run script:** `run.sh` added at repo root — kills ports 8000/3000, starts both servers, single Ctrl+C stops both.

### 2.6 Dev Sync Fix & First-Sync UX [DONE]
**Completed:** 2026-06-23

**Root cause diagnosed:** Dashboard was always empty because the CF sync pipeline (Celery + Redis) is not started by `run.sh`. No sync had ever run, so all analytics tables (`daily_activity`, `tag_stats`, `rating_history`) were empty.

**Files created/modified:**
- `backend/app/workers/cf_sync.py` — `_get_cf_problemset()` degrades gracefully when Redis is unavailable (try/except on both read+write); `time.sleep(2)` → `await asyncio.sleep(2)` (blocking sleep freezes the FastAPI event loop when sync runs as a BackgroundTask)
- `backend/app/api/v1/routes/handles.py` — `_enqueue_sync()` helper: tries Celery first, falls back to `FastAPI BackgroundTasks`; `confirm` endpoint now auto-triggers sync after verification; manual sync endpoint uses same helper
- `backend/app/schemas/analytics.py` — `is_syncing: bool` added to `DashboardResponse`
- `backend/app/services/analytics.py` — `get_dashboard()` sets `is_syncing=True` when `sync_status=IN_PROGRESS` or `last_synced_at IS NULL`
- `frontend/app/(dashboard)/dashboard/page.tsx` — polls every 5s while `is_syncing=true`; spinner banner shown during sync; auto-reloads all sections when sync completes
- `frontend/app/(dashboard)/handles/page.tsx` — SUCCESS state now includes `handleId`; "Go to Dashboard" (broken CF profile link) replaced with "Sync & Go to Dashboard" button; `syncHandle()` called before navigation
- `frontend/app/_lib/analytics.ts` — `is_syncing: boolean` added to `DashboardData`
- `frontend/app/_lib/handles.ts` — `syncHandle()` function added
- `backend/tests/integration/test_handle_routes.py` — mock updated: `lastName` → `organization` (latent mismatch from Phase 2.5 QA audit)
- `backend/tests/unit/test_handle_service.py` — same mock fix
- `docs/phase_2_6.md` — full phase documentation

**Technical decisions:**
- BackgroundTask fallback is dev-only by intent — Celery provides retries + monitoring in production; BackgroundTask provides none of those guarantees.
- `socket_connect_timeout=2` on Redis client caps "Redis not running" failure at 2s instead of OS default (~30s).
- `is_syncing=True` when `last_synced_at IS NULL` catches the window between "BackgroundTask enqueued" and "sync sets status to IN_PROGRESS".
- `syncHandle()` treats HTTP 429 (cooldown) as success — cooldown means a sync is running or just ran, which is the desired outcome.
- All 67 tests passing.

### 2.7 Dashboard Polish & Data Audit [DONE]
**Completed:** 2026-06-25

**Files changed:**
- `frontend/app/(dashboard)/dashboard/page.tsx` — 70/30 grid split (`cols-10`), `max-w-[1400px] mx-auto`, `items-start` on bottom row, `peakRating` from `ratingHistory`, `handleRefresh` callback, `recTags` wired to `WeaknessCards`
- `frontend/app/(dashboard)/dashboard/_components/rating-chart.tsx` — sequential numeric XAxis index (all points hover-reachable); 4-layer overflow chain (`overflow-visible` on wrapper + recharts-responsive-container + recharts-wrapper + recharts-surface); peak reference line label moved to `insideTopLeft`; visible dots added
- `frontend/app/(dashboard)/dashboard/_components/activity-heatmap.tsx` — complete rewrite; GitHub span≥3 month label rule; absolute-positioned month labels; legend moved to header; grid centered with `flex justify-center`
- `frontend/app/(dashboard)/dashboard/_components/stat-strip.tsx` — peak rating badge inline on rating line (3-line card preserved); badge only shows when peak ≠ current
- `frontend/app/(dashboard)/dashboard/_components/tag-stats.tsx` — acceptance rate label "% accepted" → "% solved" (metric is problem-level success rate, not submission-level); scrollbar padding `pr-1` → `pr-3`
- `frontend/app/(dashboard)/dashboard/_components/weakness-cards.tsx` — renamed "Weaknesses" → "Focus Areas"; urgency dots → priority dots (High/Med/Low Priority); "X problems selected" rec-count hint
- `frontend/app/(dashboard)/dashboard/_components/recommendations.tsx` — Refresh button with spinning icon + `isRefreshing` disabled state; position badges (gold/silver/bronze) restored
- `backend/app/services/analytics.py` — `_compute_streaks` parameter renamed `date_to_solved` → `date_to_submissions` for clarity
- `backend/app/workers/cf_sync.py` — `_pick_problem()` collects all candidates then `random.choice()` — fixes Refresh returning the same problem every time
- `docs/phase_2_7.md` — phase documentation

**Data audit findings (all verified):**
- `total_solved`: `COUNT(DISTINCT problem_id WHERE verdict='OK')` ✓ correctly deduplicates
- `cf_rating`: most recent `new_rating` ✓
- `peak_rating`: `Math.max(all new_ratings)` ✓
- Streak: any-submission days with grace day ✓
- Rating history upsert: unique constraint exists (migration 004) ✓
- Heatmap, tag stats, weaknesses, recommendations: all logically correct ✓

**Test count:** 67 passed (unchanged — no new endpoints)

---

## Phase 3 — Contest Discovery [DONE]

### 3.1 CLIST Sync Worker + DB [DONE]
**Completed:** 2026-06-25

**Files created/modified:**
- `backend/app/models/analytics.py` — `Contest` ORM model added (`TimestampMixin`, `clist_id` BIGINT UNIQUE)
- `backend/app/models/__init__.py` — `Contest` exported
- `backend/alembic/versions/005_add_contests_table.py` — migration: `contests` table + `uq_contests_clist_id` + `idx_contests_start_time`
- `backend/app/workers/clist_sync.py` — NEW: `sync_clist_contests` Celery task; `_run_sync`, `_fetch_contests`, `_map_contest` helpers
- `backend/app/workers/celery_app.py` — `clist_sync` module included; beat entry: every 4h
- `backend/app/core/config.py` — `CLIST_USERNAME`, `CLIST_API_KEY` added (default empty strings)
- `backend/.env.example` — CLIST vars documented
- `backend/tests/unit/test_clist_sync.py` — 8 unit tests
- `backend/tests/integration/test_clist_sync_integration.py` — 3 integration tests (insert, upsert-on-conflict, created_at preservation)
- `docs/phase_3_1.md` — phase documentation

**Technical decisions:**
- Separate `clist_sync.py` from `cf_sync.py`: global vs per-user concern; different beat schedules (4h vs 6h).
- Upsert key is `clist_id` (CLIST's stable integer), not UUID PK — keeps our UUID stable even when contest metadata changes.
- `created_at` excluded from `ON CONFLICT DO UPDATE SET` — preserves original insertion time across unlimited refreshes.
- Async pattern (`asyncio.run` + `asyncpg`) — avoids adding `psycopg2` as a second driver; consistent with `cf_sync.py`.
- Graceful degradation at `_fetch_contests` level (not just Celery retry) — makes the "no DB write on API error" path unit-testable.
- `CLIST_USERNAME` and `CLIST_API_KEY` default to empty strings so the app boots without them; sync will simply fail gracefully until credentials are added.

**Test count:** 78 passed (was 67)

---

### 3.2 Contest API [DONE]
**Completed:** 2026-06-24

**Files created/modified:**
- `backend/app/schemas/contests.py` — NEW: `ContestItem`, `ContestsListResponse`, `CalendarDay`, `ContestsCalendarResponse`
- `backend/app/services/contests.py` — NEW: `get_contests`, `get_contests_calendar`, `get_platforms`, `_is_stale` helper
- `backend/app/api/v1/routes/contests.py` — NEW: 3 route handlers (`GET /contests`, `GET /contests/calendar`, `GET /contests/platforms`)
- `backend/app/api/v1/__init__.py` — `contests_router` included
- `backend/tests/unit/test_contests_service.py` — 8 unit tests (_is_stale thresholds, calendar grouping, platforms)
- `backend/tests/integration/test_contests_routes.py` — 8 integration tests (list, filter, pagination, sort, calendar, platforms)
- `docs/phase_3_2.md` — phase documentation

**Technical decisions:**
- All 3 endpoints require `get_current_user` for consistency (contest page is inside the app shell; no reason for a public route exception).
- Stale detection: `MAX(last_synced_at) > 8h ago` — two missed 4h sync cycles. Returned as `is_stale: bool` in response body so frontend can show amber banner.
- Calendar grouping done in Python (not SQL) — keeps DB query simple; timezone conversion is a presentation concern for the frontend.
- `total` included in list response (for pagination display) but not in calendar response (all-at-once rendering).
- Route order: `/calendar` and `/platforms` before any future `/{id}` param route to prevent FastAPI path-capture collision.

**Test count:** 94 passed (was 78)

### 3.2 Post-Review Fixes [DONE]
**Completed:** 2026-06-24

Four bugs found and fixed during a line-by-line audit of Phase 3 code before Phase 3.3 started.

| Bug | Fix |
|---|---|
| Pagination tiebreaker missing — `ORDER BY start_time` is non-deterministic on ties; `offset` pages could skip/duplicate rows when contests share a start time | Added `clist_id ASC` as secondary sort key in `get_contests` and `get_contests_calendar` |
| Live contests disappeared at `start_time` — filter `start_time >= now` ejected a running contest the instant it began | Changed lower bound to `end_time > from_dt`; confirmed by user: running contests should stay visible until they end |
| `get_platforms` returned all-time platforms (including past/expired contests) — clicking a stale chip yields an empty list | Scoped query to `end_time > now AND start_time <= now+30d` to match the default list window |
| Naive datetime query params — FastAPI parses `?from_dt=2026-07-01T00:00:00` (no tz suffix) as a naive datetime; asyncpg comparison against TIMESTAMPTZ is implicit | Added `_ensure_utc()` helper that attaches UTC tzinfo to any incoming naive datetime before it hits the query |

New test: `test_get_contests_pagination_stable_with_tied_start_times` — 4 contests with identical start times, verifies page1 ∪ page2 = all 4 with no overlaps.

**Test count:** 95 passed (was 94)

---

### 3.3 Contest UI [DONE]
**Completed:** 2026-06-24

**Files created/modified:**
- `frontend/app/_lib/contests.ts` — NEW: `ContestItem`, `ContestsListResponse`, `fetchContests`, `fetchContestPlatforms`, platform color/abbr/display helpers, time formatting utilities, `groupContestsByLocalDate`, `getLocalWeekDays`, `getWeekBoundsISO`, `getNextContest`
- `frontend/app/(dashboard)/contests/page.tsx` — NEW: orchestrator; manages filter, view, week state; cancellable fetch effect; modal state
- `frontend/app/(dashboard)/contests/_components/platform-badge.tsx` — NEW: colored abbreviation badge per platform
- `frontend/app/(dashboard)/contests/_components/countdown-display.tsx` — NEW: `useCountdown` hook + `CountdownDisplay` (card) + `HeroCountdown` (hero); escalating urgency format/color
- `frontend/app/(dashboard)/contests/_components/stale-data-banner.tsx` — NEW: amber strip when `is_stale=true`
- `frontend/app/(dashboard)/contests/_components/contest-card.tsx` — NEW: contest row with left-border urgency states; skeleton variant
- `frontend/app/(dashboard)/contests/_components/contest-list-view.tsx` — NEW: date-grouped list; empty state; skeleton variant
- `frontend/app/(dashboard)/contests/_components/contest-detail-modal.tsx` — NEW: framer-motion animated modal; Escape key + backdrop dismiss
- `frontend/app/(dashboard)/contests/_components/contest-calendar-view.tsx` — NEW: 7-column week grid; Mon–Sun in local TZ; inline "+N more" expansion; day cell skeletons
- `frontend/app/(dashboard)/contests/_components/platform-filter-chips.tsx` — NEW: multi-select chips; "All" auto-restores when all deselected; platform color active state
- `frontend/app/(dashboard)/contests/_components/next-contest-hero.tsx` — NEW: next/live contest strip with HeroCountdown; platform-colored CTA; skeleton variant
- `frontend/app/_components/sidebar.tsx` — MODIFIED: Contests nav item enabled (`disabled` removed)
- `docs/phase_3_3.md` — NEW: full phase documentation

**Technical decisions:**
- Single list endpoint for both views; calendar groups client-side by local date (avoids UTC/local mismatch from server-side grouping).
- Countdown precision escalates: >1d → `Xd Yh`; <24h → `HH:MM:SS` cyan; <1h → `HH:MM:SS` red (pulse); live → LIVE badge + remaining time.
- `tabular-nums` on all countdown spans prevents digit-column jitter.
- `HeroSegment`/`HeroSep` defined at module level (not inside render) to satisfy `react-hooks/static-components`.
- Cancellation flag in fetch effect prevents stale responses from overwriting fresh data on rapid filter changes.
- Platform colors: `hex/22` tint background + `hex` text — works on dark backgrounds without white card.
- TypeScript build clean; ESLint clean on all new files.

**Test count:** 95 (frontend has no automated test framework; verification is TypeScript build + ESLint + manual browser check)

---

### 3 QA Audit [DONE]
**Completed:** 2026-06-25

Full audit of all Phase 3 code (backend + frontend). Four bugs found and fixed.

| # | Severity | Bug | Fix |
|---|---|---|---|
| 1 | Critical | Multi-platform filter silently broken — `platform: str \| None` in route accepted only one value; frontend sends `?platform=a&platform=b` for multi-select | Changed to `list[str] \| None = Query(default=None)` in both list and calendar routes; service now uses `Contest.platform.in_(platform)` |
| 2 | Correctness | Multi-day contest end time shows no date — `"Sat Jul 12 · 17:35 – 02:00"` looks same-day even for a 33h contest | Added `formatLocalEndLabel(start, end)` to `_lib/contests.ts`: same-day → time only; different day → `"Sun, Jul 13 · 02:00"`. Applied in card, hero strip, and modal |
| 3 | UX | `CalendarDayCell` expanded state persisted across platform filter changes — "+N more" stays open even after filter produces fewer contests | Added `useEffect(() => { setExpanded(false); }, [contests])` in `CalendarDayCell` |
| 4 | Performance | Escape key listener registered even when modal is closed — inline `onClose` arrow changed identity on every parent render, causing listener re-registration | Added `if (!contest) return` guard at effect top; added `contest` to deps so listener only lives while modal is open |

**Test additions:**
- `test_get_contests_filters_by_multiple_platforms` — new integration test verifying `platform=["cf","ac"]` returns contests from both platforms
- `test_get_platforms_returns_distinct_sorted` — rewritten with relative `now + N days` offsets (was hardcoded Jul 2026 dates, would have expired Jul 4 2026)
- All existing tests updated: single-platform calls changed from `platform="x"` → `platform=["x"]` to match new `list[str]` signature

**Test count:** 96 passed (was 95)

### 3.4 UI/UX Overhaul [DONE]
**Completed:** 2026-06-27

**Files modified:** `globals.css`, `sidebar.tsx`, `stat-strip.tsx`, `activity-heatmap.tsx`, `rating-chart.tsx`, `tag-stats.tsx`, `next-contest-hero.tsx`, `contest-card.tsx`, `platform-filter-chips.tsx`, `stale-data-banner.tsx`, `contest-calendar-view.tsx`

**What changed:**
- Design tokens: desaturated navy → neutral-dark (`#09090C` base); borders switched to `rgba(255,255,255,0.06/0.10)` semi-transparent overlay
- Sidebar: section labels ("Analytics" / "Tools"); neutral white active state; darker sidebar bg (`#0D0D12`)
- Stat cards: tight `tracking-[-0.02em] tabular-nums` on values; sparkline SVG on Total Solved card; amber left-border when streak is active
- Heatmap: vibrant indigo palette (5-level); hover scale+ring; today cell ring; staggered column entrance animation; glassmorphism tooltip
- Rating chart: switched `LineChart` → `AreaChart` with indigo gradient fill; mean rating reference line; grid at `rgba(255,255,255,0.05)`
- Tag stats: gradient bar fills; neutral `rgba(255,255,255,0.04)` track
- Contest hero: live green gradient tint; "Open Contest" CTA when live
- Contest cards: `border-l-2`; ended link fades until hover
- Filter chips: `ring-inset` box-shadow active state
- Stale banner: slimmer, pulsing dot
- Calendar: today as dot indicator below day number

**Test count:** 96 passed (no backend changes)

### 3.5 Contest Page Redesign — Direction B [DONE]
**Completed:** 2026-06-25

**Files modified:**
- `frontend/app/_lib/contests.ts` — `UrgencyLane`, `ContestLane`, `groupContestsByUrgency`, `formatLocalDateShort`
- `frontend/app/(dashboard)/contests/_components/countdown-display.tsx` — `isEndingSoon` added to hook
- `frontend/app/(dashboard)/contests/_components/next-contest-hero.tsx` — split-panel layout + SVG arc progress ring
- `frontend/app/(dashboard)/contests/_components/contest-card.tsx` — status-based tint, badge pill, typographic weight
- `frontend/app/(dashboard)/contests/_components/contest-list-view.tsx` — urgency swim lanes (LIVE/TODAY/THIS WEEK/NEXT WEEK/LATER)
- `frontend/app/(dashboard)/contests/_components/contest-calendar-view.tsx` — 15% opacity pills, live outline, past-day dimming
- `docs/phase_3_5.md` — phase documentation

**Root-cause fixes:**
- Status information now expressed at 4 levels simultaneously: background tint + left border + badge shape + countdown color
- Hero has visual mass (split panel, `text-2xl` name, platform gradient tint, SVG arc ring)
- List groups by urgency (LIVE first) not calendar date
- Calendar pills legible on dark background (15% vs 7% opacity)

**TypeScript build:** Clean (0 errors, 0 ESLint errors)

---

## Phase 4 — Classroom System [DONE]

### 4.1 Database Migration [DONE]
**Completed:** 2026-06-29

**Files created/modified:**
- `backend/alembic/versions/006_add_classroom_tables.py` — 4 tables + `classroom_membership_role` PG enum; CASCADE + SET NULL FKs
- `backend/app/models/classroom.py` — SQLAlchemy 2.0 models: `Classroom`, `ClassroomInvite`, `ClassroomMembership`, `ClassroomLeaderboard`
- `backend/app/models/__init__.py` — exports 4 new models

**Technical decisions:**
- JSONB for `top_tags` / `weak_tags` on leaderboard — cache rebuilt hourly; UPSERT single row per user vs. child-table churn
- `classroom_memberships.invite_id` ON DELETE SET NULL — preserve membership audit trail when invite is removed
- `classroom_leaderboard.user_id` ON DELETE CASCADE — cache row is a projection; vanishes when user is deleted
- `values_callable=lambda x: [e.value for e in x]` on enum — required to match DB values to Python strings

### 4.2 Backend CRUD [DONE]
**Completed:** 2026-06-29

**Files created/modified:**
- `backend/app/schemas/classroom.py` — all Pydantic schemas (request + response)
- `backend/app/services/classroom.py` — 12 service functions (create, join, leave, delete, invites, members, leaderboard, cohort)
- `backend/app/api/v1/routes/classrooms.py` — 14 REST endpoints
- `backend/app/api/v1/__init__.py` — classrooms_router registered
- `backend/app/services/auth.py` — account-deletion guard (409 if user owns active classrooms)
- `backend/tests/integration/test_classroom_routes.py` — 30 integration tests

**Technical decisions:**
- Route ordering: `/classrooms/join` and `/classrooms/join-preview/{token}` registered before `/{classroom_id}` (prevents FastAPI treating "join" as UUID)
- `join-preview` endpoint is public (no `get_current_user` dep) — needed by unauthenticated join landing page
- Join flow uses 410 Gone (not 403) for expired/revoked invites
- `my_role` derived per-requesting-user in `ClassroomResponse` — self-contained, no second query from client

**Test count:** 126 passed

### 4.3 Leaderboard Worker + Cohort Analytics [DONE]
**Completed:** 2026-06-29

**Files created/modified:**
- `backend/app/workers/classroom_sync.py` — `rebuild_classroom_leaderboard` (Celery task) + `rebuild_all_classroom_leaderboards` (beat)
- `backend/app/workers/celery_app.py` — classroom_sync included; beat entry every hour
- `backend/app/workers/cf_sync.py` — Step 6: trigger per-classroom leaderboard rebuild after CF sync
- `backend/app/services/classroom.py` — `get_cohort_analytics()` reads JSONB, aggregates via Python Counter

**Technical decisions:**
- `asyncio.run()` per Celery task — isolated event loop; no shared state between tasks
- Partial failure: `_build_leaderboard_row()` returns None on missing handle → old row preserved, rebuild continues
- Stale member pruning: `DELETE WHERE user_id NOT IN ($current_member_ids)` after rebuild
- `from app.workers.classroom_sync import ...` inside helper function — breaks circular import
- Cohort analytics reads only `classroom_leaderboard` table; JSONB aggregated in Python (simpler than SQL `jsonb_array_elements`)

### 4.4 Frontend [DONE]
**Completed:** 2026-06-29

**Files created/modified:**
- `frontend/app/_lib/classrooms.ts` — 14 API functions + types + utilities
- `frontend/app/(dashboard)/classrooms/page.tsx` — classroom list + empty state
- `frontend/app/(dashboard)/classrooms/create/page.tsx` — single-field create form
- `frontend/app/(dashboard)/classrooms/[id]/page.tsx` — orchestrator: tabs, parallel fetches, delete/leave
- `frontend/app/(dashboard)/classrooms/[id]/_components/leaderboard-table.tsx` — 7-column table + shimmer
- `frontend/app/(dashboard)/classrooms/[id]/_components/invite-panel.tsx` — teacher invite management
- `frontend/app/(dashboard)/classrooms/[id]/_components/cohort-analytics.tsx` — attendance bars + tag lists
- `frontend/app/(dashboard)/classrooms/[id]/_components/member-management.tsx` — inline remove confirm
- `frontend/app/join/[token]/page.tsx` — 7-state discriminated union; public landing
- `frontend/app/_components/sidebar.tsx` — Classroom nav enabled; disabled branch removed
- `frontend/app/(auth)/callback/page.tsx` — `pending_join` localStorage redirect after OAuth

**Technical decisions:**
- `undefined | null | T` sentinel for all async data — eliminates boolean `isLoading` pairs
- Teacher-only data (cohort, invites) fetched in dedicated `useEffect` gated on `isTeacher` — no wasted requests for students
- `pending_join` uses localStorage (not auth storage) — invite token is not a secret; survives OAuth redirect loop
- `fetchJoinPreview` uses raw `fetch` (not `apiFetch`) — public endpoint; no auth header injection
- Inline two-step confirm (not modal) for destructive actions — sufficient for simple yes/no without additional input

**Build:** `npm run build` — 0 TypeScript errors, 0 ESLint errors, 11 routes

### 4.5 Phase 4 QA Audit [DONE]
**Completed:** 2026-06-30

Full code review + subagent audit of all Phase 4 classroom code. 5 real bugs found and fixed.

| Severity | Bug | Fix |
|---|---|---|
| HIGH | `join_classroom` race condition — concurrent double-join raised unhandled 500 | Catch `IntegrityError`, rollback, return 409 |
| HIGH | `soft_delete_user` left student memberships + leaderboard rows alive — PII persisted on classroom | Added `DELETE ClassroomMembership` + `DELETE ClassroomLeaderboard` for user |
| MEDIUM | `cohort_analytics.member_count = len(entries)` — counted cache rows, not actual members | Replaced with `await _member_count(db, classroom_id)` |
| MEDIUM | Join page `useEffect` missing `user` in deps — session-restore race stranded page on "unauthenticated" | Added `user` to dependency array |
| LOW | `already_member` state had dead `classroomId: ""` field — never used, misleading type | Removed field from discriminated union type |

Also added missing test: `test_join_classroom_expired_invite_raises_410`.

**Test count:** 127 passed (was 126)

## Phase 5.0 — Marketing Landing Page [DONE]
**Completed:** 2026-07-01

**Files created/modified:**
- `frontend/app/page.tsx` — REWRITTEN: full 11-section landing page (was `redirect("/dashboard")`)
- `frontend/app/_components/landing-navbar.tsx` — NEW: sticky navbar, scroll-triggered backdrop-blur, auth-aware CTA (Log In + Sign Up vs. Dashboard)
- `frontend/app/_components/handle-preview-widget.tsx` — NEW: live CF API handle lookup, 4-state UX (empty/loading/success/error), rating-color-coded profile card
- `frontend/app/(auth)/login/page.tsx` — UPDATED: "← Back to home" link added

**Technical decisions:**
- CF API called directly from browser (CORS verified: `access-control-allow-origin: *`); no backend proxy needed
- `PHONE_HEATMAP` fixed constant array (35 values) replaces `Math.random()` to prevent SSR/client hydration mismatch
- All JSX text uses HTML entities (`&apos;`, `&ldquo;`, etc.) + no contractions to satisfy `react/no-unescaped-entities`
- `eslint-disable-next-line @next/next/no-img-element` scoped to CF avatar `<img>` — subdomain varies per user, cannot be pre-registered in next.config.ts
- Mobile section placed before AI section — mobile app is a primary shippable product
- Social proof section uses placeholder stats and testimonials — must be replaced with real data before external launch (see docs/phase_5_0.md)

**Build:** `npm run build` — 0 TypeScript errors, 0 ESLint errors, `/` is `○ (Static)` prerendered

## Phase 5.1 — Insights Page [DONE]
**Completed:** 2026-06-29

**Files created/modified:**
- `frontend/app/(dashboard)/insights/page.tsx` — NEW: orchestrator with 4 parallel fetches (dashboard flags, tags, weaknesses, recs), polling while syncing, NoHandleNudge fallback
- `frontend/app/(dashboard)/dashboard/page.tsx` — SIMPLIFIED: removed tags/weakness/recs; rating chart now full-width
- `frontend/app/_components/sidebar.tsx` — UPDATED: Insights nav item (Lightbulb icon) added between Dashboard and Contests

**Technical decisions:**
- All three components (tag-stats, weakness-cards, recommendations) reused as-is — no component rewrites
- Cross-directory imports: `insights/page.tsx` imports from `../dashboard/_components/` — valid relative path within same route group
- `Lightbulb` icon chosen over `Brain`/`Sparkles` — doesn't imply AI is already live; can swap to `Brain` when Phase 6 ships
- Polling loop duplicated on Insights page — users may be on this page when sync runs (just linked handle)

**Build:** `npm run build` — 0 TypeScript errors, 0 ESLint errors, `/insights` is `○ (Static)`

## Deployment — Go-Live (100% Free, Push-to-Deploy)

Plan: `docs/deployment_golive_plan.md`. Architecture: Vercel (frontend) → `/api/*` rewrite
proxy → Render (FastAPI, free) → Neon (Postgres, free); cron-job.org for keep-warm + sync.
No Redis / no Celery worker.

### D0 — Backend worker-free changes + deploy config [DONE]
**Completed:** 2026-06-29

**Files created/modified:**
- `backend/app/core/config.py` — `CRON_SECRET` setting (empty default → cron endpoints reject all)
- `backend/app/core/database.py` — asyncpg `connect_args={"ssl": True}` in production (Neon TLS)
- `backend/app/workers/cf_sync.py` — `_get_cf_problemset` now has a **process-local TTL cache**
  (Redis substitute; avoids re-fetching the ~10MB CF problemset → OOM risk on 512MB). Fixed two
  latent bugs: missing `return problems` (returned `None` on cache-miss) and a stray
  `return problems` inside `_trigger_leaderboard_rebuilds` (NameError); made the Celery
  `.delay()` leaderboard enqueue best-effort so a missing broker can't fail handle sync.
- `backend/app/api/v1/routes/cron.py` — NEW: `POST /cron/sync-contests`, `POST /cron/sync-handles`,
  guarded by `X-Cron-Secret` (constant-time compare); run work via FastAPI BackgroundTasks
- `backend/app/api/v1/__init__.py` — cron router wired
- `backend/app/api/v1/routes/auth.py` — refresh cookie `samesite` `strict` → `lax` (first-party
  via the Vercel proxy; strict would drop the cookie on the OAuth cross-site redirect)
- `backend/Dockerfile` — CMD honors Render's `$PORT` (shell form, default 8000)
- `render.yaml` — NEW: free web service from `backend/Dockerfile`, health check, `preDeployCommand:
  alembic upgrade head`, secret env vars (`sync: false`)
- `frontend/vercel.json` — NEW: rewrite `/api/:path*` → Render backend (makes API same-origin)

**Technical decisions:**
- Worker-free by design: background sync moves from Celery beat to cron-triggered BackgroundTasks;
  `REDIS_URL` unset degrades gracefully (problemset cache + sync fallback already in place, Phase 2.6)
- BackgroundTasks run sequentially after the response → handle syncs are naturally CF-rate-friendly
- Vercel rewrite proxy keeps the refresh cookie first-party (avoids Safari/Chrome third-party-cookie
  block that would silently break session-restore-on-reload)

**Verification:** 127 backend tests pass; app boots with `REDIS_URL=""`; cron endpoints return 401
without the secret.

### D1–D6 — Live deployment [DONE]
**Completed:** 2026-06-30. Full execution log + gotchas: `docs/deployment_execution.md`.

- **Live:** frontend https://prognos-chi.vercel.app · backend https://prognos-api.onrender.com ·
  Neon Postgres (Singapore). Google login working; lands on `/dashboard`.
- **Go-live fixes (commits):** `a805e8c` Render region → Singapore; `567a4c4` migrations moved
  into Docker `CMD` (free tier has no `preDeployCommand`) + alembic files copied into image +
  alembic TLS; `ed7675c` frontend API base defaults to `""` (proxy) in prod (Vercel rejects empty
  env var); `62dd121` empty commit to re-trigger a stale Vercel build.
- **Gotchas documented:** free-tier no pre-deploy hook, Vercel no empty env var, `FRONTEND_URL`
  default `localhost` after login, stale Vercel build — all in `docs/deployment_execution.md`.
- **cron-job.org [DONE]:** keep-warm `GET /health` 10m, `POST /cron/sync-contests` 4h,
  `POST /cron/sync-handles` 6h (with `X-Cron-Secret`) — all verified working. **Deployment complete.**

## Phase 5.2 — On-Demand Sync (Sync-on-View + Classroom Sync) [DONE]
**Completed:** 2026-07-02. Full write-up: `docs/phase_5_2.md`.

**Files created/modified:**
- `backend/app/workers/enqueue.py` — NEW: shared `enqueue_sync()` (extracted from `handles.py`) so
  handle-verify, sync-on-view, and classroom sync share one Celery-else-BackgroundTasks policy
- `backend/app/services/analytics.py` — `get_dashboard()` gains optional `background_tasks`;
  sync-on-view enqueues a refresh for handles stale >5 min (`SYNC_ON_VIEW_STALE_AFTER`), keyed off
  `last_synced_at` (never `last_manual_sync_at`)
- `backend/app/api/v1/routes/analytics.py` — dashboard route injects `BackgroundTasks`
- `backend/app/services/classroom.py` — NEW `sync_classroom()` (member-guarded, 15-min per-classroom
  cooldown, enqueues per-member in leaderboard order); `_classroom_syncing()` + `syncing` in
  `get_leaderboard`
- `backend/app/api/v1/routes/classrooms.py` — NEW `POST /{classroom_id}/sync` (202)
- `backend/app/models/classroom.py` — `Classroom.last_bulk_sync_at`
- `backend/app/schemas/classroom.py` — `ClassroomSyncResponse` + `LeaderboardResponse.syncing`
- `backend/alembic/versions/008_classroom_last_bulk_sync.py` — NEW migration (007 → 008)
- `frontend/app/_lib/classrooms.ts` — `syncClassroom()`, `ClassroomSyncResponse`, `syncing` field
- `frontend/app/(dashboard)/classrooms/[id]/page.tsx` — Sync button (all members), poll-while-syncing,
  cooldown banner
- Tests: +4 classroom (order, cooldown 429, non-member 403, syncing flag), +2 analytics (sync-on-view
  stale/fresh)

**Technical decisions:**
- **Client triggers, server fetches** — clients never send CF data, only request a sync; the server
  fetches authoritatively on its own IP, so a leaderboard can never carry forged data. Rejected
  client-side CF fetch: submissions are append-only facts, so peer re-syncs can add real rows but
  never erase injected fakes (and destructive-replace would enable deletion attacks).
- Two independent sync clocks: sync-on-view uses `last_synced_at` (5 min); manual button uses
  `last_manual_sync_at` (30 min) — they never fight.
- Reused `_sync_handle_async`, `rebuild_leaderboard`, and the existing 5 s poll — no new infra.

**Free-tier hardening (bugs found tracing the worker-free path):**
- `_ensure_leaderboard` now rebuilds when a member's `last_synced_at` is newer than the board
  ("behind" via `_max_member_sync`) — `_trigger_leaderboard_rebuilds` `.delay()` is a no-op without a
  broker, so otherwise the board showed stale numbers for up to the 10-min TTL after a sync.
- `_fetch_leaderboard_rows` uses `.execution_options(populate_existing=True)` — sessions are
  `expire_on_commit=False`, so the inline rebuild's Core upsert was otherwise returned stale within
  the same request (also fixed the pre-existing TTL path).
- `sync_classroom` pre-marks enqueued handles `IN_PROGRESS` in the request txn so the immediate
  leaderboard GET reports `syncing=true` and the poll starts (BackgroundTasks run after the response).
- Frontend poll: preserves the last-good board on transient errors, caps at 5 consecutive failures.

**Verification:** full backend suite green (+8 new tests this phase); `alembic upgrade head` 007→008;
`npm run build` 0 TS/ESLint errors.

## Endgame Architecture ("Max Plan") [DOC — reference]
**Written:** 2026-07-02 — `docs/architecture_endgame.md`. The definitive scaling source of truth:
two laws (reads scale with money; CF ingestion only with intelligence + client-assist +
partnership), numeric SLOs, the 100k-active CF-budget math (~21.6k server syncs/day/IP → balanced
cohort table), cloud reference stack (AWS default, GCP/Azure mapping, Terraform-portable),
speed/freshness layers, reliability/security/observability, M0–M5 roadmap with exit criteria and
cost envelopes, anti-goals. Supersedes `freshness_scalability_plan.md` (pointer added there).
First executable slice when scaling begins: **M0** (paid Redis + Tier-0 token bucket + per-handle
locks + Celery re-enabled).

## Phase 5 — Mobile App (Android + iOS) [IN_PROGRESS]

### M6 — Home-Screen Widget + Polish + Release [DONE]
**Completed:** 2026-07-04. Full write-up: `docs/phase_M6.md`. **Mobile M0–M6 complete.**
- **Android home-screen widget (R7):** next/live contest + countdown (static relative string) +
  current streak. `home_widget` — Flutter computes a flat payload from the drift caches
  (`buildWidgetPayload`: `nextContest` + cached dashboard streak) → Kotlin `ContestWidgetProvider`
  (RemoteViews) renders it; tap opens the app. Updated from the **main isolate** (cache/analytics
  change) and the **workmanager isolate** (after bg refresh). No ticking (widgets refresh ~30 min);
  graceful `—` when streak cache absent.
- **Release signing:** `build.gradle.kts` reads gitignored `key.properties` **only if present**,
  else debug — keyless release builds still succeed (verified). Secrets already gitignored.
- **Accessibility:** tooltips/semantics on icon-only buttons (invite copy/revoke, remove member);
  IconButton 48dp tap targets; theme-driven contrast.
- **Docs:** `docs/store_listing.md` (draft) + `docs/mobile_release_checklist.md` (keystore,
  Shorebird, store submission, physical-device smoke, outstanding OAuth clients).
- **Verify:** `flutter analyze` clean; `flutter test` **55 pass** (was 52) — widget payload mapping
  (empty/next/live); `flutter build apk --release` ✓; emulator install+launch + widget render.
- **User-gated (can't run here):** real keystore, store submission, Shorebird account, physical-device
  cold-start/reminder/widget checks, Android OAuth client (debug+release SHA-1).

### M5 — Classrooms + Handle Verification [DONE]
**Completed:** 2026-07-04. Full write-up: `docs/phase_M5.md`.
- **Part A — Handle verification:** 3-step wizard (enter handle → copy `PGS-XXXX` into CF
  Organization field → verify) as a state machine restored from `GET /handles`
  (None→Pending→Verified/Failed/Locked). API maps confirm 400/423/410 → typed `ConfirmException`
  (mismatch+attempts / locked / expired) so the UI never sees Dio. On success invalidates
  `analyticsProvider` → **the M4 dashboard fills in with live data**. Reached from the M4 nudge.
- **Part B — Classrooms ("Classes" tab):** cached-first list (drift KV) + create + join-by-code;
  detail = leaderboard (CF-coloured, is_me highlight, poll-while-syncing) / members / cohort +
  invites (teacher) / bulk sync / leave-delete. Leaderboard is `FutureProvider.family`
  network-first-cache-fallback (Riverpod 3 non-codegen family notifier arg access is awkward).
- **Invite deep links** `prognos://join/{token}` via `app_links` (cold-launch + running), Android
  VIEW intent-filter + iOS CFBundleURLTypes; join screen previews via public `join-preview` then joins.
- **Privacy:** `clearUserData` (sign-out) now also wipes `classrooms.*` cache; test extended.
- **Verify:** `flutter analyze` clean; `flutter test` **52 pass** (was 41) — handle state machine
  (7), classroom model round-trip + list/leaderboard cache + offline fallback; `flutter build apk
  --release` ✓ (app_links R8-clean). Live verify/leaderboards + on-device join gated on OAuth
  client (M1) + verified handle.

### M4 — Dashboard + Insights [DONE]
**Completed:** 2026-07-03. Full write-up: `docs/phase_M4.md`.
- **Personal analytics on mobile**, cached-first, matching the web. Dashboard tab with an
  **Overview ⇄ Insights** segmented toggle: Overview = stat strip (streak/solved/rating/peak, CF
  ladder) + Canvas activity heatmap (53×7, 5 levels) + `fl_chart` rating chart; Insights = tag
  bars + Focus Areas (weakness signals) + refreshable recommendations.
- **Cached-first (same contract as M2), 6 endpoints:** parallel fetch → drift blob cache (reuses
  the `Settings` KV table via model `toJson`/`fromJson` round-trip, no new migration) → never
  cleared on failure (offline note). **Polls every 5s while `is_syncing`**, stops on completion.
- `has_verified_handle=false` → "link handle on web" nudge (handle-verify is M5).
- Heatmap is a `CustomPainter` (no dep); only the rating chart needed a package (`fl_chart`).
- **Privacy fix (sign-out):** analytics is the first *private* per-user local cache; left alone,
  account-switching on one device would leak User A's dashboard (and reminders) to User B.
  `signOut` now wipes user-scoped drift rows (`analytics.*`, stars, rules, scheduled reminders,
  reminder settings), cancels all OS notifications, and invalidates in-memory providers; public
  contests cache kept. Pinned by a test.
- **Verify:** `flutter analyze` clean; `flutter test` **41 pass** (was 31) — incl. a
  `DashboardScreen` widget test (stat strip + heatmap + fl_chart, toggle to Insights), model
  round-trip, repository offline, and sign-out cleanup tests; `flutter build apk --release` ✓
  (60 MB, fl_chart R8-clean). Live dashboard needs a verified handle (M5) + OAuth client (M1).

### M3 — Contest Reminders ⭐ [DONE — device-only firing gated on a physical Android test]
**Completed:** 2026-07-03. Full write-up: `docs/phase_M3.md`.
- **The headline feature.** Star a contest or enable a platform → on-device exact alarms fire at
  `start − lead` (default 1h + 15m), offline/screen-off; tap deep-links to contest detail.
- **Reconcile ≠ fire:** an idempotent reconcile loop computes desired = (starred ∪ platform-rule)
  × leads, keyed by **deterministic 31-bit FNV-1a IDs**, and diffs against the **OS pending set**
  (`pendingNotificationRequests()`) — never against our own ledger (which desyncs on reboot / iOS
  eviction). Drift `scheduled_reminders` is intent-only (drives the "upcoming" list).
- **Correctness traps handled:** `tz.setLocalLocation` (else every alarm is UTC-offset-wrong);
  `AndroidScheduleMode.alarmClock` (Doze-exempt) + `RECEIVE_BOOT_COMPLETED` + FLN boot receiver
  (survives reboot); cold-launch deep link via `getNotificationAppLaunchDetails()` vs warm tap
  stream; single-isolate reconcile (main isolate on open/foreground/cache-update — no FLN in the
  bg isolate).
- **Reliability flow (R3):** notifications → exact-alarm grant → OEM battery whitelist (tailored
  per manufacturer via device_info_plus) → test notification. Re-runnable from Reminders screen.
- **Decisions (confirmed this slice):** per-platform rules (no division filters); in-app detail
  deep link; 1h + 15m default leads.
- Schema: drift v2 (+ StarredContests, PlatformRules, ScheduledReminders, Settings). Deps:
  flutter_local_notifications, timezone, flutter_timezone, permission_handler, device_info_plus.
  Android: reminder permissions + FLN receivers + **core-library desugaring** (FLN 22 needs java.time).
- **Verify:** `flutter analyze` clean; `flutter test` 31 pass (was 19); `flutter build apk --debug`
  **and `--release`** ✓; release APK **installed + launched on an emulator** (renders login screen).
  Firing/reboot/permissions are device-only (stated in doc); scheduling logic is unit-tested.
- **Release crash fixed (R8):** the first release build crashed at process start —
  `NoSuchMethodException: androidx.work.impl.WorkDatabase_Impl.<init>` (R8 stripped the
  reflectively-instantiated Room constructor the `workmanager` plugin needs via
  androidx.startup). Debug never showed it. Fixed with `androidx.work`/`androidx.room` + Room DB
  ctor keep rules in `android/app/proguard-rules.pro`; re-verified on emulator.

### M2 — Contests + Offline Cache [DONE]
**Completed:** 2026-07-03. Full write-up: `docs/phase_M2.md`.
- **First mobile tab with real data.** `GET /contests` (30-day window) → cached in **drift**
  (SQLite) → rendered **cached-first** (instant from cache, background refresh), fully usable
  offline. Feature parity with the web contests page: list (urgency lanes LIVE/TODAY/THIS
  WEEK/NEXT WEEK/LATER), week calendar, detail sheet w/ "Open contest" (url_launcher), platform
  filter, next/live hero + escalating countdown, pull-to-refresh.
- **Offline guarantee = one invariant:** a failed fetch never propagates or clears the cache
  (`ContestsRepository.fetchAndReplace` writes only on success; notifier keeps last-good rows).
  Tested against a *throwing* network, not an empty response.
- **Client-side platform filtering** over the cached window (offline-friendly, no re-fetch);
  API still serializes `platform` as `ListFormat.multi` (`?platform=a&platform=b`) for FastAPI.
- **Background refresh:** `workmanager` ~8h periodic, headless isolate — rebuilds auth (rotate
  refresh token via `/auth/refresh/mobile`, persist it), fetch, replace cache. Cache-only; no
  alarms (M3). On-app-open refresh in the notifier is the real freshness guarantee.
- **Timezone:** store UTC, group/format local (`.toLocal()`); grouping ported 1:1 from web
  `_lib/contests.ts`; local-day boundary case explicitly tested.
- Deps added: drift, drift_flutter, sqlite3_flutter_libs, path_provider, path, workmanager,
  url_launcher (+ dev: drift_dev, build_runner). Android manifest: INTERNET + https VIEW query.
- **Auth-gate offline fix (M1 layer):** `restoreSession` was wiping the session on *any* error —
  a cold launch in airplane mode dumped the user on login and destroyed credentials, making the
  offline Contests path unreachable. Now distinguishes network error (keep session + open with a
  keystore-cached profile) from auth rejection (401/403 → clear). `AuthInterceptor` hardened the
  same way. Lazy `ListView.builder` bounds live countdown timers to the viewport (R5).
- **Verify:** `flutter analyze` clean; `flutter test` 19 pass (was 3); `flutter build apk --debug` ✓.

### M1 — Auth (Google Sign-In) [DONE — live test gated on user's OAuth clients]
**Completed:** 2026-07-03. Full write-up: `docs/phase_M1.md`.
- **Backend:** `verify_google_id_token` (google-auth: signature+aud+iss+exp) — the *verifying*
  counterpart to the web's no-verify `decode_google_id_token`; `POST /auth/google/mobile` +
  `POST /auth/refresh/mobile` returning the pair in the body; reuses `upsert_user`/`create_session`/
  `rotate_refresh_token`. Deps: google-auth, requests. +5 tests (16 pass in auth file).
- **App:** google_sign_in v7 (`GoogleSignIn.instance` + `initialize(serverClientId)` +
  `authenticate()`), access token in memory + refresh token in keystore, `AuthInterceptor`
  (Bearer + one-shot refresh-on-401, persists rotated refresh), `AsyncNotifier` auth controller,
  login screen + auth gate, shell shows user + sign-out. `flutter analyze` clean, 3 tests pass.
- **Audience verified identical:** app `serverClientId` == backend `GOOGLE_CLIENT_ID`
  (`238081955675-…fpdlu`). **User TODO for live sign-in:** create Android (pkg `io.prognos.prognos`
  + debug SHA-1) and iOS OAuth clients in Google Cloud.

### M0 — Foundation [DONE]
**Completed:** 2026-07-02. Full write-up: `docs/phase_M0.md`.
- Flutter 3.44.4 SDK installed user-local at `~/dev/flutter` (no sudo, removable).
- `flutter create` project at `mobile/` (Android+iOS); deps: flutter_riverpod, dio, google_fonts,
  intl, flutter_secure_storage.
- Design system transcribes the web tokens exactly (`app_colors.dart`, `cf_rating.dart` ← from
  `frontend/app/globals.css` + stat-strip ladder); Material 3 dark theme, Inter/JetBrains Mono.
- Core wiring: `AppConfig` (API base via --dart-define), `dioProvider`, `secureStoreProvider`,
  3-tab shell (Dashboard/Contests/Leaderboard placeholders), shimmer `Skeleton`.
- **Verify:** `flutter analyze` clean; `flutter test` 3/3 pass. (APK/device run needs Android SDK
  on the user's machine — see `mobile/README.md`.)


**Plan finalized:** 2026-07-02 — `docs/mobile_implementation_plan.md` (supersedes the
Android-only Kotlin plan; user widened scope to both platforms → **Flutter**, research-backed:
RN's Notifee archived Apr 2026, `flutter_local_notifications` v22 active; market wide open —
WatchR dead, no competitor has alarms+streaks+classrooms). Headline feature: **local contest
reminders** (per-contest bell + per-platform auto-rules, 1h+15m defaults, exact alarms
Doze/reboot-proof, iOS 64-cap rolling window, first-run reliability flow). Feature parity with
web, cached-first rendering (<2s cold start), web design tokens ported. Slices M0–M6; M1 needs
two additive backend auth endpoints (verified Google ID-token exchange + body refresh).
## Phase 6 — AI Layer [TODO]
