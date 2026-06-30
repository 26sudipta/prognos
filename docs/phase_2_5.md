# Phase 2.5 — Phase 2 QA Audit

## What Was Fixed

This was a full line-by-line audit of every Phase 2 deliverable against `requirement.md` and `implementation.md` before moving to Phase 3. No new features were added — only correctness bugs and spec deviations were addressed.

**Files changed:** 9 backend files, 4 frontend files, 1 new migration (`004_add_missing_constraints.py`)

---

## Concepts Explained

### 1. Streak Grace-Day Was Missing (Critical)

**Before:** `_compute_streaks()` counted from today. If a user hadn't solved anything yet today, today's zero broke their streak.

**After:**
```python
start_date = date.today() - timedelta(days=1) if date_to_solved.get(today, 0) == 0 else today
```

The requirement (§D.2) explicitly states a grace day: if today has 0 solved, the streak is measured from yesterday. A user who solves daily and hasn't solved yet today should not see their streak reset to 0.

**Why this is hard to catch in tests:** A test that checks streak always runs at some point during the day. If seeded data doesn't include "today" explicitly, the test passes for the wrong reason. The fix required an explicit test case: `today=0, yesterday=5, day-2=5 → current_streak=2`.

### 2. `POST /analytics/recommendations/refresh` Was Never Built (High)

The endpoint was in `requirement.md` and `implementation.md` but was skipped during Phase 2.3. It was added in this audit:

```python
@router.post("/analytics/recommendations/refresh")
async def refresh_recommendations(user: User = Depends(get_current_user), ...):
    await refresh_recommendation_set(db, user)
    return await get_recommendations(db, user)
```

The service calls the same `_pick_problem()` pipeline that runs after CF sync, but on demand. No cooldown — the user can refresh whenever they want.

### 3. `noHandleLinked()` False-Positive (High)

**Before:** The frontend detected "no handle" by checking `total_solved === 0 && cf_rating === null`. This is wrong: a user with a verified handle who has only Wrong Answer submissions has `total_solved=0` but IS linked.

**After:** Backend added `has_verified_handle: bool` to `DashboardResponse`:
```python
has_verified_handle: bool = await _has_verified_handle(db, user.id)
```

Frontend reads this directly instead of proxying from data values.

### 4. Missing Unique Constraints on Two Tables (Medium)

`rating_history` had no unique constraint — if a CF sync ran twice without deduplication, the same contest could appear twice. Same for `weakness_signals`. Migration 004 added:

```sql
UNIQUE(user_handle_id, cf_contest_id)              -- rating_history
UNIQUE(user_handle_id, tag, signal_type)           -- weakness_signals
```

The `on_conflict_do_nothing()` upsert in the sync worker was also missing `index_elements` — without them, PostgreSQL doesn't know which constraint to check. Fixed to:
```python
insert(...).on_conflict_do_nothing(index_elements=["user_handle_id", "cf_contest_id"])
```

### 5. Difficulty Band Clamping (Low)

`_pick_problem()` was computing `low = cf_rating - 200` / `high = cf_rating + 300` without bounds. For a 900-rated user: `low=700`, which is below CF's minimum difficulty of 800. Problems in that range don't exist and the recommendation would always be empty. Fixed with `max(800, low)` and `min(3500, high)`.

### 6. Handle Verification Field Changed: `lastName` → `organization`

This was found during the same audit session. The original implementation asked users to paste their verification token into their CF profile's `lastName` field. This is destructive — many users have their real name there. Changed to the `organization` field, which is empty for most competitive programmers.

Also fixed:
- Frontend URL: `settings/general` → `settings/social` (where the Organization field is)
- Token expiry: 30 min → 60 min (users need time to actually navigate to CF and paste)
- Token comparison: added `.strip()` — CF may add trailing whitespace to the `organization` field

---

## Verification

```bash
cd backend
.venv/bin/python -m pytest tests/ -q
# Expected: 67 passed (1 new test added: test_streak_grace_day_yesterday_counts)

# Confirm migration applies cleanly
.venv/bin/python -m alembic upgrade head
```

---

## Key Takeaways

- **QA audits before moving phases are non-negotiable.** Phase 2.5 caught 8 bugs that would have become load-bearing assumptions in Phase 3 and 4.
- **Proxy detection (`total_solved == 0`) is always wrong.** Use explicit flags (`has_verified_handle: bool`) from the server.
- **Unique constraints must be paired with `index_elements` on `on_conflict_do_nothing()`** — the constraint is silent if Postgres can't identify which one to check.
- **Grace-day logic is easy to miss because tests rarely include "today" explicitly.** Always write the edge case test before writing the fix.

---

**Next:** Phase 2.6 — Dev Sync Fix (first-sync UX + Redis graceful degradation).
