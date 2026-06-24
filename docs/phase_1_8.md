# Phase 1.8 — User Account Management & Phase 1 Audit

## What Was Built

### New/Modified Files

```
backend/
├── app/
│   ├── schemas/user.py              ← added UserUpdateRequest
│   ├── services/auth.py             ← added update_user_name, soft_delete_user; fixed upsert_user
│   └── api/v1/routes/users.py      ← added PATCH /users/me, DELETE /users/me
└── tests/
    └── integration/
        └── test_auth_service.py     ← 11 new integration tests (NEW FILE)

requirement.md                        ← token prefix corrected CS- → PGS-
implementation.md                     ← token format description corrected
PROGRESS.md                          ← date corrected, Phase 1.8 entry added
```

---

## Concepts Explained

### 1. Why These Endpoints Were Missing

`requirement.md` §9.2 lists three `/users/me` routes:

| Method | Path | Purpose |
|---|---|---|
| GET | `/users/me` | Get current user — ✅ Phase 1.3 |
| PATCH | `/users/me` | Update display name — ❌ missing |
| DELETE | `/users/me` | Soft-delete account — ❌ missing |

They were missing because `implementation.md` Phase 1.3 only listed the 5 auth endpoints + `GET /users/me`. `PATCH` and `DELETE` were described in the requirements document but never added to the implementation plan. They would have been silently skipped indefinitely without the audit.

---

### 2. Soft-Delete Pattern — Why Not Hard-Delete

Per requirement.md §A.4, deleting a user soft-deletes them: `is_active = false`. Hard deletion is intentionally avoided because:

- **Classroom membership and leaderboard entries** reference `user_id`. Hard-deleting would cascade-delete this data or orphan it.
- **Historical analytics data** (submissions, tag_stats, rating_history) belongs to the handle, not the user account directly. Preserving it keeps future audit/migration paths open.
- **Teacher account deletion is explicitly blocked** if classrooms exist (Phase 4 enforcement).

---

### 3. PII Anonymization Strategy

When an account is deleted, `soft_delete_user` replaces all PII fields:

| Field | Before | After |
|---|---|---|
| `email` | `user@gmail.com` | `deleted_a3f9c2b1e4d8f70c@deleted.invalid` |
| `google_id` | `102345678901234567890` | `deleted_a3f9c2b1e4d8f70c8923...` (full SHA-256) |
| `name` | `Sudipta Das` | `Deleted User` |
| `avatar_url` | `https://...` | `NULL` |
| `is_active` | `true` | `false` |

**Why SHA-256 of `user_id` for the replacement values?**

Two goals conflict:
1. Remove all identifying data (GDPR-style compliance).
2. Preserve uniqueness constraints (`email UNIQUE`, `google_id UNIQUE`) so the anonymized value doesn't violate them if two users are deleted.

Using `sha256(user_id)` as the anonymous placeholder satisfies both: the original PII is gone, and each anonymized value is unique (one user → one hash, deterministic and unique).

The `@deleted.invalid` TLD is a non-routable domain (`invalid` is RFC-2606 reserved), so the fake email can never be used for actual communication.

---

### 4. SQLAlchemy Identity Map — The Stale Object Problem

When writing auth service integration tests, three tests failed with stale data even after a commit. This is a fundamental SQLAlchemy behavior:

**The identity map** is a per-session in-memory dictionary: `{(Model, primary_key) → ORM instance}`. When you execute a `SELECT` and the PK is already in the map, SQLAlchemy returns the **cached instance** without updating it from the DB result — unless the object is expired.

The session factory in `conftest.py` uses `expire_on_commit=False`:
```python
factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
```

This means: after `await db.commit()`, objects in the identity map are NOT expired. A subsequent `select()` for the same PK will return the cached (stale) instance.

**Two fixes applied:**

**Fix 1 — Service functions:** After any mutating operation (`INSERT ON CONFLICT`, `UPDATE`), re-select with `populate_existing=True`:
```python
# Forces SQLAlchemy to apply DB values to the existing identity map entry
result = await db.execute(
    select(User).where(User.id == user_id),
    execution_options={"populate_existing": True},
)
```
This is now used in `upsert_user` and `update_user_name`.

**Fix 2 — Tests:** For soft-delete, use `await db_session.refresh(obj)` instead of a plain `select()`. `refresh()` always hits the DB and updates the object:
```python
await soft_delete_user(db_session, str(test_user.id))
await db_session.refresh(test_user)  # Forces DB read
assert test_user.is_active is False   # Now correct
```

**Why `populate_existing` vs `refresh`?**
- `populate_existing` on a `select()` is for service functions returning a new object — we don't have the ORM instance, only an ID.
- `refresh(obj)` is for tests where we already have the ORM instance and want to force-reload it.

---

### 5. Token Prefix: CS- vs PGS-

The original spec (`requirement.md`) specified a `CS-` prefix for verification tokens. Phase 1.6 changed it to `PGS-` (documented in PROGRESS.md) but never updated the spec. The audit caught this drift.

**Rule:** `requirement.md` is the source of truth. Any deviation must be reflected back into `requirement.md` at the time the decision is made. A decision that lives only in PROGRESS.md is invisible to anyone reading the spec later.

Fixed: `requirement.md` and `implementation.md` now show `PGS-A3F9C2` as the example format.

---

## Verification

```bash
cd backend

# Run new auth service tests
.venv/bin/python -m pytest tests/integration/test_auth_service.py -v
# Expected: 11 passed

# Run full test suite
.venv/bin/python -m pytest -v
# Expected: 30 passed
```

---

## Key Takeaways

- **Spec drift is silent.** A decision documented only in PROGRESS.md is invisible to requirement.md readers. Spec corrections must be reflected back into the source-of-truth document immediately.
- **`expire_on_commit=False` requires discipline.** Any service function that mutates and then returns the object must use `populate_existing=True` on the re-select. Otherwise tests (and code that reuses the same session) will see stale data.
- **Soft-delete is not free.** PII anonymization must satisfy two constraints simultaneously: compliance (remove identifying data) and database integrity (preserve uniqueness). SHA-256 of the primary key threads this needle.
- **Phase audits catch gaps.** `PATCH /users/me` and `DELETE /users/me` were in the requirements, not in the implementation plan, and would have been silently skipped. An audit before each phase transition is part of the definition of done.

---

## Next

**Phase 2 — Personal Analytics Engine** ([implementation.md](../implementation.md#phase-2--personal-analytics-engine)):
Celery + Redis setup, CF submission sync worker, `daily_activity` / `tag_stats` / `rating_history` tables, analytics API, weakness engine, recommendations.
