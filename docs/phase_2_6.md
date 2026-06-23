# Phase 2.6 — Dev Sync Fix & First-Sync UX

## What Was Built

A cross-cutting fix that makes the analytics pipeline usable in a local dev environment
(no Redis, no Celery worker) and gives users clear feedback during their first sync.

```
backend/
  app/
    api/v1/routes/handles.py          ← auto-trigger sync on verify; BackgroundTask fallback
    schemas/analytics.py              ← is_syncing field added to DashboardResponse
    services/analytics.py             ← is_syncing populated from handle sync_status
    workers/cf_sync.py                ← Redis graceful degradation; blocking sleep fixed
  tests/
    integration/test_handle_routes.py ← mock updated: lastName → organization
    unit/test_handle_service.py       ← mock updated: lastName → organization

frontend/
  app/
    (dashboard)/
      dashboard/page.tsx              ← polling while is_syncing; spinner banner
      handles/page.tsx                ← "Sync & Go to Dashboard" button; handleId in SUCCESS
    _lib/
      analytics.ts                    ← is_syncing added to DashboardData type
      handles.ts                      ← syncHandle() API function added
```

---

## 1. Root Cause: Dashboard Was Always Empty

**Symptom:** User verified a handle; the dashboard showed all zeros and a blank heatmap.

**Cause:** The analytics tables (`daily_activity`, `tag_stats`, `rating_history`,
`weakness_signals`) are only populated by the CF sync pipeline. That pipeline runs inside
a Celery worker, which in turn needs Redis as a message broker. Neither Redis nor Celery
is started by `run.sh` — so no sync had ever run, and all analytics tables were empty.

The sequence expected by the design:

```
User verifies handle
      │
      ▼
POST /handles/verify/confirm
      │
      ▼
sync_handle.delay(handle_id)  ──→  Redis queue
                                        │
                                        ▼
                                  Celery worker
                                  _sync_handle_async()
                                        │
                                        ▼
                            submissions / daily_activity /
                            tag_stats / rating_history /
                            weakness_signals / recommendations
```

In the dev environment this chain broke at the first arrow: no Redis → the
`.delay()` call raised `kombu.exceptions.OperationalError` and the sync never ran.

---

## 2. Fix 1 — BackgroundTask Fallback in the Handles Router

The sync endpoint (and the verify-confirm endpoint) now try Celery first, then fall
back to a FastAPI `BackgroundTask` when Celery/Redis is unavailable.

```python
# handles.py — shared helper
def _enqueue_sync(handle_id: uuid.UUID, background_tasks: BackgroundTasks) -> str:
    try:
        from app.workers.cf_sync import sync_handle
        task = sync_handle.delay(str(handle_id))
        return task.id
    except Exception:
        from app.workers.cf_sync import _sync_handle_async
        background_tasks.add_task(_sync_handle_async, handle_id)
        return str(uuid.uuid4())
```

This means:
- **With Redis + Celery running:** exact same behaviour as before — task queued.
- **Dev (no Redis):** sync runs in the FastAPI process as a background coroutine after
  the HTTP response is returned.

`_sync_handle_async` creates its own SQLAlchemy engine (it was designed to run in a
separate Celery worker process), so it doesn't interfere with the FastAPI request session.

---

## 3. Fix 2 — Auto-Trigger Sync on Handle Verification

Previously, users had to hit a separate "Sync" endpoint after verification. The
`confirm` endpoint now calls `_enqueue_sync` automatically:

```python
@router.post("/verify/confirm", response_model=HandleVerifiedResponse)
async def confirm(body, background_tasks, db, current_user):
    row = await confirm_verification(db, current_user.id, body.handle_id)
    _enqueue_sync(row.id, background_tasks)           # ← new
    return HandleVerifiedResponse(...)
```

For all future verifications (and re-verifications after unlink), the sync fires
immediately and data appears in the dashboard without any manual step.

---

## 4. Fix 3 — Blocking Sleep in the Sync Worker

`_fetch_submissions` paginates CF's `user.status` API and sleeps 2 seconds between
pages to respect CF's rate limit. The original code used `time.sleep(2)` — a
**blocking** call that would freeze the entire FastAPI event loop for 2 seconds per
page when the sync runs as a `BackgroundTask`.

```python
# Before — blocks event loop for 2s per 500-submission page
time.sleep(2)  # CF rate limit

# After — yields control back to the event loop
await asyncio.sleep(2)  # CF rate limit
```

With Celery the sync runs in a separate process so `time.sleep` was harmless there.
Now that sync can run inside the FastAPI event loop, only the async version is correct.

---

## 5. Fix 4 — Redis Graceful Degradation

`_generate_recommendations` calls `_get_cf_problemset()` which fetches CF's full
problem list and caches it in Redis. With no Redis running, this call raised
`redis.exceptions.ConnectionError` and the entire sync failed at the last step.

The function is now wrapped so Redis failures are silently caught at both the read
and write path:

```python
async def _get_cf_problemset() -> list[dict]:
    # Try cache read (best-effort)
    try:
        r = aioredis.from_url(settings.REDIS_URL, socket_connect_timeout=2)
        try:
            cached = await r.get(CF_PROBLEMSET_CACHE_KEY)
            if cached:
                return json.loads(cached)
        finally:
            await r.aclose()
    except Exception:
        pass  # Redis unavailable — fall through

    # Fetch directly from CF
    async with httpx.AsyncClient() as client:
        data = await _cf_get(client, "problemset.problems")
    problems = data["result"]["problems"]

    # Try cache write (best-effort)
    try:
        r = aioredis.from_url(settings.REDIS_URL, socket_connect_timeout=2)
        try:
            await r.set(CF_PROBLEMSET_CACHE_KEY, json.dumps(problems), ex=CF_PROBLEMSET_TTL)
        finally:
            await r.aclose()
    except Exception:
        pass  # ignore — next call will re-fetch

    return problems
```

