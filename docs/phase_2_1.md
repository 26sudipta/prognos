# Phase 2.1 — Celery + CF Sync Worker
**Status:** DONE  
**Date:** 2026-06-24  
**Goal:** Build the data collection engine — a background worker that fetches every submission a user has made on Codeforces, stores it in the database, and computes derived analytics tables ready for instant reads. Also includes the weakness detection and recommendation generation pipelines that run automatically at the end of every sync.

---

## What Was Built

```
backend/
├── app/
│   ├── models/
│   │   ├── analytics.py          ← NEW: Submission, SubmissionTag, DailyActivity, TagStats, RatingHistory
│   │   ├── signals.py            ← NEW: WeaknessSignal, RecommendationSet, Recommendation
│   │   └── __init__.py           ← UPDATED: exports all 8 new models so Alembic sees them
│   ├── workers/
│   │   ├── celery_app.py         ← NEW: Celery instance, Redis broker config, beat schedule
│   │   └── cf_sync.py            ← NEW: full 6-step sync pipeline
│   ├── schemas/
│   │   └── handle.py             ← UPDATED: SyncResponse added
│   ├── services/
│   │   └── handle.py             ← UPDATED: get_handle_for_user helper added
│   └── api/v1/routes/
│       └── handles.py            ← UPDATED: POST /handles/{id}/sync endpoint
├── alembic/versions/
│   └── 003_add_analytics_tables.py  ← NEW: 8 tables + weakness_signal_type enum
└── tests/
    ├── unit/
    │   └── test_weakness_signals.py   ← NEW: 5 unit tests (all 3 signal rules)
    └── integration/
        └── test_sync_endpoint.py      ← NEW: 7 integration tests (cooldown, ownership)
```

---

## Concepts Explained

### 1. What Is a Task Queue and Why Do We Need One?

**The problem:** When a user clicks "Sync Now", the backend needs to:
1. Call the Codeforces API (paginated — up to 20+ HTTP requests for active users)
2. Wait 2 seconds between each page (CF rate limit)
3. Insert thousands of rows into the DB
4. Recompute 4 derived tables
5. Generate recommendations via another CF API call

This can take **30–90 seconds**. A FastAPI route handler cannot do this work directly — the HTTP request would time out, and more importantly, the web server process would be locked doing sync work instead of handling other users' requests.

**The solution: a task queue.**

```
User clicks "Sync Now"
        ↓
HTTP POST /handles/{id}/sync   (returns immediately, ~5ms)
        ↓
Celery receives task message from Redis
        ↓
Celery worker (separate process) executes the 90-second job
        ↓
Result stored in DB, no HTTP connection involved
```

The web server and the worker are **completely separate processes**. The web server just drops a message into Redis ("hey, sync handle X") and immediately responds to the user. The worker picks it up and does the actual work in the background.

---

### 2. What Is Celery?

Celery is a Python library for running background tasks. It has three parts:

| Part | What it does | Our config |
|---|---|---|
| **Producer** | Web server code that creates tasks | FastAPI routes calling `.delay()` |
| **Broker** | Message queue where tasks wait | Redis (`REDIS_URL`) |
| **Worker** | Process that executes tasks | Separate `celery worker` process |

When you call `sync_handle.delay(handle_id)`, Celery serializes the arguments to JSON, pushes them into Redis, and returns a task ID immediately. The worker process (running separately) pulls the message from Redis and calls the actual function.

**Our Celery config (`celery_app.py`):**
```python
celery_app = Celery(
    "prognos",
    broker=settings.REDIS_URL,    # where tasks are queued
    backend=settings.REDIS_URL,   # where results are stored
    include=["app.workers.cf_sync"],  # which files contain tasks
)
```

`include` tells Celery where to find `@shared_task` decorated functions. Without it, the worker process doesn't know the tasks exist.

---

### 3. What Is Redis?

Redis is an in-memory key-value store. It's extremely fast (microsecond reads/writes) because everything lives in RAM, not on disk.

We use Redis for two completely different purposes in this phase:

| Use | Key pattern | TTL | What's stored |
|---|---|---|---|
| Celery broker | Internal Celery keys | Auto-managed by Celery | Task messages (JSON-serialized function arguments) |
| CF problemset cache | `cf:problemset:all` | 6 hours | JSON list of all ~9000 CF problems |

