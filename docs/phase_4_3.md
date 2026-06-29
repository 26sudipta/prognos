# Phase 4.3 — Classroom System: Leaderboard Worker + Cohort Analytics

## What Was Built

```
backend/app/workers/classroom_sync.py     ← Celery tasks for leaderboard rebuild
backend/app/workers/celery_app.py         ← beat schedule + include list
backend/app/workers/cf_sync.py            ← trigger per-classroom rebuild after CF sync
backend/app/services/classroom.py         ← get_cohort_analytics()
```

---

## Concepts Explained

### 1. Pre-Computed Cache: Never Aggregate on Request

The leaderboard is **never** built at request time. A `GET /classrooms/{id}/leaderboard` request reads exactly one table: `classroom_leaderboard`. No joins, no aggregations.

This is the core design invariant:

```
CF sync completes → trigger rebuild_classroom_leaderboard.delay(classroom_id)
Celery beat (hourly) → rebuild_all_classroom_leaderboards()

GET /leaderboard → SELECT * FROM classroom_leaderboard WHERE classroom_id=$1
```

**Why?** A classroom leaderboard with 30 students would require 30 × 5 queries (rating history, streaks, daily activity, solved count, tag stats) at request time — 150+ queries, unbounded latency. Pre-computing shifts this cost to background workers that can fail and retry without affecting the user.

### 2. `asyncio.run()` Inside Celery Tasks

Celery workers run in a synchronous context, but our database code is async (AsyncSession). The bridge is:

```python
@shared_task(bind=True, max_retries=3, default_retry_delay=30)
def rebuild_classroom_leaderboard(self, classroom_id: str) -> dict:
    return asyncio.run(_rebuild_async(uuid.UUID(classroom_id)))
```

Each task invocation creates a fresh event loop (`asyncio.run()`), runs the async pipeline to completion, then exits. This is intentional: Celery tasks are isolated. Sharing an event loop or database session across tasks would cause subtle concurrency bugs.

**Why `bind=True`?** So the task can call `self.retry()` on exceptions. If the rebuild fails (e.g., DB connection timeout), Celery retries up to 3 times with a 30-second delay — without the scheduler having to requeue it.

### 3. Partial Failure: Old Rows Are Preserved

The rebuild handles users with no verified handle gracefully:

```python
async def _build_leaderboard_row(session, classroom_id, user_id):
    # Returns None if no verified handle exists
    handle = await session.scalar(
        select(UserHandle).where(...is_verified=True, is_active=True)
    )
    if not handle:
        return None  # caller logs and skips; old row untouched
```

The rebuild loop:
```python
for member in members:
    try:
        row = await _build_leaderboard_row(session, classroom_id, member.user_id)
        if row is None:
            continue  # skip — preserves old leaderboard row
        # UPSERT row
    except Exception as exc:
        logger.exception("Leaderboard rebuild failed for user %s", member.user_id)
        continue  # partial failure — don't abort the whole classroom
```

**Why preserve instead of delete?** A student who hasn't synced recently still belongs on the leaderboard. Their last-known rating and stats are better than a gap. Only users who have been removed from `classroom_memberships` are pruned:

```python
# After processing all current members:
await session.execute(
    delete(ClassroomLeaderboard).where(
        ClassroomLeaderboard.classroom_id == classroom_id,
        ClassroomLeaderboard.user_id.not_in(member_ids),
    )
)
```

### 4. Per-User Trigger After CF Sync

When a user's CF data is synced, their classrooms should reflect the update immediately (without waiting for the hourly beat):

```python
# In cf_sync.py, after the 5-step pipeline:
async def _trigger_leaderboard_rebuilds(user_id, session):
    from app.workers.classroom_sync import rebuild_classroom_leaderboard
    result = await session.execute(
        select(ClassroomMembership.classroom_id).where(
            ClassroomMembership.user_id == user_id
        )
    )
    for cid in result.scalars().all():
        rebuild_classroom_leaderboard.delay(str(cid))
```

**Why import inside the function?** Circular imports: `classroom_sync.py` imports models; `cf_sync.py` also imports models; importing at the top of `cf_sync.py` creates a circular dependency chain. Deferring to the function call site breaks the cycle cleanly.

**Why `.delay()` and not `.apply()`?** `.delay()` dispatches to the Celery broker and returns immediately. The sync endpoint doesn't wait for the leaderboard rebuild — that's acceptable latency for a cache refresh.

### 5. Cohort Analytics: JSONB-Only Aggregation

`get_cohort_analytics()` reads only `classroom_leaderboard` rows and aggregates in Python:

```python
neglected_counter = Counter()
for entry in entries:
    for wt in (entry.weak_tags or []):
        if wt["signal_type"] == "neglected":
            neglected_counter[wt["tag"]] += 1

most_neglected = [CohortTag(tag=t, count=c) for t, c in neglected_counter.most_common(5)]
```

**Why Python aggregation instead of SQL?** The `weak_tags` data is inside JSONB arrays — unnesting them in SQL is verbose and PostgreSQL-specific. Since the classroom leaderboard is at most a few hundred rows, Python `Counter` is fast and readable. No premature optimization.

### 6. Beat Schedule

```python
"rebuild-all-leaderboards": {
    "task": "app.workers.classroom_sync.rebuild_all_classroom_leaderboards",
    "schedule": crontab(minute=0),  # every hour, on the hour
}
```

The beat task queries all active classrooms and dispatches individual `rebuild_classroom_leaderboard` tasks — one per classroom. This keeps each rebuild isolated: one classroom's slow data doesn't block another's.

---

## Verification

```bash
cd backend

# Manually trigger a rebuild
.venv/bin/python -c "
from app.workers.classroom_sync import rebuild_classroom_leaderboard
result = rebuild_classroom_leaderboard.apply(args=['<paste-classroom-uuid>'])
print(result.result)
"

# Then check the leaderboard
curl -H "Authorization: Bearer <token>" \
  http://localhost:8000/api/v1/classrooms/<id>/leaderboard
# Expected: { entries: [...], computed_at: "<timestamp>" }
```

---

## Key Takeaways

- Pre-computed caches are the only correct pattern for leaderboards at scale. Never aggregate on request.
- `asyncio.run()` in Celery is the standard bridge — one fresh event loop per task.
- Partial failure in a batch job should log-and-continue, never abort. Old rows are safer than gaps.
- Import inside function body breaks circular import cycles cleanly.
- JSONB aggregation in Python is fast enough for classroom-scale data; no need for SQL `jsonb_array_elements`.

---

**Next:** Phase 4.4 — Frontend classroom pages.
