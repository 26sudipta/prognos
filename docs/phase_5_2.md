# Phase 5.2 — On-Demand Sync (Sync-on-View + Classroom Sync)

**Status:** DONE — 2026-07-02

## Context

The flat 6-hour background cron (see `docs/deployment_golive_plan.md`) meant a user — or
anyone reading a classroom leaderboard — could stare at data up to 6 hours stale with no way
to refresh it short of the personal "Sync now" button. The architecture review flagged this
freshness gap.

We explored letting the **client fetch Codeforces data itself** (each browser's IP has its own
CF rate-limit budget, so this would distribute load and scale freshness linearly). We **rejected**
it after analysis:

1. **Client-fed data is forgeable** — a user could POST fabricated submissions to inflate their
   own leaderboard standing.
2. **Submissions are append-only facts** — ingest inserts rows keyed by `(handle, cf_submission_id)`
   and never deletes. So an honest peer re-syncing a cheater can only *add* real rows, never
   *erase* injected fake ones. Making sync destructive-replace would hand any user a one-click
   tool to delete a rival's real data.

**Decision: client triggers, server fetches.** The client never writes CF data — it only asks the
server to fetch authoritatively from CF on the server's own IP. The leaderboard can therefore only
ever reflect real Codeforces data, and no client can touch another user's data. The tradeoff (the
server IP stays the CF bottleneck) is acceptable: on-demand + sync-on-view spends the CF budget
only where humans are actually looking — Tier 1 of `docs/freshness_scalability_plan.md`.

---

## What Was Built

```
backend/
  app/
    workers/
      enqueue.py                       ← NEW: shared enqueue_sync() (extracted from handles.py)
    services/
      analytics.py                     ← get_dashboard(): sync-on-view for stale handles
      classroom.py                     ← sync_classroom() + _classroom_syncing() + syncing flag
    api/v1/routes/
      analytics.py                     ← dashboard route now injects BackgroundTasks
      handles.py                       ← uses shared enqueue_sync (local helper removed)
      classrooms.py                    ← NEW route: POST /{classroom_id}/sync
    models/
      classroom.py                     ← Classroom.last_bulk_sync_at column
    schemas/
      classroom.py                     ← ClassroomSyncResponse + LeaderboardResponse.syncing
  alembic/versions/
    008_classroom_last_bulk_sync.py    ← NEW migration
  tests/integration/
    test_classroom_routes.py           ← +4 tests (order, cooldown, 403, syncing flag)
    test_analytics_routes.py           ← +2 tests (sync-on-view stale / fresh)

frontend/
  app/_lib/classrooms.ts               ← syncClassroom() + ClassroomSyncResponse + syncing field
  app/(dashboard)/classrooms/[id]/page.tsx  ← Sync button, poll-while-syncing, cooldown banner
```

---

## Concepts Explained

### 1. Why one shared `enqueue_sync` helper
Three call sites now need to kick off an authoritative per-handle sync: handle verification
(`handles.py`), sync-on-view (`analytics.py`), and classroom bulk sync (`classrooms.py`). The
enqueue *policy* — try Celery `.delay()`, else fall back to FastAPI `BackgroundTasks` for the
worker-free free-tier deployment — must live in exactly one place so all three behave
identically. It was previously a private `_enqueue_sync` inside `handles.py`; it moved verbatim to
`app/workers/enqueue.py`. `cf_sync` is imported lazily *inside* the function to avoid an import
cycle (services → enqueue → cf_sync → …).

### 2. Sync-on-view (personal dashboard)
`get_dashboard()` gained an optional `background_tasks` parameter. When present (i.e. called from
the HTTP route, not a unit test), it checks each verified handle: if `last_synced_at` is older than
`SYNC_ON_VIEW_STALE_AFTER` (5 min) — or the handle has never synced and isn't already in progress —
it enqueues a refresh and sets `is_syncing=true`.

The frontend already polls `/analytics/dashboard` every 5s while `is_syncing` and auto-reloads on
completion (Phase 2.6), so **no frontend change was needed** for personal freshness.

**Critical detail — two independent clocks:**

| Field | Drives | Cooldown |
|---|---|---|
| `last_synced_at` | sync-on-view staleness | 5 min |
| `last_manual_sync_at` | the "Sync now" button | 30 min |

Sync-on-view keys off `last_synced_at` and **never writes** `last_manual_sync_at`, so automatic
refreshes never consume the manual button's cooldown. A regression test asserts exactly this.

### 3. Classroom "Sync" button (`POST /classrooms/{id}/sync`)
Any member (teacher or student) may press it. The endpoint:

1. Asserts membership (`_assert_member` → 403 otherwise).
2. Enforces a per-classroom cooldown via `Classroom.last_bulk_sync_at` (`BULK_SYNC_COOLDOWN` =
   15 min → 429 with `retry_after_seconds`). This protects the shared CF budget: a full 100-member
   re-sync already costs ~3.3 min of CF calls (1 call / 2 s).