**Why cache the CF problemset in Redis?**  
The Codeforces `/problemset.problems` API returns all ~9000 problems in one call. We need this to generate recommendations. Fetching it on every sync would be wasteful and slow. Redis lets us fetch it once and reuse it for 6 hours across all workers and all users.

```python
cached = await r.get(CF_PROBLEMSET_CACHE_KEY)
if cached:
    return json.loads(cached)          # ← instant, from RAM

problems = await _cf_get(client, "problemset.problems")  # ← one network call
await r.set(CF_PROBLEMSET_CACHE_KEY, json.dumps(problems), ex=3600 * 6)
```

---

### 4. What Is Celery Beat?

Celery Beat is a scheduler that runs inside the Celery process and fires tasks on a time-based schedule — like cron, but integrated with Celery.

**Our schedule:**
```python
celery_app.conf.beat_schedule = {
    "cf-sync-all-handles": {
        "task": "app.workers.cf_sync.sync_all_handles",
        "schedule": crontab(minute=0, hour="*/6"),   # every 6 hours
    },
}
```

`sync_all_handles` queries the DB for every verified, active handle and calls `sync_handle.delay(handle_id)` for each one. So even without any user manually triggering a sync, every handle gets refreshed automatically.

**To run beat locally:**
```bash
# Terminal 1: the worker
.venv/bin/celery -A app.workers.celery_app worker --loglevel=info

# Terminal 2: the scheduler
.venv/bin/celery -A app.workers.celery_app beat --loglevel=info
```

Beat must run as a separate process — it's only responsible for enqueueing tasks on schedule; the worker does the actual execution.

---

### 5. The Problem: Celery Tasks Are Synchronous, Our Code Is Async

