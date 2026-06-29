# Phase 4.1 — Classroom System: Database Migration

## What Was Built

```
backend/alembic/versions/006_add_classroom_tables.py   ← new migration
backend/app/models/classroom.py                        ← 4 SQLAlchemy 2.0 models
backend/app/models/__init__.py                         ← exports 4 new models
```

---

## Concepts Explained

### 1. Four Tables, One Domain

The classroom system requires four tightly-coupled tables:

| Table | Role |
|---|---|
| `classrooms` | The entity: name, owner, is_active |
| `classroom_invites` | Multi-use invite links (token, expiry, revocable) |
| `classroom_memberships` | Who belongs to which classroom and in what role |
| `classroom_leaderboard` | Pre-computed cache of per-user stats (JSONB for tags) |

**Why four instead of merging?** Each table has a distinct lifecycle: invites are write-once after creation (only `revoked_at` is updated), memberships change slowly, and the leaderboard is written hourly by Celery workers. Keeping them separate avoids wide tables and lock contention.

### 2. Cascade Strategy

| FK | On delete |
|---|---|
| `classroom_invites.classroom_id → classrooms.id` | CASCADE |
| `classroom_memberships.classroom_id → classrooms.id` | CASCADE |
| `classroom_memberships.user_id → users.id` | CASCADE |
| `classroom_memberships.invite_id → classroom_invites.id` | SET NULL |
| `classroom_leaderboard.classroom_id → classrooms.id` | CASCADE |
| `classroom_leaderboard.user_id → users.id` | CASCADE |

**Why SET NULL on `invite_id`?** If an invite is hard-deleted (which we don't currently do, but could in the future), the membership should survive — the invite was only the entry mechanism. Revoking an invite only sets `revoked_at`; it never deletes existing members.

**Why CASCADE on user_id for leaderboard?** If a user account is deleted, their cached leaderboard row should vanish automatically. The leaderboard is a projection of the user's data — not a historical record.

### 3. JSONB for `top_tags` / `weak_tags`

```python
top_tags: Mapped[Optional[list]] = mapped_column(JSONB, nullable=True)
weak_tags: Mapped[Optional[list]] = mapped_column(JSONB, nullable=True)
```

The leaderboard stores the top 5 tags and top 3 weakness signals per user as JSONB arrays:

```json
// top_tags
[{"tag": "dp", "solved_count": 45}, {"tag": "graphs", "solved_count": 32}]

// weak_tags
[{"tag": "geometry", "signal_type": "neglected", "score": 23.4}]
```

**Why JSONB and not a child table?** The leaderboard is a cache, not a source of truth. It's rebuilt entirely on each Celery run. A child table would require DELETE + INSERT on each rebuild, generating more churn and complexity. JSONB lets us UPSERT a single row per user with all their data atomically.

### 4. `ClassroomInvite` is Write-Once

`ClassroomInvite` inherits from `Base` directly, not `TimestampMixin`, because it only needs `created_at` (no `updated_at`). Revocation writes only `revoked_at`. This models the semantic: an invite record is immutable after creation — you can mark it as revoked, but you can't change the token, the classroom, or the expiry.

### 5. Role Enum Pattern

```python
class ClassroomMembershipRole(str, enum.Enum):
    TEACHER = "teacher"
    STUDENT = "student"

class ClassroomMembership(Base):
    role: Mapped[ClassroomMembershipRole] = mapped_column(
        Enum(ClassroomMembershipRole, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
    )
```

`values_callable=lambda x: [e.value for e in x]` is required to make Alembic use the string values (`"teacher"`, `"student"`) instead of the Python attribute names (`TEACHER`, `STUDENT`) when creating the PG enum type. This matches the convention established in migration 002 (`user_handle_status`).

---

## Verification

```bash
cd backend

# Apply migration
.venv/bin/python -m alembic upgrade head
# Expected: 006_add_classroom_tables ... done

# Verify models import cleanly
.venv/bin/python -c "
from app.models import Classroom, ClassroomInvite, ClassroomMembership, ClassroomLeaderboard
print('Models OK')
"
# Expected: Models OK

# Check tables in psql
psql -U postgres -d prognos -c "\dt classroom*"
# Expected: 4 tables listed
```

---

## Key Takeaways

- Keep cache tables (`classroom_leaderboard`) separate from source-of-truth tables. JSONB + UPSERT is the right pattern for hourly-rebuilt caches.
- CASCADE deletes are safe for cache rows and membership. SET NULL is correct for the `invite_id` audit trail on memberships.
- `values_callable` is required on every enum to avoid Alembic/PG name mismatch.

---

**Next:** Phase 4.2 — Backend CRUD: 14 REST endpoints, service layer, and integration tests.
