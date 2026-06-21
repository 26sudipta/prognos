# Phase 1.5 — Database: Handle Table
**Status:** DONE  
**Date:** 2026-06-21  
**Goal:** Create the `user_handles` table — the single most important table in PROGNOS. Every downstream feature (analytics, sync, verification, classrooms) hangs off a row in this table. Getting the schema and constraints exactly right here prevents expensive migrations later.

---

## What Was Built

```
backend/
├── alembic/
│   └── versions/
│       └── 002_add_user_handles.py     ← migration: table + 3 PG enum types + 2 indexes
├── app/
│   └── models/
│       ├── __init__.py                 ← added UserHandle export
│       ├── user.py                     ← added `handles` relationship
│       └── user_handle.py              ← UserHandle model + enum classes (new)
└── tests/
    ├── conftest.py                     ← async DB session + test_user fixture (new)
    ├── unit/
    │   └── test_user_handle_model.py   ← enum values + model instantiation (new)
    └── integration/
        └── test_user_handle_constraints.py  ← partial unique index behavior (new)
```

---

## Concepts Explained

### 1. Why This Table Exists Before the Verification API

Phase 1.6 (verification backend) needs to read and write `user_handles` rows. SQLAlchemy resolves foreign keys at import time — if you define `UserHandle` and then try to run the server without the table existing in the DB, every startup crashes with `UndefinedTable`.

The migration lands first so that when Phase 1.6 adds routes and service code, the DB is already ready. This is the standard "schema-first" discipline: the DB is never behind the application code.

### 2. The Table's Lifecycle Roles

A single `user_handles` row is not just a link record. It is the **state machine** for the entire handle relationship:

| Column group | Purpose |
|---|---|
| `handle`, `platform`, `user_id` | What handle, on what platform, owned by whom |
| `is_active`, `is_verified`, `status` | Current state of the relationship |
| `verification_token`, `token_expires_at`, `attempt_count` | Ephemeral verification state (Phase 1.6) |
| `is_locked`, `lockout_expires_at` | Brute-force protection (Phase 1.6) |
| `sync_status`, `last_synced_at`, `last_sync_error`, `last_manual_sync_at` | CF data sync pipeline (Phase 2) |
| `created_at`, `updated_at` | Audit trail |

Rather than splitting these concerns into multiple tables, one row holds the full lifecycle. This avoids joins and makes state transitions (verify → sync → suspend) atomic single-row updates.

### 3. Why Soft Delete Instead of Hard Delete

When a user unlinks their handle (`is_active = false`), we do **not** delete the row. All related data — submissions, tag stats, rating history, weakness signals — is kept and remains queryable.

If we deleted the row, the FK constraints on all those child tables would cascade-delete years of competitive programming history. The user's analytics would vanish permanently. Soft delete preserves history while excluding the row from active logic.

The trade-off: every query on "active handle" must include `WHERE is_active = true`. This is enforced by convention in Phase 1.6 service code.

### 4. The Partial Unique Index (the Most Important Decision)

The requirement doc says:
> Unique constraint: `(user_id, platform, is_active)` — one active handle per platform per user.

**This literal constraint is wrong.** Here is why:

A regular `UNIQUE(user_id, platform, is_active)` constraint would mean:
- Only one row with `is_active = true` per user+platform ✓ (desired)
- Only one row with `is_active = false` per user+platform ✗ (breaks soft delete)

If a user links handle A, unlinks it (→ `is_active = false`), then links and unlinks handle B, you'd have two rows with `is_active = false` for the same `user_id + platform`. The constraint would reject the second INSERT.

The correct implementation is a **partial unique index**:

```sql
CREATE UNIQUE INDEX uq_user_handles_active_platform
    ON user_handles (user_id, platform)
    WHERE is_active = true;
```

This index only covers rows where `is_active = true`. PostgreSQL enforces uniqueness only within the filtered set. An unlimited number of `is_active = false` rows can coexist.