FastAPI uses `async`/`await` (Python's async model). Celery tasks, by default, are regular synchronous functions.

Our sync pipeline uses `AsyncSession` (async SQLAlchemy) and `httpx.AsyncClient` — both require an event loop to run.

**The bridge: `asyncio.run()`**

```python
@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def sync_handle(self, handle_id: str) -> dict:
    # sync_handle is a regular function — Celery calls it like a normal function
    # but we need async code inside, so we create a fresh event loop:
    return asyncio.run(_sync_handle_async(uuid.UUID(handle_id)))
```

`asyncio.run()` creates a new event loop, runs the async function to completion, then closes the loop. It's the correct way to call async code from a synchronous context.

**Why not make the Celery task itself `async`?**  
Celery has experimental async support, but it requires special configuration and is fragile across versions. Using `asyncio.run()` is the battle-tested approach and works with all Celery versions.

---

### 6. The Database Schema — 8 New Tables

These tables form two categories:

**Raw data (source of truth):**

| Table | Purpose | Key constraint |
|---|---|---|
| `submissions` | One row per CF submission | `UNIQUE(cf_submission_id)` — CF IDs never repeat |
| `submission_tags` | Problem tags for each submission | No unique constraint — a problem can have 3 tags |

**Derived data (pre-computed for fast reads):**

| Table | Computed from | Refresh strategy |
|---|---|---|
| `daily_activity` | `submissions` grouped by UTC date | Full recompute per user on each sync |
| `tag_stats` | `submissions` + `submission_tags` grouped by tag | Full recompute per user on each sync |
| `rating_history` | CF `user.rating` API | Full recompute per user on each sync |

**Intelligence layer:**

| Table | Purpose |
|---|---|
| `weakness_signals` | Identified weak tags with type + score + reason |
| `recommendation_sets` | Header record grouping a batch of recommendations |
| `recommendations` | One problem per weak tag, up to 5 per set |

**Why store `SubmissionTag` separately instead of an array column in `Submission`?**  
A PostgreSQL array column (`tags TEXT[]`) cannot be efficiently queried or joined. `SELECT * FROM submissions WHERE 'dp' = ANY(tags)` works but is slow on large tables and can't use a standard B-tree index.

A separate `submission_tags` table with an index on `submission_id` allows:
- Efficient join: `JOIN submission_tags ON submission_tags.submission_id = s.id`
- Future: index on `tag` to quickly find all submissions for a tag across users
- Aligns with relational normal form — no repeating groups inside a row

---

### 7. Incremental Sync — The Cursor Strategy

Fetching all submissions every time would be wasteful. A user with 2000 submissions would trigger thousands of DB inserts on every 6-hour sync, even though only 5 new ones exist.

**The cursor:** `max(cf_submission_id)` stored in the DB.

```python
result = await session.execute(
    select(Submission.cf_submission_id)
    .where(Submission.user_handle_id == handle_id)
    .order_by(Submission.cf_submission_id.desc())
    .limit(1)
)
max_id = result.scalar_one_or_none() or 0
```

CF submission IDs are **monotonically increasing integers** — each new submission gets an ID larger than all previous ones. This is guaranteed by Codeforces' internal counter.

**Why integer ID cursor, not timestamp?**

| Approach | Problem |
|---|---|
| Timestamp cursor | CF API returns Unix timestamps (seconds). Multiple submissions in the same second → ambiguous boundary. Timezone bugs. Rounding errors. |
| Integer ID cursor | `submissionId > max_id` is unambiguous. No floating-point math, no timezone conversion. |

**First sync:** `max_id = 0`, so `submissionId > 0` matches everything — full historical fetch.  
**Subsequent syncs:** Only the delta since last sync is fetched.

The CF API accepts pagination params (`from`, `count`) and returns submissions in reverse chronological order. We stop pagination as soon as we encounter a submission ID ≤ `max_id`.

---

### 8. PostgreSQL UPSERT — `ON CONFLICT DO NOTHING` vs `ON CONFLICT DO UPDATE`

Two different upsert strategies are used for different reasons:

**`ON CONFLICT DO NOTHING` — for submissions:**
```python
stmt = pg_insert(Submission).values(...).on_conflict_do_nothing(
    index_elements=["cf_submission_id"]
)
```
CF submissions are **immutable once made** (a submission's code/verdict is permanent). If we try to insert a submission that already exists — just skip it silently. No update needed.

**`ON CONFLICT DO UPDATE` — for derived tables:**
```python
# daily_activity example
INSERT INTO daily_activity (...) VALUES (...)
ON CONFLICT (user_handle_id, activity_date) DO UPDATE
    SET submission_count = EXCLUDED.submission_count,
        solved_count = EXCLUDED.solved_count
```
Derived tables are **recomputed from scratch** — their values can change if, say, a CF admin reverts a verdict. `DO UPDATE` overwrites the old row with the new computed value.

`EXCLUDED` is a PostgreSQL special pseudo-table that refers to the row that *would have been inserted* if the conflict hadn't happened. `EXCLUDED.submission_count` means "the new value we tried to insert."

---

### 9. Why the Sync Pipeline Has a Strict Order

```python
await _fetch_submissions(...)        # Step 1: populate submissions table
await _recompute_daily_activity(...) # Step 2: depends on submissions
await _recompute_tag_stats(...)      # Step 3: depends on submissions + submission_tags
await _upsert_rating_history(...)    # Step 4: independent CF API call
await _compute_weakness_signals(...) # Step 5: depends on tag_stats
await _generate_recommendations(...) # Step 6: depends on weakness_signals + rating_history
```

This is a **DAG (Directed Acyclic Graph)** of dependencies:

```
submissions ──→ daily_activity
      ↓
submission_tags ──→ tag_stats ──→ weakness_signals ──→ recommendations
                                          ↑
                         rating_history ──┘
```

If you ran step 5 before step 3, `weakness_signals` would be computed from stale `tag_stats`. The pipeline order enforces correctness.

**Why not use transactions across steps?**  
Each step issues its own `await session.commit()`. We commit after each step rather than batching all 6 into one transaction because:
1. Some steps take several seconds — holding a long transaction locks the tables
2. If step 4 fails (CF API down), steps 1–3 are already durable and don't need to rerun
3. This is more memory-efficient — SQLAlchemy's identity map doesn't accumulate thousands of ORM objects

---

### 10. Weakness Signal Detection — The Three Rules

After `tag_stats` is populated, we evaluate three rules in priority order (`if/elif/elif`):

```python
if row.solved_count >= 1 and row.last_activity_at < neglect_threshold:
    # NEGLECTED
elif row.attempt_count >= 5 and row.acceptance_rate < 0.50:
    # LOW_SUCCESS
elif row.solved_count < 5:
    # UNDER_PRACTICED
```

**Why `if/elif/elif` (mutually exclusive)?**  
A tag can satisfy multiple conditions simultaneously. For example, a tag with `solved_count=2, attempt_count=8, acceptance_rate=0.25` satisfies both `low_success` and `under_practiced`. Using `if/elif` means only one signal fires — the one with the highest priority.

This prevents duplicate recommendations for the same tag from different signals.

**Priority reasoning:**

| Priority | Signal | Reasoning |
|---|---|---|
| 1st | `neglected` | User learned the topic but stopped practicing → most impactful to re-engage |
| 2nd | `low_success` | User is actively attempting but failing → needs targeted practice |
| 3rd | `under_practiced` | Baseline catch-all for untouched topics |

**Score formulas and what they mean:**

| Signal | Formula | Range | Intuition |
|---|---|---|---|
| `neglected` | `min(days_since / 14, 5.0)` | 1.0–5.0 | The longer the gap, the higher the urgency; capped at 5 |
| `low_success` | `3.0 × (1 − acceptance_rate)` | 0.0–3.0 | 0% acceptance → score 3.0; 40% acceptance → score 1.8 |
| `under_practiced` | `1.0 + (5 − solved) × 0.4` | 1.0–3.0 | 0 solved → 3.0; 4 solved → 1.4 |

Scores are on the same scale and are used to rank weak tags for recommendations.

---

### 11. Recommendation Algorithm — Problem Selection

```
1. Sort all weakness signals by score descending
2. Deduplicate: take highest-score signal per tag
3. Take top 5 tags
4. For each tag:
   a. Search the CF problemset for a problem where:
      - tag matches
      - difficulty in [user_rating − 100, user_rating + 300]
      - not already solved by this user
   b. If no match: expand band to [user_rating − 200, user_rating + 600], retry once
   c. If still no match: skip this tag
5. Return 1 problem per tag, max 5 total
```

**Why is the difficulty band asymmetric `[−100, +300]`?**

A user rated 1500 solving a 1400-rated problem builds confidence without being trivial. The same user attempting a 1900-rated problem (+400) is productive stretch. But a 2200-rated problem (+700) is likely unsolvable and discouraging.

The band is not centered because competitive programming difficulty perception is asymmetric — slightly below is warmup, far above is frustrating, slightly above is the sweet spot.

**User rating source:**  
The user's current rating is read from the latest entry in `rating_history.new_rating`. If the user has never participated in a rated contest (empty rating_history), we default to `1200` — Codeforces' initial rating for new users.

**Already-solved exclusion:**
```python
solved_result = await session.execute(
    select(Submission.problem_id)
    .where(Submission.user_handle_id == handle_id, Submission.verdict == "OK")
    .distinct()
)
solved_ids = set(solved_result.scalars().all())
```

`problem_id` is stored as `"{contestId}{index}"` (e.g., `"1234A"`). The exclusion set is built once before the loop, not re-queried per tag — O(n) total instead of O(n × tags).

---

### 12. Manual Sync Cooldown — Race Condition Protection

`POST /handles/{id}/sync` enforces a 30-minute cooldown to prevent users from hammering the CF API.

**The race condition:**  
Without protection, two simultaneous requests for the same handle would both pass the cooldown check and both enqueue tasks.

```
Request A: check cooldown → passes → (context switch)
Request B: check cooldown → passes → enqueue task B
Request A: (resumes)     → enqueue task A
→ Two syncs running simultaneously for the same user
```

**The fix:** Write `last_manual_sync_at` to the DB and `await db.commit()` **before** enqueuing the task:

```python
handle.last_manual_sync_at = datetime.now(UTC)
await db.commit()           # ← atomic write to DB

task = sync_handle.delay(str(handle_id))   # ← only after commit
```

Now if two requests race:
- Request A commits `last_manual_sync_at`
- Request B reads the row, sees the timestamp, fails the cooldown check → 429

The DB commit is the synchronization point. This works because PostgreSQL row-level locking ensures only one writer wins.

**429 response includes `retry_after_seconds`:**
```python
retry_after = int((handle.last_manual_sync_at + cooldown - datetime.now(UTC)).total_seconds())
raise HTTPException(
    status_code=429,
    detail={"message": "Sync cooldown active", "retry_after_seconds": retry_after},
)
```
The frontend can use `retry_after_seconds` to show a countdown timer ("Sync available in 18 minutes").

---

### 13. Sync Status on the Handle

`user_handles.sync_status` is an enum: `idle | in_progress | completed | sync_error`

This is separate from task state (which Celery tracks internally) because:
1. The frontend needs to show sync status without querying Celery
2. Celery task results expire from Redis; the DB state is permanent

The worker updates `sync_status` at two points:
```python
# Beginning of sync
handle.sync_status = HandleSyncStatus.IN_PROGRESS
await session.commit()

# End of sync (success)
handle.sync_status = HandleSyncStatus.COMPLETED
handle.last_synced_at = datetime.now(UTC)
handle.last_sync_error = None

# End of sync (failure)
handle.sync_status = HandleSyncStatus.SYNC_ERROR
handle.last_sync_error = str(exc)[:500]   # truncated to fit column
```

The `try/except` in `_sync_handle_async` guarantees that even if step 3 fails, the status is updated to `SYNC_ERROR` — the handle never gets stuck permanently in `IN_PROGRESS`.

---

### 14. `bind=True` and Celery Task Retries

```python
@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def sync_handle(self, handle_id: str) -> dict:
    try:
        return asyncio.run(_sync_handle_async(uuid.UUID(handle_id)))
    except Exception as exc:
        raise self.retry(exc=exc)
```

`bind=True` gives the task access to `self` — the task instance. This is needed to call `self.retry()`.

`self.retry(exc=exc)` tells Celery: re-enqueue this task after `default_retry_delay` seconds (60 seconds here), up to `max_retries` times (3 times). If all retries are exhausted, the exception propagates and the task enters the `FAILURE` state.

**Why retry?** CF's API occasionally returns 503 or times out. A transient failure shouldn't permanently leave a user's data unsynced. Automatic retry handles this transparently.

---

## Verification

```bash
cd backend

# 1. Confirm migration applied
.venv/bin/python -m alembic current
# → 003 (head)

# 2. Confirm all 8 tables exist in the database
psql prognos -c "\dt"
# Should include: submissions, submission_tags, daily_activity, tag_stats,
#                 rating_history, weakness_signals, recommendation_sets, recommendations

# 3. Run Phase 2.1 tests only
.venv/bin/python -m pytest tests/unit/test_weakness_signals.py tests/integration/test_sync_endpoint.py -v
# Expected: 12 passed

# 4. Run full test suite — verify no regressions
.venv/bin/python -m pytest -v
# Expected: 42 passed

# 5. Confirm Celery can import tasks (requires Redis running)
.venv/bin/python -c "from app.workers.celery_app import celery_app; print(celery_app.tasks.keys())"
# Should include: app.workers.cf_sync.sync_handle, app.workers.cf_sync.sync_all_handles

# 6. Start the worker locally (requires Redis on localhost:6379)
.venv/bin/celery -A app.workers.celery_app worker --loglevel=info

# 7. Start the beat scheduler (separate terminal)
.venv/bin/celery -A app.workers.celery_app beat --loglevel=info

# 8. Manually trigger a sync for a verified handle (replace UUID)
.venv/bin/python -c "
from app.workers.cf_sync import sync_handle
result = sync_handle.delay('your-handle-uuid-here')
print('Task ID:', result.id)
"
```

---

## Key Takeaways

1. **Task queue = web server and slow work are decoupled.** The web server returns immediately; Celery does the slow work in a separate process.
2. **Redis serves two roles:** Celery message broker AND problemset cache. Same service, different keyspaces.
3. **`asyncio.run()` bridges sync Celery tasks to async SQLAlchemy/httpx code.** Celery is synchronous by default; we wrap async logic with `asyncio.run()`.
4. **Integer submission ID cursor > timestamp cursor.** Monotonically increasing IDs are unambiguous; timestamps have edge cases.
5. **Derived tables are fully recomputed each sync.** Simpler logic, handles verdict changes on CF, no partial-update bugs.
6. **`ON CONFLICT DO NOTHING` for raw data, `DO UPDATE` for derived data.** Raw submissions are immutable; derived stats must be overwritten.
7. **Pipeline order matters.** Weakness signals depend on tag_stats; recommendations depend on both weakness_signals and rating_history. Step order is not arbitrary.
8. **Commit before enqueue.** The DB write is the race-condition barrier for the manual sync cooldown.
9. **`bind=True` + `self.retry()`** gives automatic retry on transient CF API failures — up to 3 attempts, 60s apart.

---

## Updates

### 2026-06-30 — Dashboard went blank after handle re-verify (zero submissions, rating still shown)

**Symptom.** After unlinking and re-verifying the same Codeforces handle, the dashboard
showed `total_solved=0`, `current_streak=0`, an empty heatmap, and Insights had no focus
areas — **but** CF rating (979, 12 contests) and (stale) recommendations still rendered.

**Diagnosis.** Analytics reads 100% from the DB, keyed on the user's *active + verified*
handle (`_get_handle_ids`). A sync has two independent pipelines: **submissions**
(`user.status` → `submissions` → recomputes `daily_activity`, `tag_stats`) and **rating**
(`user.rating` → `rating_history`). Because the derived tables are recomputed from
`submissions` every sync, an empty heatmap + 0 solved proves `submissions` was empty for
the active handle, while the independent `user.rating` call still populated rating.

**Root cause — a GLOBAL unique on `submissions.cf_submission_id`.** Re-verifying creates a
*new* `user_handles` row (unlink only soft-deletes the old one). The new handle's sync
re-fetches the same submissions from Codeforces — but `submissions.cf_submission_id` had a
**global** `UNIQUE` (migration 003), and the insert used
`ON CONFLICT (cf_submission_id) DO NOTHING`. Every id already existed under the old handle,
so every insert was a **no-op → 0 rows stored under the active handle**. The derived tables
recompute from those (zero) rows → blank dashboard. `_fetch_submissions` even *returned*
the fetched count (~hundreds) while storing nothing, hiding it.

Rating was immune because `rating_history`'s conflict key is **composite**
`(user_handle_id, cf_contest_id)` (migration 004) — so the same contest stores once per
handle. That asymmetry is exactly why rating showed but submissions didn't. (The public CF
API returns this user's submissions fine — confirmed via `user.status?handle=Sudipta_Das` —
so nothing was wrong upstream; the writes were silently dropped by the constraint.)

**Fixes:**

| Area | Change | Why |
|---|---|---|
| **migration 007 + `models/analytics.py`** | Drop the global `UNIQUE(cf_submission_id)`; add composite **`UNIQUE(user_handle_id, cf_submission_id)`** | **The load-bearing fix.** Each handle stores its own submissions; cross-handle re-fetch no longer no-ops |
| `workers/cf_sync.py` `_fetch_submissions` | Conflict target → `(user_handle_id, cf_submission_id)`; post-insert id lookup scoped by handle; return the **stored** count (not fetched) | Matches the new constraint; `scalar_one()` would break once ids aren't globally unique; honest count |
| `services/handle.py` `initiate_verification` | Re-verifying a handle the user previously unlinked now **reactivates and reuses the dormant row** (same `id`) instead of creating a new one | Avoids row proliferation + a needless full re-fetch; re-verify is self-healing |
| `workers/cf_sync.py` `_cf_get` | Remap `from_` → **`from`** (CF's real param name); retry/backoff on `429`/`5xx`/transport errors **and** on CF's `HTTP 200 + status=FAILED + "limit exceeded"** | `from_` was ignored by CF, so pagination past 500 silently refetched page 1; and CF signals rate-limiting as a 200/FAILED body, which previously aborted the whole sync with no retry |
| `workers/cf_sync.py` `_sync_handle_async` | If a handle ends a sync with **0 submissions but rated contests**, record it in `last_sync_error` and log a warning | Stops a silent-zero sync from looking "COMPLETED & fine"; next cron run retries |
| `workers/cf_sync.py` `_recompute_tag_stats` | Add `DELETE` before the upsert (parity with `_recompute_daily_activity`) | Stale tags could otherwise linger when submissions shrink and feed bogus weakness signals |
| `api/.../handles.py` `manual_sync` | Add owner-only `?force=true` to bypass the 30-min cooldown | Lets a user immediately re-sync to recover missing data |

**Recovery for already-affected accounts (in order):**
1. Deploy — migration 007 runs at container start, swapping the unique constraint.
2. Force a full re-sync of the active handle: `POST /handles/{id}/sync?force=true`. With the
   composite key, the re-fetched submissions now insert under the active handle (no global
   collision with the old row), and all derived tables recompute → dashboard fills.
   *(Alternative, no re-fetch: `UPDATE submissions SET user_handle_id='<active>' WHERE
   user_handle_id='<old>'` then resync to recompute.)*

**Verification:** `pytest` → full suite green, including new regression tests:
`test_submissions_unique.py` (same CF submission id stores under two handle rows; same-handle
dup is a no-op), the `from`-param remap, the 200/FAILED rate-limit retry, and
reactivate-dormant-row on re-verify.

---

## Next: Phase 2.2 — Analytics API
Build 3 read endpoints that serve pre-computed data directly from the derived tables:
- `GET /api/v1/analytics/dashboard` — heatmap (365 days), current/longest streak, total solved, CF rating
- `GET /api/v1/analytics/tags` — full tag stats table
- `GET /api/v1/analytics/rating-history` — rating trend over time
