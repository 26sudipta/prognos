# PROGNOS — Go-Live Plan (100% Free, Push-to-Deploy)
**Status:** Approved plan — not yet implemented. Execute one slice at a time (CLAUDE.md §2).

## Context

The web app (Next.js frontend + FastAPI backend + Postgres + Redis + Celery worker) needs to go
**live, free of cost, with auto-deploy on `git push`**, with minimal ops headache. Repo is on
GitHub (`26sudipta/prognos`), `main` branch.

**The core finding:** frontend and Postgres host free easily; the **Celery worker + Redis** are
the only things that block a clean free tier (free hosts don't run always-on workers well, and
Upstash's free Redis drains fast because Celery polls the broker continuously). We already have
the escape hatch built: the **FastAPI BackgroundTasks fallback** (Phase 2.6) + **sync-on-view**
design let us **drop Celery/Redis entirely** for the free deployment.

**Chosen path (user decision): 100% free**, accepting minor compromises (occasional cold start).

### Market research (free tiers, 2026)
| Component | Free host | Verdict |
|---|---|---|
| Frontend (Next.js) | **Vercel** Hobby | Free, auto-deploy on push — best in class |
| Postgres | **Neon** free | Sustainable, scale-to-zero (<500ms resume). Beats Supabase, which pauses entirely after 1 week idle and needs manual unpause |
| Backend (FastAPI) | **Render** free web service | Free, auto-deploy; spins down on idle → solved with a keep-warm ping |
| Redis | **Upstash** free | Avoided — Celery polls the broker constantly and drains the 500K-commands/month quota |
| Celery worker | — | No good free always-on worker → **dropped** |

### Target architecture (free)
```
Browser
  │
  ▼
Vercel  (Next.js)  —— /api/* rewrite proxy ——▶  Render (FastAPI, free)  ──▶  Neon (Postgres, free)
  ▲                                                     ▲
  └── first-party cookie (same origin via proxy)        │
                                                cron-job.org (free)
                                       • GET /api/v1/health every 10m  (keep-warm)
                                       • POST /api/v1/cron/sync-contests  every 4h
                                       • POST /api/v1/cron/sync-handles    every 6h
No Redis. No Celery worker. CF problemset cached in-process (TTL).
```

**Why the Vercel rewrite proxy is the keystone:** if the browser talked to `onrender.com`
directly while the page is `vercel.app`, the refresh cookie would be **third-party** → Safari
blocks it, Chrome restricts it → **session-restore-on-reload silently fails** (breaks the Phase
1.4 auth model). Proxying `/api/*` through Vercel makes the API **same-origin** → cookie is
first-party → `SameSite=Lax` just works, and the cross-origin CORS + `SameSite=None` complexity
disappears. One cheap latency hop, free at hobby scale.

---

## Part A — Backend code/config changes (do first, verify locally)

1. **Replace Redis with an in-process TTL cache** (the ~10MB CF problemset refetched
   per-recommendation risks OOM on Render's 512MB). In
   [cf_sync.py](../backend/app/workers/cf_sync.py) `_get_cf_problemset`: keep the Redis path when
   `REDIS_URL` is set, else use a **module-level dict `{data, fetched_at}` with a 6h TTL**.
   Single web process → a process-local cache is a correct Redis substitute here.

2. **Cron trigger endpoints** (replace the Celery beat schedule). New
   `backend/app/api/v1/routes/cron.py`, guarded by an `X-Cron-Secret` header == `settings.CRON_SECRET`:
   - `POST /api/v1/cron/sync-contests` → runs CLIST sync core (`_run_sync` already exists, PROGRESS
     3.1) via `BackgroundTasks`.
   - `POST /api/v1/cron/sync-handles` → enqueues `_sync_handle_async` for all active verified
     handles via `BackgroundTasks` (reuse the `_enqueue_all_handles` selection logic).
   - 401 on missing/wrong secret. Wire into [__init__.py](../backend/app/api/v1/__init__.py).
   - Add `CRON_SECRET` to [config.py](../backend/app/core/config.py) (default empty → endpoints 403).

3. **Neon + asyncpg SSL** in [database.py](../backend/app/core/database.py): add
   `connect_args={"ssl": True}` (gated to production / non-localhost) to `create_async_engine`.
   Use Neon's **direct** endpoint (not `-pooler`) at this scale; if the pooled endpoint is ever
   used, also set `statement_cache_size=0` (asyncpg + PgBouncer breaks prepared statements).

4. **Cookie**: with the proxy the cookie is first-party, so change `samesite="strict"` →
   `"lax"` in `_set_refresh_cookie` ([auth.py](../backend/app/api/v1/routes/auth.py)) for safety;
   keep `secure=is_production`. No `SameSite=None`, no cross-origin CORS needed.

5. **Confirm worker-free boot**: `celery_app` import must not open a broker connection at startup
   (Celery connects on send; Phase 2.6 wrapped `_enqueue_sync` in try/except) — so an unset
   `REDIS_URL` won't crash the web process. Verify `backend/Dockerfile` binds **`$PORT`** (Render
   injects it).

## Part B — Deployment config files (committed to repo)

6. **`frontend/vercel.json`** — rewrite `/api/:path*` → `https://<render-app>.onrender.com/api/:path*`.
   Set Vercel project **Root Directory = `frontend`** and env `NEXT_PUBLIC_API_URL=""` so the
   client calls relative `/api/v1/...` ([api.ts](../frontend/app/_lib/api.ts) already reads that var).

7. **`render.yaml`** (repo root) — web service built from `backend/Dockerfile`,
   `healthCheckPath: /api/v1/health`, `preDeployCommand: alembic upgrade head`, env vars (below).
   Mirrors the existing [railway.toml](../railway.toml) web service, minus the worker.

## Part C — External setup (user actions, documented — no secrets in chat)

8. **Neon**: create project → copy the **direct** asyncpg connection string → it becomes
   `DATABASE_URL` on Render.
9. **Render**: New Web Service → connect the GitHub repo → it reads `render.yaml` → set secret
   env vars in the dashboard. Auto-deploys on push to `main`.
10. **Vercel**: Import the GitHub repo → Root Directory `frontend` → deploy. Auto-deploys on push.
11. **Google Cloud**: add authorized redirect URI
    `https://<vercel-app>/api/v1/auth/google/callback` (goes through the proxy → first-party
    cookie) and authorized JS origin `https://<vercel-app>`. Set `GOOGLE_REDIRECT_URI` on Render
    to that Vercel callback URL; `FRONTEND_URL` = the Vercel URL.
12. **cron-job.org** (free): keep-warm `GET /health` every 10m; `POST /cron/sync-contests` every
    4h and `POST /cron/sync-handles` every 6h, each with the `X-Cron-Secret` header. (cron-job.org
    over GitHub Actions — more reliable, no 60-day repo-inactivity disable.)

### Env var matrix
| Var | Render (backend) | Vercel (frontend) |
|---|---|---|
| `DATABASE_URL` | Neon direct URL | — |
| `GOOGLE_CLIENT_ID` / `_SECRET` | ✓ | — |
| `GOOGLE_REDIRECT_URI` | `https://<vercel>/api/v1/auth/google/callback` | — |
| `FRONTEND_URL` | `https://<vercel>` | — |
| `ENVIRONMENT` | `production` | — |
| JWT secret | ✓ | — |
| `CRON_SECRET` | ✓ | — |
| `CLIST_USERNAME` / `CLIST_API_KEY` | ✓ | — |
| `REDIS_URL` | unset (graceful) | — |
| `NEXT_PUBLIC_API_URL` | — | `""` (relative, via proxy) |

---

## Execution order (slices)

| Slice | Does |
|---|---|
| **D0** | Part A code + Part B config files; verify locally (boot with `REDIS_URL` empty + no worker) |
| **D1** | Provision Neon; run `alembic upgrade head` against it |
| **D2** | Deploy backend to Render (env vars, health check) |
| **D3** | Deploy frontend to Vercel (root `frontend`, `vercel.json` rewrite) |
| **D4** | Wire Google OAuth redirect/origin + `FRONTEND_URL`/`GOOGLE_REDIRECT_URI` |
| **D5** | Configure cron-job.org (keep-warm + 2 sync jobs) |
| **D6** | End-to-end verification |

---

## Verification

**Local (D0):**
- App boots with `REDIS_URL` empty and no Celery worker running.
- `POST /api/v1/cron/sync-contests` with the secret → contests populate; **without** the secret → 401.
- Recommendation generation works (in-process problemset cache; no Redis).

**Production (D6):**
- `git push` to `main` → Vercel **and** Render auto-deploy.
- Login works; **reload the page → session restores** (first-party cookie via proxy) — test in
  **both Chrome and Safari** (this is the third-party-cookie trap; must pass on Safari).
- Dashboard/contests/classrooms load against Neon.
- Trigger `sync-contests` cron → contest list fills; trigger `sync-handles` → dashboard data syncs.
- Keep-warm ping holds the backend awake (no cold start on a normal visit).

---

## Compromises & upgrade path (be honest)
- **Cold start** if the keep-warm ping ever lapses (~30–50s first hit on Render free) — acceptable
  at hobby scale.
- **Neon scale-to-zero** adds <500ms on the first query after idle.
- No always-on worker → background refresh is cron-driven, not continuous (fine; matches the
  freshness plan's on-view model).
- **Flip to paid later is trivial:** the existing [railway.toml](../railway.toml) already defines the
  always-on web+worker+Redis setup — moving to Railway (~$5/mo) restores Celery with no code change.
