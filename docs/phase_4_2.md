# Phase 4.2 — Classroom System: Backend CRUD

## What Was Built

```
backend/app/schemas/classroom.py              ← Pydantic v2 schemas
backend/app/services/classroom.py             ← business logic
backend/app/api/v1/routes/classrooms.py       ← 14 REST endpoints
backend/app/api/v1/__init__.py                ← router registration
backend/app/services/auth.py                  ← account-deletion guard
backend/tests/integration/test_classroom_routes.py  ← 30 tests
```

---

## Concepts Explained

### 1. The Join Flow: 8-Step Gauntlet

Joining a classroom is the most security-sensitive operation. The service validates every precondition before inserting:

```
Token lookup → 404 if not found
Revocation check → 410 if revoked_at IS NOT NULL
Expiry check → 410 if expires_at < now()
Classroom check → 410 if classroom is_active = False
Handle check → 403 if user has no verified active handle
Membership check → 409 if already a member
INSERT membership
Return ClassroomResponse
```

**Why 410 Gone (not 403/400) for expired/revoked invites?** The resource existed but is no longer available. 410 signals "stop trying this link" — more semantic than 403 (which implies authorization) or 400 (which implies bad input).

**Why 403 for no-handle?** The user is authenticated but lacks the prerequisite. The response includes a `code: "HANDLE_NOT_VERIFIED"` field so the frontend can render the specific "verify your handle" CTA without string-matching the message.

### 2. Route Ordering: Static Before Dynamic

FastAPI matches routes top-to-bottom. Since `/classrooms/join` and `/classrooms/{classroom_id}` share the same path prefix, registering `/join` after `/{classroom_id}` would cause FastAPI to treat `"join"` as a UUID — resulting in a validation error every time.

```python
# Correct order in classrooms.py:
@router.post("/classrooms/join")          # registered first
@router.get("/classrooms/join-preview/{token}")  # also static
@router.get("/classrooms/{classroom_id}")  # dynamic — comes after
```

Same principle applies within member routes:
```python
@router.delete("/classrooms/{classroom_id}/members/me")     # static path first
@router.delete("/classrooms/{classroom_id}/members/{user_id}")  # dynamic after
```

### 3. `join-preview` is Public (No Auth)

```python
@router.get("/classrooms/join-preview/{token}")
async def join_preview(token: str, db: AsyncSession = Depends(get_db)):
    # NO get_current_user dependency
```

This endpoint is called by the `/join/[token]` frontend page before the user authenticates. It returns the classroom name and member count so the join page can show a meaningful preview ("You're invited to ICPC Team 2026 — 5 members") without the user being logged in.

It deliberately returns minimal information: just enough to render the CTA, never any member list or private data.

### 4. Account Deletion Guard

`soft_delete_user()` in `services/auth.py` now blocks deletion if the user owns active classrooms:

```python
active_classrooms = await db.scalar(
    select(func.count()).where(
        Classroom.owner_id == user_id,
        Classroom.is_active.is_(True),
    )
)
if active_classrooms:
    raise HTTPException(409, "Delete your classrooms before deleting your account.")
```

**Why block instead of cascade-delete?** A teacher's classroom may contain students who haven't backed up their data. Silently deleting everything on account deletion would be a destructive surprise. The user must explicitly delete (or transfer) each classroom first.

### 5. Schemas: `my_role` is Per-Requesting-User

`ClassroomResponse` includes `my_role: Literal["teacher", "student"]`. This is not stored on the classroom — it's derived from the membership row for the requesting user. The service queries `classroom_memberships WHERE classroom_id=$1 AND user_id=$2` to populate it.

This pattern keeps the API response self-contained: the frontend never needs a separate "am I a teacher?" query.

### 6. Test Fixtures

```python
@pytest.fixture
async def teacher_user(db): ...
@pytest.fixture
async def student_with_handle(db): ...  # has verified CF handle
@pytest.fixture
async def classroom(db, teacher_user): ...
@pytest.fixture
async def invite(db, classroom, teacher_user): ...
```

The `student_with_handle` fixture is critical — most join tests require a verified handle. The fixture inserts a `UserHandle` row with `is_verified=True, is_active=True` so tests don't have to go through the full verification flow.

---

## API Reference (14 Endpoints)

| Method | Path | Auth | Notes |
|---|---|---|---|
| GET | `/classrooms` | required | List user's classrooms |
| POST | `/classrooms` | required | Create (201) |
| GET | `/classrooms/{id}` | required | Detail + my_role |
| DELETE | `/classrooms/{id}` | teacher | Soft-delete classroom (204) |
| GET | `/classrooms/{id}/leaderboard` | member | From cache |
| GET | `/classrooms/{id}/cohort` | teacher | Cohort analytics |
| GET | `/classrooms/{id}/members` | member | All members |
| DELETE | `/classrooms/{id}/members/me` | student | Self-exit (204) |
| DELETE | `/classrooms/{id}/members/{user_id}` | teacher | Remove student (204) |
| POST | `/classrooms/join` | required | Join via token (201) |
| GET | `/classrooms/join-preview/{token}` | **public** | Preview for landing page |
| POST | `/classrooms/{id}/invites` | teacher | Generate invite (201) |
| GET | `/classrooms/{id}/invites` | teacher | List active invites |
| DELETE | `/classrooms/{id}/invites/{invite_id}` | teacher | Revoke (204) |

---

## Verification

```bash
cd backend
.venv/bin/python -m pytest tests/integration/test_classroom_routes.py -v
# Expected: 30 passed

# All 126 tests still pass
.venv/bin/python -m pytest tests/ -q
# Expected: 126 passed
```

---

## Key Takeaways

- Route ordering matters in FastAPI: register static paths before dynamic ones in the same prefix family.
- 410 Gone is the correct status for expired/revoked resources — not 403 or 400.
- Public endpoints (join-preview) must explicitly NOT depend on `get_current_user`.
- `my_role` belongs in the response shape, not as a separate endpoint — keeps the API self-contained.

---

**Next:** Phase 4.3 — Leaderboard Celery worker + cohort analytics.