In Alembic:
```python
op.create_index(
    "uq_user_handles_active_platform",
    "user_handles",
    ["user_id", "platform"],
    unique=True,
    postgresql_where=sa.text("is_active = true"),
)
```

The intent from the spec ("one active handle per user per platform") is fully honored. The literal column list is not.

### 5. PostgreSQL Enum Types vs VARCHAR + CHECK

Three columns store categorical data with a fixed set of values: `platform`, `status`, `sync_status`. We use native PostgreSQL enum types rather than `VARCHAR + CHECK`:

| Approach | Pros | Cons |
|---|---|---|
| `VARCHAR + CHECK` | Easy to add values without migration | No type safety in DB; any string accepted at app layer if CHECK is bypassed |
| `PG ENUM` | Type-safe at DB level; psql shows valid values; storage is compact | Requires `ALTER TYPE ... ADD VALUE` to extend |

For `platform`, we anticipate adding `leetcode`, `atcoder` etc. later. PG enums are extensible with `ALTER TYPE handle_platform ADD VALUE 'leetcode'`, which is a lightweight DDL operation. The PG enum approach wins on correctness.

The three types created:
```sql
CREATE TYPE handle_platform   AS ENUM ('codeforces');
CREATE TYPE handle_status     AS ENUM ('active', 'suspended');
CREATE TYPE handle_sync_status AS ENUM ('idle', 'in_progress', 'completed', 'sync_error');
```

### 6. `values_callable` — The Hidden SQLAlchemy Trap

When you use `sa.Enum(PythonEnumClass, ...)` in SQLAlchemy, the default behavior is to store the enum's **name** (the Python identifier, e.g. `CODEFORCES`) in the database, not its **value** (e.g. `codeforces`).

Our PG enum type was created with lowercase values. Storing `CODEFORCES` would violate the type and raise:
```
asyncpg.exceptions.InvalidTextRepresentationError:
    invalid input value for enum handle_platform: "CODEFORCES"
```

The fix — add `values_callable` to every enum column:

```python
# Wrong — stores "CODEFORCES" (the Python name)
platform: Mapped[HandlePlatform] = mapped_column(
    sa.Enum(HandlePlatform, name="handle_platform"),
)

# Correct — stores "codeforces" (the Python value)
platform: Mapped[HandlePlatform] = mapped_column(
    sa.Enum(HandlePlatform, name="handle_platform",
            values_callable=lambda x: [e.value for e in x]),
)
```

Rule: **any time you use a Python `enum.Enum` class with `sa.Enum()`, always add `values_callable` to store values, not names.**

### 7. Alembic + Model Metadata = Double CREATE TYPE

The first migration attempt used `op.execute("CREATE TYPE handle_platform AS ENUM (...)")` to explicitly create PG enum types, then `sa.Enum(..., create_type=False)` in `op.create_table()` to suppress SA's own DDL.

It failed:
```
DuplicateObjectError: type "handle_platform" already exists
```

Why: `alembic/env.py` does `import app.models`, which registers `UserHandle` (and its `sa.Enum` columns) in `Base.metadata`. When `op.create_table()` ran, SQLAlchemy's DDL event system fired `_on_table_create` for the **metadata's** enum registration — which had `create_type=True` (the model). The type was being created twice: once by `op.execute()` and once by SA's event.

The fix: **remove the `op.execute()` calls entirely.** Let `sa.Enum` in `op.create_table()` handle type creation with the default `create_type=True`. SA creates each enum type exactly once as part of the table DDL. The downgrade drops them manually:

```python
def downgrade() -> None:
    op.drop_index("uq_user_handles_active_platform", ...)
    op.drop_index("idx_user_handles_user_id", ...)
    op.drop_table("user_handles")
    op.execute("DROP TYPE handle_sync_status")
    op.execute("DROP TYPE handle_status")
    op.execute("DROP TYPE handle_platform")
```