3. Reads members **in current leaderboard order** (`cf_rating desc, solved_count desc`) so the
   visible top of the board refreshes first; members missing from the cache are appended.
4. Enqueues `_sync_handle_async` per verified handle via the shared helper. Under `BackgroundTasks`
   these run **sequentially** and `_fetch_submissions` already sleeps 2 s between CF calls, so the
   wave is naturally CF-rate-safe. Each per-handle sync already ends with
   `_trigger_leaderboard_rebuilds`, so rows update as members finish.

**Why this can't be cheated:** the client sends *no data*, only the request to sync. The server
fetches the truth from CF. There is no code path for a client to write submissions for itself or
anyone else.

### 3b. Free-tier freshness fixes found during hardening
Two non-obvious bugs surfaced when tracing the worker-free path end-to-end:

1. **Leaderboard didn't reflect a sync for up to the TTL.** `_trigger_leaderboard_rebuilds` uses
   Celery `.delay()`, which is a **no-op with no broker** — so member syncs never rebuilt the cache,
   and `_ensure_leaderboard` saw "fresh" rows (10-min TTL) and skipped a rebuild. Fix:
   `_ensure_leaderboard` now also rebuilds when a member's `last_synced_at` is newer than the board's
   `computed_at` ("behind"), via `_max_member_sync`. This gives live incremental updates while a bulk
   sync runs, captures the last member on the final poll, and self-limits (after a rebuild the board
   is no longer behind).

2. **Rebuild results were served stale within the same request.** Sessions use
   `expire_on_commit=False`, so after the inline rebuild (a Core `pg_insert().on_conflict_do_update()`
   + commit) the identity-mapped ORM rows were returned with their *old* values — the rebuilt data
   only appeared on the *next* request. Fix: `_fetch_leaderboard_rows` uses
   `.execution_options(populate_existing=True)` so the refetch overwrites cached attributes with
   fresh DB values. (This also silently fixed the pre-existing TTL-rebuild path.)

3. **Poll could fail to start.** BackgroundTasks run *after* the response, so the leaderboard GET
   fired immediately after `POST /sync` could see `syncing=false`. `sync_classroom` now pre-marks the
   enqueued handles `IN_PROGRESS` in the committed request transaction, so the first read
   deterministically reports `syncing=true`. Safe because `_sync_handle_async` always runs regardless
   of status and cron re-syncs all verified handles, so a handle can't get stuck.

### 4. Leaderboard `syncing` flag + progress UX
`LeaderboardResponse.syncing` is `true` while any member's verified handle has
`sync_status == in_progress` (`_classroom_syncing`, one COUNT query). The classroom page starts a
5-second poll while `syncing` is true — mirroring the dashboard pattern — re-rendering rows as
bulk-sync results land, and stops when it clears. A 429 surfaces a friendly "Recently synced — try
again in ~N min" banner.

---

## Verification

```bash
# Backend — full suite (8 new tests added this phase: 4 classroom sync, 2 sync-on-view,
# 2 free-tier freshness/poll hardening)
cd backend && .venv/bin/python -m pytest -q

# Targeted
.venv/bin/python -m pytest -q tests/integration/test_classroom_routes.py \
                              tests/integration/test_analytics_routes.py
# → 55 passed  (includes: sync order, cooldown 429, non-member 403, syncing flag,
#                sync-on-view enqueues-when-stale, skips-when-fresh)

# Migration
.venv/bin/python -m alembic upgrade head    # 007 → 008 add classrooms.last_bulk_sync_at

# Frontend typecheck
cd frontend && npx tsc --noEmit             # 0 errors
```

**Manual:** open a classroom → click **Sync** → top rows refresh first, footer shows
"Refreshing members from Codeforces…", rows update as members complete, indicator clears; pressing
Sync again within 15 min shows the cooldown banner. Open a stale personal dashboard → it
auto-syncs on load and re-renders via the existing 5 s poll.

---

## Key Takeaways

- **Client triggers, server fetches** — the only design that keeps a competitive leaderboard
  trustworthy when freshness is user-driven. Append-only submission facts mean crowd-sourced
  client writes can never erase forgeries, only server-authoritative fetches can.
- **Two sync clocks** (`last_synced_at` vs `last_manual_sync_at`) let automatic and manual refresh
  coexist without fighting over one cooldown.
- **Spend the CF budget where humans look** — sync-on-view + on-demand classroom sync realize Tier 1
  of the freshness plan without any new infrastructure, reusing `_sync_handle_async`,
  `rebuild_leaderboard`, and the existing 5 s poll.

## Next

The per-IP client-fetch idea remains parked as a possible future *personal-only* optimization if
the server CF budget ever binds — see `docs/freshness_scalability_plan.md`.
