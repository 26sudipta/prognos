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
