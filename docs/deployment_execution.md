# Deployment Execution Log — Going Live (Free Tier)
**Date:** 2026-06-29 → 2026-06-30
**Outcome:** PROGNOS web app deployed live, 100% free, auto-deploy on `git push`.
**Plan it follows:** [deployment_golive_plan.md](deployment_golive_plan.md)

This log records *what we actually did* and — more importantly — *every gotcha hit during
go-live and how it was fixed*, so a future deploy (or the next environment) is painless.

---

## Live URLs

| Piece | URL | Host |
|---|---|---|
| Frontend (web app) | https://prognos-chi.vercel.app | Vercel (free) |
| Backend API | https://prognos-api.onrender.com | Render (free, Singapore) |
| Database | (Neon direct endpoint) | Neon (free, Singapore) |

Architecture: **Browser → Vercel (Next.js + `/api/*` rewrite proxy) → Render (FastAPI) →
Neon (Postgres)**. No Redis, no Celery worker. Background sync via cron-triggered endpoints.

---

## Commits made this session

| Commit | What |
|---|---|
| `30cc1fd` | feat(deploy): worker-free backend — cron endpoints, in-process problemset cache, Neon TLS, cookie `strict→lax`, `$PORT` Dockerfile, `render.yaml`, `frontend/vercel.json`; fixed 2 latent bugs in `_get_cf_problemset` |
| `df51002` | docs: deployment / freshness-scalability / Android plans |
| `a805e8c` | chore(deploy): Render region → Singapore (match Neon) |
| `567a4c4` | fix(deploy): run migrations at container start (free tier has no preDeploy) |
| `ed7675c` | fix(frontend): default API base to proxy path (`""`) in production |
| `62dd121` | chore: trigger Vercel redeploy with the API-base fix |

Also created (planning, not code): [freshness_scalability_plan.md](freshness_scalability_plan.md),
[mobile_android_implementation_plan.md](mobile_android_implementation_plan.md).

---

## What we built (code/config)

1. **Worker-free backend** — drop the hard Celery/Redis dependency so the app runs on free
   hosting:
   - `app/api/v1/routes/cron.py` (NEW) — `POST /cron/sync-contests`, `POST /cron/sync-handles`,
     guarded by an `X-Cron-Secret` header (constant-time compare); work runs via FastAPI
     `BackgroundTasks`. Replaces the Celery beat schedule.
   - `app/workers/cf_sync.py` — `_get_cf_problemset` gained a **process-local TTL cache**
     (Redis substitute). Fixed two latent bugs uncovered here: a missing `return problems`
     (cache-miss returned `None`) and a stray `return problems` inside
     `_trigger_leaderboard_rebuilds` (`NameError`); made the Celery `.delay()` enqueue
     best-effort so a missing broker can't fail a handle sync.
   - `app/core/config.py` — `CRON_SECRET`. `app/core/database.py` + `alembic/env.py` — asyncpg
     `connect_args={"ssl": True}` in production (Neon requires TLS).
   - `app/api/v1/routes/auth.py` — refresh cookie `samesite` `strict → lax`.
2. **Deploy config** — `render.yaml` (free web service from `backend/Dockerfile`),
   `frontend/vercel.json` (rewrite `/api/*` → Render), `backend/Dockerfile` now honors `$PORT`
   and runs `alembic upgrade head` at container start.

---

## Gotchas hit during go-live (the valuable part)

### 1. `preDeployCommand` is not allowed on Render's free tier
**Symptom:** Blueprint validation error — *"pre-deploy command is not supported for free tier."*
**Fix (`567a4c4`):** moved `alembic upgrade head` into the **Docker `CMD`** (runs right before
uvicorn on every container start; a no-op when the DB is already current). Also had to **copy the
alembic files into the image** (`COPY alembic/ ./alembic/`, `COPY alembic.ini ./`) — they weren't
in the image before — and give `alembic/env.py` the same TLS `connect_args` for Neon.