`socket_connect_timeout=2` caps the connection attempt at 2 seconds so a "Redis not
running" failure is fast rather than blocking for the OS default timeout (often 30s).

---

## 6. Fix 5 — `is_syncing` Field and Dashboard Polling

When a user lands on the dashboard immediately after verifying, the sync is still
running. Without any indicator, the dashboard looks broken (all zeros).

`DashboardResponse` now carries an `is_syncing` boolean:

```python
# schemas/analytics.py
class DashboardResponse(BaseModel):
    ...
    is_syncing: bool = False
```

Populated in `get_dashboard()`:

```python
sync_row = (await db.execute(
    select(UserHandle.sync_status, UserHandle.last_synced_at)
    .where(UserHandle.id.in_(handle_ids))
    .limit(1)
)).first()

is_syncing = sync_row is not None and (
    sync_row.sync_status == HandleSyncStatus.IN_PROGRESS
    or sync_row.last_synced_at is None   # ← never completed a sync
)
```

`last_synced_at IS NULL` catches the period between "sync enqueued as BackgroundTask"
and "sync sets status to IN_PROGRESS" — that window is small but real.

The dashboard polls every 5 seconds while `is_syncing` is true, then stops and
reloads all sections once sync completes:

```tsx
if (d.is_syncing) {
  pollRef.current = setInterval(() => {
    fetchDashboard(tok).then((fresh) => {
      setDashboard(fresh);
      if (!fresh.is_syncing) {
        clearInterval(pollRef.current!);
        pollRef.current = null;
        // Reload all other sections now that data exists
        fetchTags(tok).then(setTags)...
      }
    });
  }, 5000);
}
```

During sync, a blue banner is shown at the top of the page:

```
⟳  Syncing your Codeforces data… This usually takes 1–2 minutes.
   The page will update automatically.
```

---

## 7. Fix 6 — Handles Page Success State

Three bugs in the `SUCCESS` state of the handles wizard:

| # | Bug | Fix |
|---|---|---|
| 1 | "Go to Dashboard" `<a>` linked to `codeforces.com/profile/{handle}` | Replaced with "Sync & Go to Dashboard" button that calls `POST /handles/{id}/sync`, then navigates to `/dashboard` via `useRouter` |
| 2 | `SUCCESS` state stored `{ handle, verifiedAt }` — no `handleId` | Added `handleId: string` to `SUCCESS` state type; updated both setters (on page load from `fetchHandles` and after `confirmVerification`) |
| 3 | No way to trigger sync for an already-verified handle | "Sync & Go to Dashboard" button fires `syncHandle()` → `POST /handles/{id}/sync` |

The `syncHandle()` function in `_lib/handles.ts` treats HTTP 429 (cooldown active) as
success — cooldown means a sync is either in progress or just ran, which is the outcome
the button is trying to achieve.

---

## 8. Test Fixes

The handle verification service was changed from reading `lastName` to `organization`
in the Phase 2.5 QA audit (see `docs/phase_1_6.md` Updates). The test mocks were not
updated at the same time, leaving a latent failure.

Both test files updated:

```python
# Before
CF_OK      = {"status": "OK", "result": [{"handle": "tourist", "lastName": ""}]}
CF_WITH_TOKEN = lambda t: {..., "lastName": t}

# After
CF_OK      = {"status": "OK", "result": [{"handle": "tourist", "organization": ""}]}
CF_WITH_TOKEN = lambda t: {..., "organization": t}
```

All 67 tests pass after the fix.

---

## Verification

```bash
# 1. Start the app (no Redis/Celery needed)
./run.sh

# 2. Verify a handle — sync fires automatically as a BackgroundTask
#    Check backend logs for:  "sync_handle starting for <id>"
#    After 1–2 minutes:       "sync_handle completed: N submissions synced"

# 3. Dashboard shows spinner banner while sync runs, then auto-updates

# 4. Run tests
cd backend && .venv/bin/python -m pytest -q
# → 67 passed

# 5. Frontend build
cd frontend && npm run build
# → Compiled successfully, 0 TypeScript errors
```

---

## Key Takeaways

- **Celery is optional in dev.** The BackgroundTask fallback lets the sync pipeline run
  without Redis/Celery. In production, Celery provides retries, concurrency, and
  monitoring — the fallback is intentionally dev-only.

- **Blocking I/O in async code kills throughput.** `time.sleep()` inside a
  `BackgroundTask` would have frozen the event loop for every active connection during
  sync. Always use `await asyncio.sleep()` in async contexts.

- **External caches must be optional.** Redis is an optimization (avoid re-fetching
  the CF problemset on every sync). The sync pipeline must be correct without it, and
  it now is — Redis failures are silent no-ops.

- **`last_synced_at IS NULL` is a meaningful state.** A handle can be verified and in
  `sync_status = IDLE` (not yet started) or `IN_PROGRESS` (running). Both mean "no
  data yet." Checking both conditions ensures the banner shows for the full window.

- **Auto-trigger sync on verify.** Requiring a separate manual sync click after
  verification is a friction point. The verify endpoint now starts the sync
  automatically — "verify once, data appears" is the intended UX.

## Next

**Phase 3 — Contest Discovery**: `GET /api/v1/contests` pulling upcoming Codeforces
contests, `/contests` page with a filterable list, countdown timers, and calendar export.
