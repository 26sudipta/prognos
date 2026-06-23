# Phase 2.3 — Weakness + Recommendations Engine

## What Was Built

```
backend/
├── app/
│   ├── schemas/analytics.py          ← added WeaknessSignalResponse, RecommendationResponse, RecommendationSetResponse
│   ├── services/analytics.py         ← added get_weaknesses(), get_recommendations()
│   └── api/v1/routes/analytics.py   ← added GET /analytics/weaknesses, GET /analytics/recommendations
└── tests/integration/
    └── test_weaknesses_recommendations.py   ← 8 integration tests
```

---

## Concepts Explained

### 1. Why Two Different Foreign Key Strategies

`WeaknessSignal` is keyed by `user_handle_id` — weaknesses are per-handle because they're derived from that handle's submission history. A user with two verified handles could have different (or overlapping) weakness profiles.

`RecommendationSet` is keyed by `user_id` — recommendations are synthesized at the user level by the sync worker, which already collapses cross-handle signals. Querying by `user_id` directly avoids the indirection through handle lookup.

```
/weaknesses:      user_id → _get_handle_ids() → WeaknessSignal WHERE user_handle_id IN (ids)
/recommendations: user_id → RecommendationSet WHERE user_id = user_id (direct)
```

This asymmetry mirrors the schema design decisions in Phase 2.1 — the sync worker decides at what granularity data lives, and the read API respects that.

---

### 2. No-Data Contracts

| Endpoint | No-data response | Why |
|---|---|---|
| `/weaknesses` | `[]` | Consistent with `/tags` and `/rating-history`; an empty list is a valid, renderable state |
| `/recommendations` | `null` (JSON null, HTTP 200) | A recommendation *set* is a singular object — there's either one or there isn't. `null` communicates "sync hasn't run yet" more clearly than an empty wrapper object |

The frontend distinguishes these states: an empty weaknesses list means "nothing to improve" (rare but valid after a strong performance), while a null recommendations response means "no data yet — trigger a sync."

---

### 3. selectin Loading + In-Memory Sort

`RecommendationSet.recommendations` is declared with `lazy="selectin"` in the ORM model. When SQLAlchemy loads a `RecommendationSet` row, it automatically fires a second `SELECT ... WHERE recommendation_set_id = $1` query and populates the relationship — no explicit join or subquery needed in the service layer.

The recommendations are then sorted in Python by `position` before serialization:

```python
row.recommendations.sort(key=lambda r: r.position)
```

This is safe because the list is already fully loaded in memory. An `ORDER BY position` on the DB query would also work, but the selectin relationship doesn't expose ordering control at declaration time without adding `order_by` to the relationship definition. In-memory sort on a small list (≤10 recommendations per set) is negligible.

---

### 4. Multiple Sets → Latest Wins

The sync worker appends a new `RecommendationSet` on each sync cycle rather than updating in place. This preserves history (useful for future auditing or trend analysis). The read endpoint returns only the most recent:

```python
select(RecommendationSet)
    .where(RecommendationSet.user_id == user_id)
    .order_by(RecommendationSet.generated_at.desc())
    .limit(1)
```

Older sets accumulate in the DB until a cleanup job runs (out of scope for Phase 2). The query is indexed on `user_id` (Phase 2.1 migration), so `ORDER BY generated_at DESC LIMIT 1` scans only the small set of rows for one user.

---

### 5. WeaknessSignalType in Pydantic

`WeaknessSignalType` is a `str, enum.Enum` defined in `app.models.signals`. Importing it directly into the Pydantic schema means the response serializes to the string value (`"low_success"`, `"neglected"`, `"under_practiced"`) — consistent with how the sync worker writes it, and what the frontend reads.

No adapter or alias needed because `str` enum values round-trip cleanly through Pydantic v2's `from_attributes` mode.

---

## Verification

```bash
cd backend

# Run all tests
.venv/bin/python -m pytest tests/ -q
# Expected: 66 passed

# Run just Phase 2.3 tests
.venv/bin/python -m pytest tests/integration/test_weaknesses_recommendations.py -v
# Expected: 8 passed

# Start dev server and check OpenAPI docs
.venv/bin/uvicorn app.main:app --reload
# Visit http://localhost:8000/docs
# Two new routes visible:
#   GET /api/v1/analytics/weaknesses
#   GET /api/v1/analytics/recommendations
```

---

## Key Takeaways

- **Asymmetric FK navigation** is normal when different tables live at different granularities (handle vs. user). Let the schema shape dictate the query path.
- **null vs [] as no-data** is a deliberate UX contract: `null` = "doesn't exist yet", `[]` = "exists but empty".
- **selectin + in-memory sort** is the right tradeoff for small, always-loaded child collections where DB-side ordering would require modifying the ORM relationship declaration.
- **Consistent service pattern**: `get_weaknesses` / `get_recommendations` follow the exact same structure as `get_tag_stats` / `get_rating_history` — same helper, same early-return, same `model_validate` serialization.

---

## Next

**Phase 2.4 — Dashboard UI**: Frontend components consuming all five analytics endpoints (dashboard, tags, rating history, weaknesses, recommendations). React charts (heatmap, rating graph), weakness cards, recommendation list.

---

## Updates

### 2026-06-23 — QA Audit Fixes

**Missing endpoint built: `POST /analytics/recommendations/refresh`**

This endpoint was specified in `requirement.md §9.4` and `implementation.md §2.3` but never implemented. It regenerates weakness signals and the recommendation set on demand, without the 30-minute sync cooldown (since it only runs local computation, not a CF API fetch).

```python
# services/analytics.py
async def refresh_recommendations(db, user_id):
    from app.workers.cf_sync import _compute_weakness_signals, _generate_recommendations
    handle_ids = await _get_handle_ids(db, user_id)
    if not handle_ids: return None
    for handle_id in handle_ids:
        await _compute_weakness_signals(handle_id, db)
    await _generate_recommendations(handle_ids[0], user_id, db)
    return await get_recommendations(db, user_id)
```

Frontend: `refreshRecommendations(token)` added to `_lib/analytics.ts`.

**Difficulty band clamped to [800, 3500]**

`_pick_problem()` in `cf_sync.py` produced negative low bounds for low-rated users (e.g., rating 900, narrow band: `900 - 200 = 700 < 800`). CF problems don't exist below 800 or above 3500.

```python
# Before
low, high = rating - band, rating + (band * 3)

# After
low  = max(800,  rating - band)
high = min(3500, rating + (band * 3))
```

**DB unique constraints added (migration 004)**

Two constraints required by the spec were missing from migration 003:
- `rating_history`: `UNIQUE(user_handle_id, cf_contest_id)` (spec §8.9)
- `weakness_signals`: `UNIQUE(user_handle_id, tag, signal_type)` (spec §8.10)

Migration `004_add_missing_unique_constraints.py` adds both. The `on_conflict_do_nothing()` call in `_upsert_rating_history()` was also updated to include `index_elements=["user_handle_id", "cf_contest_id"]` — previously it was conflicting on PK only (new UUID each time = never actually conflicted).

The delete-before-reinsert pattern in the sync pipeline prevented data integrity issues in practice; the migration adds the DB-level guarantee.
