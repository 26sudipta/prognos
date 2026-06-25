# Phase 3.1 — CLIST Sync Worker + DB

## What Was Built

```
backend/
├── app/
│   ├── models/
│   │   ├── analytics.py          ← Contest ORM model added
│   │   └── __init__.py           ← Contest exported
│   ├── workers/
│   │   ├── clist_sync.py         ← NEW: CLIST sync Celery task
│   │   └── celery_app.py         ← clist-sync beat schedule added
│   └── core/
│       └── config.py             ← CLIST_USERNAME, CLIST_API_KEY added
├── alembic/versions/
│   └── 005_add_contests_table.py ← NEW: contests table migration
├── .env.example                  ← CLIST vars documented
└── tests/
    ├── unit/
    │   └── test_clist_sync.py    ← NEW: 8 unit tests
    └── integration/
        └── test_clist_sync_integration.py ← NEW: 3 integration tests
```

---

## Concepts Explained

### 1. Why a separate `clist_sync.py` instead of adding to `cf_sync.py`

The two sync pipelines are completely independent:
- `cf_sync.py` operates **per-user** (each Codeforces handle gets its own task, runs on cooldown, updates user-specific tables).
- `clist_sync.py` operates **globally** (one task, one table, no user context).

Mixing them would make `cf_sync.py` responsible for two different concerns and make testing harder. Separate modules also let the beat schedules differ (CF every 6h, CLIST every 4h) without any coupling.

### 2. The `Contest` model uses `TimestampMixin`

Unlike the analytics tables (`Submission`, `DailyActivity`, etc.) which are user-owned and never updated once written, `contests` rows are **continuously refreshed** every 4 hours. `TimestampMixin` gives us:

- `created_at` — set once on first insert; the upsert's `ON CONFLICT DO UPDATE` deliberately excludes it.
- `updated_at` — updated on every sync; lets the API report `last_synced_at` for stale-data detection.

The `last_synced_at` column is separate from `updated_at`: it tracks when the CLIST API was queried (a sync-layer concern), while `updated_at` tracks when the row data changed (a DB-layer concern). They will often be identical, but keeping them separate makes each field's meaning unambiguous.

### 3. Upsert on `clist_id`, not on the UUID primary key

CLIST assigns stable integer IDs to contests that persist across their API versions. Using `clist_id` as the upsert key means:

- If a contest's name or time changes (common for late-announced rounds), the row updates in place.
- Our UUID `id` remains stable — the API and any future bookmarks can reference it without breaking.

The migration creates a `UNIQUE` constraint named `uq_contests_clist_id` rather than relying on the primary key because the primary key is UUID (no natural uniqueness relation to CLIST).

### 4. Why the async pattern (asyncio.run + asyncpg) instead of a sync engine

The project only has `asyncpg` installed as the PostgreSQL driver — no `psycopg2`. Rather than add a second driver, the CLIST worker follows the same pattern as `cf_sync.py`: wrap async code in `asyncio.run()` at the Celery task boundary. This means:

- A single DB driver dependency.
- The same connection pool configuration and SSL mode applies.
- Consistent error handling across all workers.

### 5. Graceful degradation

The `_fetch_contests` call is wrapped in a `try/except` at the top of `_run_sync`. On any HTTP error (timeout, 5xx, rate-limit), the function returns `{"status": "skipped", "reason": "api_error"}` and makes **zero DB writes**. The last successfully-synced data stays in the table. The Celery task retries up to 3 times with a 5-minute delay before giving up.

This is different from raising and relying on Celery's retry alone: by catching the error early, the "retaining cached data" behavior is testable in isolation (no Celery machinery needed).

### 6. CLIST datetime strings are naive UTC

CLIST returns ISO strings without timezone info (e.g. `"2026-07-01T10:00:00"`). The `_map_contest` helper converts these to timezone-aware UTC datetimes via `.replace(tzinfo=UTC)` after parsing. If CLIST ever switches to returning `+00:00` offsets, the helper also handles that via the `if dt.tzinfo is not None` branch — no code change needed.

### 7. Window calculation and `limit=200`

The sync window is `now → now + 30 days`. At typical contest density (~5–15 contests/day across all platforms), 30 days × 15 contests = 450 worst-case. Setting `limit=200` covers the realistic case; if a batch ever reaches 200, the log will show it and pagination can be added then. Adding pagination now would be premature.

---

## Verification

```bash
# Apply migration
cd backend
.venv/bin/python -m alembic upgrade head
# Expected: INFO Running upgrade 004 -> 005, add_contests_table

# Confirm table exists
psql prognos -c "\d contests"
# Expected: all columns including clist_id, start_time, last_synced_at

# Run tests
.venv/bin/python -m pytest tests/unit/test_clist_sync.py tests/integration/test_clist_sync_integration.py -v
# Expected: 11 passed

# Full suite
.venv/bin/python -m pytest
# Expected: 78 passed
```

**Manually trigger a CLIST sync** (once CLIST_USERNAME + CLIST_API_KEY are set in `.env`):
```python
# Run from backend/ with venv activated
import asyncio
from app.workers.clist_sync import _run_sync
print(asyncio.run(_run_sync()))
# Expected: {"status": "ok", "upserted": <N>}
```

---

## Key Takeaways

- **Global vs per-user workers** are cleanest in separate modules — coupling them for DRY would create the wrong abstraction boundary.
- **`clist_id` as the upsert key** (not the UUID PK) gives stability: UUID stays constant, CLIST's integer ID drives conflict resolution.
- **Exclude `created_at` from `ON CONFLICT DO UPDATE`** — this one omission preserves the row's original insertion timestamp across unlimited updates.
- **No `psycopg2` needed** — wrapping async code in `asyncio.run()` at the Celery boundary lets both workers share a single DB driver (`asyncpg`).
- **Graceful degradation at the fetch layer** (not the Celery retry layer) makes the "don't touch DB on API error" behavior unit-testable without spinning up a Celery worker.

---

## Next

**Phase 3.2** — Contest API: `GET /contests`, `GET /contests/calendar`, `GET /contests/platforms` endpoints with platform filtering, date-range params, and stale-data detection.
