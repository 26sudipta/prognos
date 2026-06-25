# Phase 3.2 — Contest API

## What Was Built

```
backend/
├── app/
│   ├── schemas/
│   │   └── contests.py             ← NEW: ContestItem, ContestsListResponse, ContestsCalendarResponse
│   ├── services/
│   │   └── contests.py             ← NEW: get_contests, get_contests_calendar, get_platforms
│   └── api/v1/
│       ├── routes/
│       │   └── contests.py         ← NEW: 3 route handlers
│       └── __init__.py             ← contests_router included
└── tests/
    ├── unit/
    │   └── test_contests_service.py    ← NEW: 8 unit tests
    └── integration/
        └── test_contests_routes.py     ← NEW: 8 integration tests
```

---

## Concepts Explained

### 1. Why these endpoints require authentication

Contest data is global (not per-user), so technically a public endpoint would work. However:
- The contests page lives inside the app shell (`/dashboard/contests`) — users are always logged in to reach it.
- Requiring `get_current_user` prevents data scraping without any user-visible friction.
- Consistency: every other API route in the app is authenticated. A single unauthenticated route is an asymmetry that needs justification; here there is none.

The route handlers use `_: User = Depends(get_current_user)` — the user object is discarded, but the dependency enforces the auth check.

### 2. Stale data detection

The `_is_stale` helper runs a single `SELECT MAX(last_synced_at) FROM contests` query:

```python
async def _is_stale(db: AsyncSession) -> bool:
    max_synced = await db.scalar(select(func.max(Contest.last_synced_at)))
    if max_synced is None:
        return True
    return (datetime.now(UTC) - max_synced) > timedelta(hours=8)
```

Design decisions:
- **No extra column** — `last_synced_at` was added in Phase 3.1 precisely for this purpose.
- **8-hour threshold** — the beat schedule syncs every 4h. If the last sync was `>8h` ago, at least two cycles were missed, which is worth surfacing to the user.
- **`None` → stale** — if the table is empty (no sync has ever run), the API should indicate that rather than silently return no data.
- **One extra query per request** — acceptable cost; the data is already indexed on `start_time`, and `MAX(last_synced_at)` is a fast aggregate on a small table.

### 3. Calendar grouping by UTC date

Grouping is done in Python after the DB query, not in SQL:

```python
grouped: dict[str, list[ContestItem]] = {}
for row in rows:
    day_key = row.start_time.date().isoformat()
    grouped.setdefault(day_key, []).append(ContestItem.model_validate(row))
days = [CalendarDay(date=d, contests=grouped[d]) for d in sorted(grouped)]
```

Why not `DATE_TRUNC` in SQL? Because:
- The grouping is a presentation concern, not a data concern. The DB doesn't know which timezone the frontend wants to display.
- `start_time` is stored as `TIMESTAMPTZ` (UTC). The server groups by UTC date; the frontend shifts to the user's local timezone for display.
- Doing it in Python keeps the query simple and testable in isolation from the DB.

The days list is always sorted ascending — the UI can rely on this.

### 4. Default time window

Both `get_contests` and `get_contests_calendar` default to `now → now+30d` when `from_dt` / `to_dt` are not provided. This matches the sync worker's lookahead window in Phase 3.1, so the API always returns data that the sync has populated.

If the caller supplies explicit dates (e.g., a calendar showing a specific week), those take precedence.

### 5. `total` in the list response vs. counting in the calendar

`ContestsListResponse` includes `total` (pre-pagination count) so the frontend can render page numbers or "showing X of Y contests" without a second request.

`ContestsCalendarResponse` does **not** include `total` — the calendar view groups all matched contests by day and renders them all at once. Pagination doesn't apply to a calendar.

### 6. Route ordering matters in FastAPI

The three routes are registered in this order:
1. `GET /contests` (list)
2. `GET /contests/calendar`
3. `GET /contests/platforms`

`/calendar` and `/platforms` must be declared **before** any `/{id}` path parameter routes (if those are added later). FastAPI matches routes top-down; a `/{id}` route would capture the literal string `"calendar"` if declared first. There is no `/{id}` route in this phase, but the ordering is already correct for when it is added.

---

## Verification

```bash
# Run new tests
cd backend
.venv/bin/python -m pytest tests/unit/test_contests_service.py tests/integration/test_contests_routes.py -v
# Expected: 16 passed

# Full suite
.venv/bin/python -m pytest
# Expected: 94 passed

# Check routes are registered
.venv/bin/uvicorn app.main:app --reload
curl http://localhost:8000/openapi.json | python -m json.tool | grep '"/api/v1/contests'
# Expected: "/api/v1/contests", "/api/v1/contests/calendar", "/api/v1/contests/platforms"
```

---

## Key Takeaways

- **`_: User = Depends(get_current_user)`** — the underscore convention signals "auth only, discard result." Keeps the intent visible without a linting complaint about an unused variable.
- **Stale detection on `MAX(last_synced_at)`** — a single aggregate over an existing column is cheaper and more correct than a separate metadata table or a heartbeat row.
- **Calendar grouping in Python, not SQL** — presentation logic stays out of the DB layer; easier to test and reason about timezone behaviour.
- **`total` in list, not in calendar** — match the response shape to how the frontend actually uses the data.
- **Route order** — `/calendar` and `/platforms` before any future `/{id}` param route; document this constraint now so it isn't rediscovered later.

---

## Next

**Phase 3.3** — Contest UI: `frontend/app/(dashboard)/contests/page.tsx` with countdown header, platform filter chips, list view (cards grouped by date, live countdown for <24h contests), and calendar week view.
