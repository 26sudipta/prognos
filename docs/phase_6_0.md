# Phase 6.0: Classroom Visit Baseline (Classroom v2, Slice 0)

> **Goal:** start measuring how often people open a classroom, *before* Classroom v2 changes
> anything they can see. Every later slice gets judged against this baseline.
> Plan: `docs/classroom_v2_plan.md` §10.0 and §12.

---

## What Was Built

```
backend/
├── alembic/versions/
│   └── 010_classroom_daily_visits.py      ← NEW: classroom_daily_visits table (009 → 010)
├── app/
│   ├── models/
│   │   ├── classroom.py                   ← ClassroomDailyVisit model
│   │   └── __init__.py                    ← model registered
│   └── services/
│       ├── classroom.py                   ← _visit_insert + _record_visit; called by
│       │                                    get_classroom and get_leaderboard;
│       │                                    delete_classroom clears the class's visits
│       └── auth.py                        ← soft_delete_user clears the user's visits
└── tests/integration/
    └── test_classroom_routes.py           ← +7 tests (visit logging)
```

No API, schema-response, web or mobile changes. Nobody can see this slice. That's the point.

---

## Concepts Explained

### 1. Why measure before changing anything

The plan's success test is a before/after comparison: does the weekly league keep bottom-third
students coming back at least as well as today's leaderboard? With 15 users in production, an A/B
test can't produce a meaningful result, so the only honest comparison is against our own past. A past
that wasn't recorded can't be compared against. So Slice 0 ships alone and collects two weeks of
data while the classroom still looks exactly as it does today.

### 2. One row per member per day, not an event log

| Option | Rows for 15 users over a year | What it can answer |
|---|---|---|
| Event log (every request) | Hundreds of thousands, mostly 5 s sync polls | Everything, at a storage and privacy cost |
| **Daily presence** (chosen) | At most ~5,500 | "Was this person in the class on day D?", which every metric in plan §1.3 needs |

The table holds `(classroom_id, user_id, visit_date)` with a unique key across all three. The
insert is `ON CONFLICT DO NOTHING`, so any number of calls on the same day leaves exactly one row.
That idempotency is what makes the next decision safe.

### 3. Why two endpoints log, not one

The plan first said "log in the leaderboard GET". A grep of both clients showed why that would
break the baseline:

| Client | What it calls when a classroom opens |
|---|---|
| Web (`classrooms/[id]/page.tsx`) | Detail **and** leaderboard. The leaderboard is re-polled every 5 s while a sync runs |
| Android app (shipped APK) | Leaderboard only. The detail comes from the cached class list, so `GET /classrooms/{id}` rarely fires |

Slice 1 makes League the web's default tab, so after Slice 1 the web would stop calling the
leaderboard on open. A leaderboard-only counter would then show a drop in visits caused purely by
a tab change, which would make the before/after comparison worthless. Logging on the detail GET
alone would miss nearly every Android visit.

So `_record_visit` runs at the end of **both** `get_classroom` and `get_leaderboard`, and will run
in the Slice 1 league read too. Thanks to the unique key, a web open that hits both endpoints
still counts once. Polling costs one no-op insert per poll. The PWA service worker never touches
`/api/`, so it can't inflate anything.

### 4. `visit_date` is UTC, and stays UTC

Classrooms get their own timezone in Slice 1. It's tempting to switch visit days to class-local
time then, but that would change what a "day" means halfway through the measurement, and the
baseline and pilot numbers would stop lining up. Days stay UTC permanently. Analysis can shift
them later if it ever matters, since 6 hours of offset barely moves a weekly count.

### 5. Analytics must never take a page down

The 2026-10-14 outage started with a migration mismatch. The boot script now starts uvicorn even
when migrations fail, which means the code can run without table 010 existing. Without
protection, every classroom page would then return 500 because of a metric nobody sees.

```python
try:
    async with db.begin_nested():          # SAVEPOINT
        await db.execute(_visit_insert(classroom_id, user_id))
    await db.commit()
except Exception:
    logger.exception("classroom visit logging failed ...")
```

Two details make this safe:

- **It runs last**, after the response object is built, so nothing the caller needs is pending.
- **It uses a savepoint, not a rollback.** A failed statement only rolls back to the savepoint. A
  full `rollback()` would expire every object in the session, and touching an expired attribute
  under async SQLAlchemy raises `MissingGreenlet`. A savepoint rollback leaves untouched objects
  alone, so the session stays usable.

`test_visit_logging_failure_does_not_break_reads` proves it by swapping the insert for one that
targets a missing table, then checking that both reads still return normally.

### 6. Leaving keeps history, deleting an account doesn't

| Event | Visit rows | Why |
|---|---|---|
| Student leaves or is removed | **Kept** | Leave rate is a guardrail metric in plan §1.3. A leaver's last visits are exactly the signal |
| Classroom deleted | Deleted with the class's other operational rows | The class is gone, and nothing should outlive it |
| Account deleted (`soft_delete_user`) | Deleted | Visit history is personal data. Soft delete keeps the `users` row, so the FK cascade wouldn't fire on its own |

The FKs still `ON DELETE CASCADE` for the rare hard delete, such as test cleanup.

### 7. Migration hygiene after the outage

