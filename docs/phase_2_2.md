# Phase 2.2 — Analytics API

## What Was Built

```
backend/
├── app/
│   ├── schemas/
│   │   └── analytics.py          ← 4 Pydantic response schemas (new)
│   ├── services/
│   │   └── analytics.py          ← 3 service functions + streak algorithm (new)
│   └── api/v1/
│       ├── routes/
│       │   └── analytics.py      ← 3 GET route handlers (new)
│       └── __init__.py           ← analytics router wired in (modified)
tests/
└── integration/
    └── test_analytics_routes.py  ← 16 tests: streaks, dashboard, tags, rating history (new)
docs/
└── phase_2_2.md                  ← this file
```

---

## Concepts Explained

### 1. Frontend-dumb Architecture (Pre-Computed Reads)

PROGNOS is designed so the frontend never aggregates data — it only reads pre-computed tables. Phase 2.1 built the sync pipeline that computes `daily_activity`, `tag_stats`, and `rating_history`. Phase 2.2 exposes them as read-only REST endpoints. No aggregation happens at request time beyond:
- Summing `daily_activity` across handles (rare: users with multiple platforms)
- Streak calculation from the `daily_activity` map

This keeps API latency predictable regardless of how much data a user has accumulated.

---

### 2. Data Access Path

```
GET /analytics/... (Bearer token)
    → get_current_user dependency → User.id
    → _get_handle_ids(db, user_id)
        SELECT id FROM user_handles
        WHERE user_id = X AND is_active AND is_verified
    → query analytics tables WHERE user_handle_id IN (handle_ids)
```

The partial unique index `UNIQUE (user_id, platform) WHERE is_active` (created in Phase 1.5) guarantees at most one active+verified handle per user per platform. The `IN (handle_ids)` pattern handles multi-platform users cleanly when they exist.

**No handle → graceful empty response.** All three endpoints return zeros or empty arrays rather than 404. A user without a verified handle is not an error state — they simply have no data yet.

---

### 3. Dashboard: What Goes in the Heatmap vs. What Gets Counted Elsewhere

The dashboard aggregates three independent views over `daily_activity`:

| View | Scope | Logic |
|---|---|---|
| `heatmap` | Last 365 days, non-zero solved only | Filter by `activity_date >= today - 364` and `solved_count > 0` |
| `total_solved` | All time | Sum all `solved_count` values in the full dataset |
| Streaks | All time | Run on the full date→solved dict |

Heatmap is scoped to 365 days because that is what a GitHub-style contribution graph renders. Total_solved and streaks are all-time because truncating them to 365 days would show misleading data for users who have been competitive programming for multiple years.

The service fetches all `daily_activity` rows in a single query and computes all three views from the in-memory result — no need for separate SQL aggregations.

---

### 4. Streak Algorithm

Streak = consecutive calendar days where `solved_count > 0`.

```python
# Current streak: walk backwards from today
d = today
while date_solved[d] > 0:
    current += 1
    d -= 1 day

# Longest streak: iterate all dates in order
for d in sorted(dates):
    if solved[d] > 0 and d == prev_active + 1 day:
        run += 1
    elif solved[d] > 0:
        run = 1
    longest = max(longest, run)
```

**Design decision — no grace day.** Some platforms allow a "grace period" where if you solved yesterday but not today, the streak is still alive. PROGNOS does not implement this. If `solved_count[today] == 0`, `current_streak = 0`. This was chosen for honesty: a streak should mean you solved *today*, not that you barely made it yesterday.

**Why not store streaks in the DB?** Streak values change every calendar day even without new submissions (the streak breaks). Recomputing from `daily_activity` at read time is trivially fast (≤1825 rows for 5 years of history) and guarantees the value is always accurate without requiring a daily cron to update a denormalized field.

---

### 5. CF Rating Source

The `cf_rating` field in `DashboardResponse` is derived from `rating_history`, not from a separate column in `user_handles`:

```sql
SELECT new_rating FROM rating_history
WHERE user_handle_id IN (...)
ORDER BY contest_time DESC
LIMIT 1
```

This is the single source of truth — it is exactly what the sync worker inserted. No risk of a stale value sitting in a denormalized column.

---

### 6. Tag Stats and Rating History

Both are direct reads from pre-computed tables with deterministic ordering:

| Endpoint | Table | Order |
|---|---|---|
| `GET /analytics/tags` | `tag_stats` | `solved_count DESC` (most practiced tags first — matches how a user scans their profile) |
| `GET /analytics/rating-history` | `rating_history` | `contest_time ASC` (chronological — matches how a rating chart is rendered left-to-right) |

---

## Verification

```bash
cd backend

# Run Phase 2.2 tests only
.venv/bin/python -m pytest tests/integration/test_analytics_routes.py -v

# Run full suite (should be 58 passing)
.venv/bin/python -m pytest -v
```