### 8. Test Architecture — Why Two Layers

**Unit tests** (`tests/unit/test_user_handle_model.py`): No database. Test Python-level behavior — enum values are correct, model can be instantiated with the right defaults. Fast, always runnable, no external dependencies.

**Integration tests** (`tests/integration/test_user_handle_constraints.py`): Hit the real PostgreSQL database. Test constraints that only exist at the DB level — specifically, that the partial unique index allows multiple inactive rows but rejects a second active row.

The `test_user` fixture creates a real user row before each test (FK requires it) and cascade-deletes it afterward via `DELETE` (which cascades to `user_handles`). Each test is isolated.

For the constraint violation test, a savepoint is used so the session remains usable after the expected `IntegrityError`:

```python
savepoint = await db_session.begin_nested()  # SAVEPOINT
try:
    await _create_handle(db_session, test_user.id, "second_handle")
    pytest.fail("Expected IntegrityError was not raised")
except IntegrityError:
    await savepoint.rollback()  # ROLLBACK TO SAVEPOINT — outer session still valid
```

Without the savepoint, SQLAlchemy marks the session as `DEACTIVE` after any exception and all further operations fail.

---

## Verification

```bash
cd backend

# 1. Apply the migration
.venv/bin/python -m alembic upgrade head
# INFO  [alembic.runtime.migration] Running upgrade 001 -> 002, add_user_handles

# 2. Inspect the table
psql -d prognos -c "\d user_handles"
# Should show 19 columns, FK to users, PK on id

# 3. Verify the partial index
psql -d prognos -c "\di+ user_handles*"
# uq_user_handles_active_platform  — UNIQUE, WHERE (is_active = true)
# idx_user_handles_user_id         — plain btree on user_id

# 4. Verify the PG enum types
psql -d prognos -c "SELECT typname, enumlabel FROM pg_enum JOIN pg_type ON pg_enum.enumtypid = pg_type.oid WHERE typname LIKE 'handle_%' ORDER BY typname, enumsortorder;"
# handle_platform   | codeforces
# handle_status     | active
# handle_status     | suspended
# handle_sync_status| idle
# handle_sync_status| in_progress
# handle_sync_status| completed
# handle_sync_status| sync_error

# 5. Run the tests
.venv/bin/python -m pytest tests/ -v
# tests/integration/test_user_handle_constraints.py::test_only_one_active_handle_per_user_platform PASSED
# tests/integration/test_user_handle_constraints.py::test_multiple_inactive_handles_allowed PASSED
# tests/unit/test_user_handle_model.py::test_enum_values PASSED
# tests/unit/test_user_handle_model.py::test_model_instantiation PASSED
# 4 passed in 0.13s
```

---

## Key Takeaways

- **Partial unique indexes are the correct tool for "one active record" patterns.** A full unique constraint on `(col_a, col_b, bool_col)` breaks when you need multiple rows where `bool_col = false`.
- **`sa.Enum` with a Python enum stores `.name`, not `.value` by default.** Always add `values_callable=lambda x: [e.value for e in x]` when your PG enum values are lowercase but your Python names are uppercase.
- **`env.py` imports models → SA registers DDL events for every enum in metadata.** Never use `op.execute("CREATE TYPE ...")` alongside `sa.Enum` in `op.create_table()` — you'll get a double-creation race. Let SA handle it once.
- **Soft delete requires every "active record" query to filter `WHERE is_active = true`.** The partial index makes this fast, but it's a convention that all future service code must follow.
- **Use savepoints in integration tests when testing expected DB exceptions.** After an `IntegrityError`, the SA session enters `DEACTIVE` state. A `begin_nested()` / `rollback()` around the failing operation keeps the outer session alive.

---

## Next

**Phase 1.6 — Handle Verification Backend:** implement the 5-step Codeforces handle verification flow (`POST /handles/verify/initiate` → CF API check → token generation → `POST /handles/verify/confirm` → profile link match).