- Hand-written, `down_revision = "009"`, with explicit `idx_` / `uq_` names. The model declares the
  same index name in `__table_args__`, so a future autogenerate won't see drift.
- Applied only to local databases, with `DATABASE_URL` set explicitly for each run. `alembic/env.py`
  refuses non-local targets outside production anyway.
- Production gets it the normal way: the container runs `alembic upgrade head` at boot after a push.

---

## Measuring the Baseline

Run these read-only queries against production at the end of each pilot week. Production is the
one place real visits exist, so use a read-only session, never the app's migration path. Each
query was checked against seeded data on the local test database (three students in different
thirds, a teacher and a leaver, inside a rolled-back transaction) and returned the expected numbers.

**Q1. Weekly active members per classroom**
```sql
SELECT v.classroom_id,
       date_trunc('week', v.visit_date)::date AS week,
       COUNT(DISTINCT v.user_id)              AS active_members
FROM classroom_daily_visits v
GROUP BY 1, 2
ORDER BY 1, 2;
```

**Q2. Week-over-week return rate by rating third** (students only; unrated students sort into the
bottom third). This is the bottom-third gap from plan §1.3 in its weekly form.
```sql
WITH weeks AS (
  SELECT DISTINCT classroom_id, user_id,
         date_trunc('week', visit_date)::date AS week
  FROM classroom_daily_visits
),
thirds AS (
  SELECT lb.classroom_id, lb.user_id,
         ntile(3) OVER (PARTITION BY lb.classroom_id
                        ORDER BY lb.cf_rating NULLS FIRST) AS third
  FROM classroom_leaderboard lb
  JOIN classroom_memberships m
    ON m.classroom_id = lb.classroom_id
   AND m.user_id = lb.user_id
   AND m.role = 'student'
)
SELECT w.classroom_id, w.week, t.third,
       COUNT(*)                                        AS active,
       COUNT(nxt.user_id)                              AS back_next_week,
       ROUND(100.0 * COUNT(nxt.user_id) / COUNT(*), 1) AS return_pct
FROM weeks w
JOIN thirds t USING (classroom_id, user_id)
LEFT JOIN weeks nxt
  ON nxt.classroom_id = w.classroom_id
 AND nxt.user_id = w.user_id
 AND nxt.week = w.week + 7
GROUP BY 1, 2, 3
ORDER BY 1, 2, 3;
```

**Q3. Teacher visit days per week**
```sql
SELECT v.classroom_id,
       date_trunc('week', v.visit_date)::date AS week,
       COUNT(*)                               AS teacher_visit_days
FROM classroom_daily_visits v
JOIN classroom_memberships m
  ON m.classroom_id = v.classroom_id
 AND m.user_id = v.user_id
 AND m.role = 'teacher'
GROUP BY 1, 2
ORDER BY 1, 2;
```

**Q4. Visitors who later left**
```sql
SELECT v.classroom_id, COUNT(DISTINCT v.user_id) AS visited_then_left
FROM classroom_daily_visits v
LEFT JOIN classroom_memberships m
  ON m.classroom_id = v.classroom_id
 AND m.user_id = v.user_id
WHERE m.user_id IS NULL
GROUP BY 1;
```

Caveat for Q2: thirds use each student's *current* rating, so a student who climbs during the pilot
can change thirds. With weekly reads and small classes this is noise, but say so when reporting.

---

## Verification

```bash
cd backend

# 1. Migration round-trip on the LOCAL test database (never production)
export DATABASE_URL="$(.venv/bin/python -c "from dotenv import dotenv_values; print(dotenv_values('.env')['TEST_DATABASE_URL'])")"
.venv/bin/python -m alembic upgrade head      # → Running upgrade 009 -> 010
.venv/bin/python -m alembic downgrade 009     # → Running downgrade 010 -> 009
.venv/bin/python -m alembic upgrade head
.venv/bin/python -m alembic current           # → 010 (head)
unset DATABASE_URL

# 2. The new tests
.venv/bin/python -m pytest tests/integration/test_classroom_routes.py -q -k visit
# → 7 passed

# 3. The whole suite
.venv/bin/python -m pytest -q
# → 164 passed
```

After deploying, open any classroom once on web and once in the app on the same day. Q1 should then
count that member once for this week.

---

## Key Takeaways

- **Measure first.** A before/after study needs a "before", and it has to be recorded while the old
  design is still live.
- **Choose the grain that answers the question.** Daily presence covers every pilot metric at a tiny
  fraction of an event log's size and privacy cost.
- **Idempotent writes let you log from several places.** With a unique key and `ON CONFLICT DO
  NOTHING`, logging from every "opened the class" read is free, and the metric survives client and
  tab changes.
- **Instrumentation is never allowed to break the product.** Write it last, in a savepoint, and
  swallow its errors with a log line.
- **Retention data and personal data follow different rules.** Leavers keep their history for the
  guardrail metric. Deleted accounts take theirs with them.
- **These GET handlers now write.** If reads ever move to a replica (tech-debt item D10), visit
  logging has to stay pinned to the primary database.

---

## Next: Phase 6.1, Weekly Growth League (Classroom v2, Slice 1)

Data fidelity (`participant_type`, `cf_problems`), class settings, visibility modes, then the league
itself. Full design in `docs/classroom_v2_plan.md` §10.1 to §10.8. It should reach users only after
two weeks of baseline from this slice.
