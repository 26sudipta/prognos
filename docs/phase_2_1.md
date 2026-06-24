# Phase 2.1 — Celery + CF Sync Worker

## What Was Built

```
backend/
├── app/
│   ├── models/
│   │   ├── analytics.py          ← NEW: Submission, SubmissionTag, DailyActivity, TagStats, RatingHistory
│   │   ├── signals.py            ← NEW: WeaknessSignal, RecommendationSet, Recommendation
│   │   └── __init__.py           ← UPDATED: exports all new models
│   ├── workers/
│   │   ├── celery_app.py         ← NEW: Celery instance + beat schedule (every 6 hours)
│   │   └── cf_sync.py            ← NEW: full sync pipeline (fetch → derive → signals → recs)
│   ├── schemas/
│   │   └── handle.py             ← UPDATED: SyncResponse schema added
│   ├── services/
│   │   └── handle.py             ← UPDATED: get_handle_for_user helper added
│   └── api/v1/routes/
│       └── handles.py            ← UPDATED: POST /handles/{id}/sync endpoint
├── alembic/versions/
│   └── 003_add_analytics_tables.py  ← NEW: 8 tables + 1 enum in one migration
└── tests/
    ├── unit/
    │   └── test_weakness_signals.py      ← NEW: 5 unit tests
    └── integration/
        └── test_sync_endpoint.py         ← NEW: 7 integration tests
```

---

## Concepts Explained

### 1. Why Celery with Redis (not FastAPI background tasks)

FastAPI's `BackgroundTasks` run in the same process as the web server. A full CF sync for an active user can take 30–60 seconds (multiple paginated API calls with mandatory 2-second sleeps for CF rate limiting). Tying up a web worker for that duration under load would exhaust the worker pool.

Celery tasks run in a completely separate worker process, communicate via Redis as the message broker, and can be retried independently if they fail. This also enables the Celery beat scheduler to fire syncs automatically every 6 hours without any HTTP request triggering them.

### 2. Incremental Sync Strategy

Each run fetches only submissions newer than `max(cf_submission_id)` stored in the DB:

```python
result = await session.execute(
    select(Submission.cf_submission_id)
    .where(Submission.user_handle_id == handle_id)
    .order_by(Submission.cf_submission_id.desc())
    .limit(1)
)
max_id = result.scalar_one_or_none() or 0
```

CF submission IDs are monotonically increasing integers. Once we have seen ID N, all IDs < N are either already stored or were submitted before we started tracking. This means the first sync is a full fetch; all subsequent syncs transfer only the delta.

**Why not timestamp-based?** Timestamps have edge cases (timezone bugs, CF API returning Unix seconds with rounding). Integer IDs are unambiguous.

### 3. Derived Tables — No Aggregation on Read

The architecture rule ("frontends read pre-computed data, never aggregate on request") means all dashboard numbers are computed by the sync worker and stored in flat rows:

| Raw table | Derived table | Computation |
|---|---|---|
| `submissions` | `daily_activity` | GROUP BY UTC date, COUNT(*), COUNT(*) FILTER OK |
| `submissions` + `submission_tags` | `tag_stats` | GROUP BY tag, solved/attempt counts, acceptance_rate |
| CF rating API | `rating_history` | Direct upsert from `user.rating` endpoint |

The `daily_activity` and `tag_stats` tables are fully rebuilt on every sync (`DELETE WHERE user_handle_id = X` then reinsert via `INSERT ... ON CONFLICT DO UPDATE`). This is correct because a submission's verdict might change on CF (rare but documented), and it keeps the logic simple.

### 4. Weakness Signal Rules

Three signal types, evaluated as mutually exclusive `if/elif/elif`:

| Signal | Condition | Score formula |
|---|---|---|
| `neglected` | solved ≥ 1 AND last_activity < 14 days ago | min(days_since / 14, 5.0) |
| `low_success` | attempts ≥ 5 AND acceptance < 50% | 3.0 × (1 − acceptance_rate) |
| `under_practiced` | solved < 5 | 1.0 + (5 − solved) × 0.4 |

The `if/elif/elif` means a tag can only generate one signal. Priority: neglected > low_success > under_practiced. This prevents double-counting a tag that is both neglected and under-practiced.

Scores are comparable across types — higher score = higher priority for recommendations.

### 5. Recommendation Algorithm

```
Top 5 weakness tags (by score) →
  For each tag: search CF problemset (cached in Redis)
    Filter: tag matches + rating in [user_rating−100, user_rating+300] + not already solved
    If no match: expand band to ±200 and retry once
  → 1 problem per tag, max 5 total
```

The CF problemset (all ~9000 problems) is fetched once and cached in Redis for 6 hours. This avoids hammering the CF API on every sync. The cache key is `cf:problemset:all`.

The difficulty band `[rating−100, rating+300]` is intentionally asymmetric — problems slightly below the user's rating are confidence-builders; problems well above are stretch goals.

### 6. Manual Sync Cooldown

`POST /handles/{id}/sync` returns 429 if `last_manual_sync_at` is within 30 minutes. The timestamp is written to DB **before** the task is enqueued, so concurrent HTTP requests in the same window are also blocked.

```python
handle.last_manual_sync_at = datetime.now(UTC)
await db.commit()           # ← commits before task dispatch

task = sync_handle.delay(str(handle_id))
```

This prevents double-sync even if the client fires two requests simultaneously.

---

## Verification

```bash
# Run tests
cd backend
.venv/bin/python -m pytest tests/unit/test_weakness_signals.py tests/integration/test_sync_endpoint.py -v
# Expected: 12 passed

# Run full suite (no regressions)
.venv/bin/python -m pytest -v
# Expected: 42 passed

# Check DB migration applied
.venv/bin/python -m alembic current
# Expected: 003 (head)

# Check new tables exist
psql prognos -c "\dt"
# Should include: submissions, submission_tags, daily_activity, tag_stats,
#                 rating_history, weakness_signals, recommendation_sets, recommendations

# Start Celery worker (requires Redis running on localhost:6379)
.venv/bin/celery -A app.workers.celery_app worker --loglevel=info

# Start Celery beat (separate terminal)
.venv/bin/celery -A app.workers.celery_app beat --loglevel=info
```

---

## Key Takeaways

- Derived tables (`daily_activity`, `tag_stats`) are fully recomputed on each sync — simplicity over partial updates.
- CF submission IDs are the sync cursor — integer comparison is unambiguous and index-friendly.
- The CF problemset cache in Redis prevents per-sync API calls for recommendations.
- The sync cooldown timestamp is committed before task dispatch to handle concurrent requests.
- Weakness signals use mutually exclusive `if/elif/elif` — one signal per tag, priority order: neglected → low_success → under_practiced.

## Next

→ Phase 2.2 — Analytics API: 3 read endpoints (`/analytics/dashboard`, `/analytics/tags`, `/analytics/rating-history`)