### 2. Vercel rejects an empty env var value
**Symptom:** Setting `NEXT_PUBLIC_API_URL=""` (needed so the SPA uses the same-origin proxy)
failed with *"value is required."*
**Fix (`ed7675c`):** removed the env var entirely and changed the **code default** instead — in
all four call sites (`_lib/api.ts`, `_lib/classrooms.ts`, `(auth)/login/page.tsx`,
`_components/auth-provider.tsx`) the base now falls back to `""` (relative, proxied) when
`NODE_ENV === "production"` and the var is unset; localhost is kept for dev.

### 3. After login, redirected to `http://localhost:3000/dashboard`
**Symptom:** Google auth succeeded but the callback bounced to localhost.
**Cause:** `http://localhost:3000` is the **code default** for `FRONTEND_URL` — the callback
redirects to `{FRONTEND_URL}/callback`, so the value simply wasn't set to the Vercel URL on
Render.
**Fix:** set `FRONTEND_URL=https://prognos-chi.vercel.app` (no trailing slash) +
`GOOGLE_REDIRECT_URI=https://prognos-chi.vercel.app/api/v1/auth/google/callback` in Render's
Environment, then redeploy.

### 4. Stale Vercel build served the old `localhost` URL
**Symptom:** login button still pointed at `localhost:8000` even after the fix was on GitHub.
**Cause:** Vercel built a snapshot from *before* `ed7675c`.
**Fix:** an empty commit (`62dd121`) + push to re-trigger the build from latest `main`.

### Why the Vercel proxy matters (design note)
The `/api/*` rewrite makes the API **same-origin** with the frontend, so the refresh cookie is
**first-party** — Safari (ITP) and Chrome block third-party cookies, which would otherwise make
session-restore-on-reload silently fail. This is why `FRONTEND_URL`, `GOOGLE_REDIRECT_URI`, and
the cookie all use the `vercel.app` domain (proxied), not the `onrender.com` domain directly.

---

## OAuth wiring (Google Cloud)
On the existing Web OAuth client, added:
- Authorized JavaScript origin: `https://prognos-chi.vercel.app`
- Authorized redirect URI: `https://prognos-chi.vercel.app/api/v1/auth/google/callback`

---

## Verification
- `curl https://prognos-api.onrender.com/api/v1/health` → `200 {"status":"ok","service":"prognos-api"}`
  (first hit ~6s = free-tier cold start; migrations ran, Neon connected).
- Frontend build: `npm run build` → 0 errors, 12 routes.
- Backend: 127 tests pass; boots with `REDIS_URL=""`; cron endpoints return 401 without the secret.
- Login: Google consent → lands on `https://prognos-chi.vercel.app/dashboard` (after `FRONTEND_URL` fix).

---

## Remaining steps
- [x] **cron-job.org** (free) — three jobs against the Render URL, all verified working:
  - `GET /api/v1/health` every ~10 min (keep-warm, avoids cold starts)
  - `POST /api/v1/cron/sync-contests` every 4h (`X-Cron-Secret` header)
  - `POST /api/v1/cron/sync-handles` every 6h (`X-Cron-Secret` header)
  - Note: a browser GET on the POST-only cron URLs returns 405 (expected); the keep-warm job may
    log one "timeout" on a cold start but still wakes the server.
- [ ] Commit the 3 WIP frontend files (`recommendations.tsx`, `weakness-cards.tsx`,
  `layout.tsx`) if desired — they were intentionally left out of this deploy.

---

## Key takeaways
- **Free tiers have sharp edges:** no pre-deploy hooks (run migrations in `CMD`), no empty env
  vars (default in code), instances sleep (keep-warm ping). Plan around them, don't fight them.
- **Same-origin via a proxy** is the cleanest way to keep auth cookies working across a
  split frontend/backend host — and it's free.
- **`localhost` showing up in prod** almost always means a missing env var falling back to a
  code default (`FRONTEND_URL`) or a stale build — check both.
- Flipping to paid Railway later restores Celery/Redis with **zero code change**
  ([railway.toml](../railway.toml) already exists).