Expected output:
```
tests/integration/test_analytics_routes.py::test_streak_consecutive_from_today PASSED
tests/integration/test_analytics_routes.py::test_streak_broken_today PASSED
tests/integration/test_analytics_routes.py::test_streak_gap_in_history PASSED
tests/integration/test_analytics_routes.py::test_dashboard_no_handle_returns_zeros PASSED
tests/integration/test_analytics_routes.py::test_dashboard_heatmap_excludes_old_rows PASSED
tests/integration/test_analytics_routes.py::test_dashboard_heatmap_excludes_zero_solved_days PASSED
tests/integration/test_analytics_routes.py::test_dashboard_total_solved_includes_old_rows PASSED
tests/integration/test_analytics_routes.py::test_dashboard_current_streak PASSED
tests/integration/test_analytics_routes.py::test_dashboard_longest_streak PASSED
tests/integration/test_analytics_routes.py::test_dashboard_cf_rating_from_latest_contest PASSED
tests/integration/test_analytics_routes.py::test_tag_stats_no_handle_returns_empty PASSED
tests/integration/test_analytics_routes.py::test_tag_stats_sorted_by_solved_count_desc PASSED
tests/integration/test_analytics_routes.py::test_tag_stats_all_fields_present PASSED
tests/integration/test_analytics_routes.py::test_rating_history_no_handle_returns_empty PASSED
tests/integration/test_analytics_routes.py::test_rating_history_ordered_by_contest_time_asc PASSED
tests/integration/test_analytics_routes.py::test_rating_history_all_fields_present PASSED

16 passed in 0.81s
```

Manual verification (requires dev server running with a verified handle that has been synced):

```bash
# Start server
.venv/bin/uvicorn app.main:app --reload

# With a valid Bearer token:
curl -H "Authorization: Bearer <token>" http://localhost:8000/api/v1/analytics/dashboard
curl -H "Authorization: Bearer <token>" http://localhost:8000/api/v1/analytics/tags
curl -H "Authorization: Bearer <token>" http://localhost:8000/api/v1/analytics/rating-history
```

---

## Key Takeaways

- All three endpoints are pure reads from pre-computed tables — zero aggregation SQL, predictable latency.
- Streak is computed at read time from `daily_activity` rows; no denormalized streak column needed.
- No grace-day logic: `current_streak = 0` if today has no solved submissions.
- Heatmap scope (365 days) and total_solved/streak scope (all time) are intentionally different.
- `cf_rating` is always derived from `rating_history` — the same table the sync worker writes to.
- No handle → empty/zero response (not 404). A user without a verified handle is a valid state.

---

## Next

**Phase 2.3** — Weakness + Recommendations Engine: expose `GET /api/v1/analytics/weaknesses` and `GET /api/v1/analytics/recommendations` from the `weakness_signals` and `recommendation_sets` tables computed by the sync worker.

---

## Updates

### 2026-06-23 — QA Audit Fixes

**Streak grace-day (requirement §D.2)**

The original implementation set `d = today` as the streak starting point and returned `current_streak = 0` if today had no solved problems. PROGRESS.md recorded this as a deliberate decision ("honest streak semantics"), but it means a user's months-long streak resets to 0 at UTC midnight even if they solved problems yesterday evening.

Fixed: `_compute_streaks()` now starts from yesterday when today has no activity.

```python
# Before
d = today

# After
d = today if date_to_solved.get(today, 0) > 0 else today - timedelta(days=1)
```

The test `test_streak_broken_today` was encoding the wrong behavior as the expected result. It was replaced with two correct tests:
- `test_streak_grace_day_yesterday_counts` — asserts `current == 2` when today=0, yesterday=5, day-2=5
- `test_streak_grace_day_no_streak` — asserts `current == 0` when both today and yesterday are 0

**`has_verified_handle` field added to `DashboardResponse`**

The dashboard page used a proxy heuristic (`heatmap.length == 0 && total_solved == 0 && cf_rating == null`) to detect whether a handle was linked. This false-positives for a verified user who has submissions but no accepted solutions (all WA — heatmap empty, total_solved 0, cf_rating null if unrated). Such a user would see "Link your Codeforces handle" despite having a verified handle.

Fixed: `DashboardResponse` now includes `has_verified_handle: bool` (True when the user has ≥1 verified active handle). `noHandleLinked()` on the frontend reads this field directly.

```python
# schemas/analytics.py — new field
class DashboardResponse(BaseModel):
    ...
    has_verified_handle: bool

# services/analytics.py — populated from handle query
return DashboardResponse(..., has_verified_handle=bool(handle_ids))
```

**Test count:** 67 passed (was 66 — net +1 from streak test replacement).
