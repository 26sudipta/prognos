# Phase 1.2 — Database Migration: Auth Tables
**Status:** DONE  
**Date:** 2026-06-19  
**Goal:** Define the `users` and `refresh_tokens` tables as Python classes (SQLAlchemy ORM models) and apply them to the real PostgreSQL database via an Alembic migration.

---

## What Was Built

```
backend/
├── app/
│   └── models/
│       ├── __init__.py        ← re-exports all models (Alembic registration)
│       ├── base.py            ← TimestampMixin (shared created_at + updated_at)
│       ├── user.py            ← User ORM model → maps to `users` table
│       └── refresh_token.py   ← RefreshToken ORM model → maps to `refresh_tokens` table
└── alembic/
    ├── env.py                 ← updated to import app.models
    └── versions/
        └── 001_create_auth_tables.py  ← the migration that creates both tables
```

After running `alembic upgrade head`, the database has:

```
users
  id, email, google_id, name, avatar_url, is_active, created_at, updated_at

refresh_tokens
  id, user_id (FK → users.id), token_hash, expires_at, revoked_at, created_at
  INDEX: idx_refresh_tokens_user_id
```

---

## Concepts Explained

### 1. What Is an ORM Model?

**ORM** stands for Object-Relational Mapper. It's a bridge between Python and the database.

Without an ORM, you write raw SQL:
```sql
INSERT INTO users (email, name) VALUES ('a@b.com', 'Alice');
SELECT * FROM users WHERE email = 'a@b.com';
```

With SQLAlchemy ORM, you write Python:
```python
user = User(email="a@b.com", name="Alice")
db.add(user)
await db.commit()

result = await db.get(User, some_uuid)
```

The ORM translates your Python objects into SQL automatically. Benefits:
- **Type safety** — your IDE knows `user.email` is a `str`, not an unknown DB value
- **No SQL injection** — parameters are always escaped by the ORM
- **Refactorable** — rename a field in Python, the ORM updates the query

---

### 2. SQLAlchemy 2.0 Style — `Mapped` and `mapped_column`

There are two ways to write SQLAlchemy models. We use the modern **2.0 style**:

**Old style (1.x — avoid):**
```python
class User(Base):
    __tablename__ = "users"
    id = Column(UUID, primary_key=True)
    email = Column(String(255), unique=True)
```

**New style (2.0 — what we use):**
```python
class User(Base):
    __tablename__ = "users"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True)
```

**Why the new style?**

The `Mapped[str]` annotation is a Python type hint. It tells your IDE, type checker (mypy), and Pylance exactly what type this field holds. In the old style, `id = Column(...)` was just an untyped class attribute — tools couldn't infer its type.

The `Mapped[str | None]` pattern is also cleaner for nullable fields:
```python
avatar_url: Mapped[str | None] = mapped_column(Text, nullable=True)
```
This immediately communicates "this can be None" at the Python type level, not just at the DB level.

---

### 3. `base.py` — The TimestampMixin

Almost every table in the app needs `created_at` and `updated_at`. Instead of copy-pasting those two columns into every model, we extract them into a mixin:

```python
class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )
```

Any model that inherits from `TimestampMixin` automatically gets both columns:
```python
class User(TimestampMixin, Base):  # inherits created_at + updated_at
    ...
```

**`server_default=func.now()`** — the default value is set by PostgreSQL (`DEFAULT now()`), not by Python. This means:
- If you insert a row without setting `created_at`, Postgres fills it in automatically
- The value is the DB server's clock, not your application server's clock — consistent across multiple app servers

**`onupdate=func.now()`** — SQLAlchemy automatically adds `updated_at = now()` to every `UPDATE` statement on this model. You never have to remember to update it manually.

---

### 4. `user.py` — The User Model

```python
class User(TimestampMixin, Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    google_id: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    avatar_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    refresh_tokens: Mapped[list["RefreshToken"]] = relationship(
        "RefreshToken", back_populates="user", lazy="noload"
    )
```

**Field decisions:**

| Field | Decision | Why |
|---|---|---|
| `id` | UUID, not integer | UUIDs are safe to expose in URLs — integers leak user count and are guessable. `gen_random_uuid()` is generated by Postgres, not Python, so it's always unique even across app restarts. |
| `email` | `UNIQUE` + `NOT NULL` | One account per email address. Also the fallback identifier if `google_id` ever changes. |
| `google_id` | `UNIQUE` + `NOT NULL` | This is the `sub` field from Google's OAuth token — Google's permanent, stable identifier for a user. We match on this during login upsert, not on email (emails can change). |
| `avatar_url` | `TEXT`, nullable | Google profile picture URL. `TEXT` instead of `VARCHAR(n)` because URLs have no meaningful max length. Nullable because anonymized/deleted users have this cleared. |
| `is_active` | `BOOLEAN`, default `true` | Soft-delete flag. When a user requests account deletion, we set `is_active = false` and anonymize PII fields instead of destroying the row. This preserves referential integrity for classroom/leaderboard data. |

**Why soft-delete instead of hard-delete?**

If we `DELETE FROM users WHERE id = ...`, all their classroom memberships, leaderboard entries, and historical stats would either cascade-delete (losing data) or leave orphaned foreign keys (breaking queries). Soft-delete lets us preserve the history while removing PII.

---

### 5. `refresh_token.py` — The RefreshToken Model

```python
class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id: Mapped[uuid.UUID] = ...
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    token_hash: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=text("now()"))
```

**Why `RefreshToken` does NOT inherit `TimestampMixin`:**

`TimestampMixin` gives you `created_at` + `updated_at`. Refresh tokens are **write-once** — once created, they are never modified (there is no UPDATE on a token row). When a token is revoked, we just set `revoked_at`. So `updated_at` would always equal `created_at` and carries no information — we leave it out.

**`token_hash` — why store a hash, not the token itself?**

The raw refresh token is a secret value (like a password). If the database is ever leaked or an attacker gets a DB dump:
- **Raw token stored** → attacker can immediately impersonate all logged-in users
- **Hash stored** → attacker gets SHA-256 digests, which cannot be reversed to the original token

```python
# When creating a token:
raw_token = secrets.token_hex(32)        # generate random token
hash = hashlib.sha256(raw_token.encode()).hexdigest()  # hash it
db.add(RefreshToken(token_hash=hash, ...))  # store hash only
# Send raw_token to the client (cookie) — never store it server-side

# When validating a token:
incoming_hash = hashlib.sha256(cookie_value.encode()).hexdigest()
token = await db.scalar(select(RefreshToken).where(RefreshToken.token_hash == incoming_hash))
```

**`ForeignKey("users.id", ondelete="CASCADE")`**

If a user row is hard-deleted from the database, PostgreSQL automatically deletes all their refresh tokens too. Without `CASCADE`, the FK constraint would block the delete entirely (or leave orphaned token rows if `ON DELETE SET NULL`).

**`index=True` on `user_id`**

The `logout-all` feature (`POST /auth/logout-all`) runs:
```sql
UPDATE refresh_tokens SET revoked_at = now() WHERE user_id = $1;
```
Without an index, this is a full table scan across all tokens. With the index, Postgres jumps directly to the user's tokens in O(log n).

---

### 6. `models/__init__.py` — Why This File Matters for Alembic

```python
from app.models.refresh_token import RefreshToken
from app.models.user import User

__all__ = ["User", "RefreshToken"]
```

Alembic's autogenerate works by comparing `Base.metadata` (the registry of all known tables) against the actual database schema. A model only gets registered into `Base.metadata` when its module is **imported**.

If `alembic/env.py` imports `Base` but never imports the model files, `Base.metadata` is empty — Alembic sees no tables and generates nothing.

By importing all models in `models/__init__.py`, a single line in `env.py` registers everything:
```python
import app.models  # noqa: F401 — this one import pulls in all models
```

As you add new models in Phase 1.5, 2.x, etc., you just add them to `models/__init__.py` — `env.py` never needs to change.

---

### 7. `001_create_auth_tables.py` — The Migration

```python
revision: str = "001"
down_revision: str | None = None   # this is the first migration, nothing before it
```

**`revision` and `down_revision`** form a linked list:

```
None ← 001 ← 002 ← 003 ← ... ← HEAD
```

`alembic upgrade head` walks this chain from left to right, applying each `upgrade()` in order. `alembic downgrade -1` applies `downgrade()` of the current revision and moves left.

**`upgrade()` — what it does:**

```python
def upgrade() -> None:
    # 1. Create users table first (refresh_tokens references it)
    op.create_table("users", ...)

    # 2. Create refresh_tokens table with FK to users
    op.create_table("refresh_tokens", ...,
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
    )

    # 3. Add index for logout-all performance
    op.create_index("idx_refresh_tokens_user_id", "refresh_tokens", ["user_id"])
```

**`downgrade()` — the undo:**

```python
def downgrade() -> None:
    # Drop in reverse order — index first, then child table, then parent table
    op.drop_index("idx_refresh_tokens_user_id", table_name="refresh_tokens")
    op.drop_table("refresh_tokens")   # child first (has FK)
    op.drop_table("users")            # parent last
```

Order matters in `downgrade` — you cannot drop `users` while `refresh_tokens` still has a FK pointing to it.

**Why the migration was written manually, not autogenerated:**

`alembic revision --autogenerate` requires a live database connection to compare against. The local `.env` had an incorrect password at migration time. Rather than block on that, the migration was written manually from the SQL spec in `implementation.md` and verified with:

```python
ScriptDirectory.from_config(cfg).walk_revisions()
# → revision=001, down=None, doc=create_auth_tables ✅
```

The result is identical to what autogenerate would have produced.

---

### 8. Relationships — How Models Reference Each Other

```python
# In User:
refresh_tokens: Mapped[list["RefreshToken"]] = relationship(
    "RefreshToken", back_populates="user", lazy="noload"
)

# In RefreshToken:
user: Mapped["User"] = relationship("User", back_populates="refresh_tokens")
```

**`back_populates`** — links the two sides of the relationship. If you load a `RefreshToken` and access `.user`, SQLAlchemy knows to look at the `User` model. And vice versa. It's bidirectional.

**`lazy="noload"`** — defines what happens when you access `user.refresh_tokens` without having explicitly loaded it:
- `lazy="select"` (default) — automatically fires a second SQL query. Hidden N+1 problem.
- `lazy="noload"` — raises an error immediately. Forces you to be explicit about loading tokens.

We chose `noload` because loading all tokens for a user is almost never needed. The auth routes work with individual token rows, not lists. If you ever need the list, you write an explicit query — no surprises.

---

## Verification

```bash
# Check migration was recognized
cd backend
.venv/bin/python -c "
from alembic.config import Config
from alembic.script import ScriptDirectory
scripts = ScriptDirectory.from_config(Config('alembic.ini'))
for s in scripts.walk_revisions():
    print(f'revision={s.revision} down={s.down_revision}')
"
# → revision=001 down=None ✅

# Apply the migration
.venv/bin/python -m alembic upgrade head
# → INFO Running upgrade  -> 001, create_auth_tables done ✅

# Confirm tables exist in PostgreSQL
sudo -u postgres psql -d prognos -c "\dt"
#          List of relations
#  Schema |     Name       | Type  |  Owner
# --------+----------------+-------+----------
#  public | alembic_version| table | postgres
#  public | refresh_tokens | table | postgres
#  public | users          | table | postgres
```

To view the schema in pgAdmin: connect to `localhost:5432`, open `prognos → Schemas → public → Tables`.

---

## Key Takeaways

1. **ORM models are Python classes** — SQLAlchemy maps them to database tables. You write Python, it writes SQL.
2. **SQLAlchemy 2.0 `Mapped` style** — type-safe, IDE-friendly. Always use this over the old `Column(...)` style.
3. **`TimestampMixin`** — one definition, used by every model. `onupdate=func.now()` means you never manually set `updated_at`.
4. **Store token hashes, never raw tokens** — SHA-256 is one-way. A leaked DB cannot be used to hijack sessions.
5. **`ON DELETE CASCADE`** — if a user is hard-deleted, their tokens are cleaned up automatically by Postgres.
6. **Index on FK columns used in WHERE clauses** — `user_id` without an index makes `logout-all` a full table scan.
7. **`models/__init__.py` is the Alembic registration point** — every new model must be imported here or Alembic won't see it.
8. **Alembic migrations are reversible** — `upgrade head` applies, `downgrade -1` undoes. Every schema change should have both.

---

## Next: Phase 1.3 — Google OAuth + JWT Backend

Implement the auth endpoints: Google OAuth redirect → callback → JWT issuance → token refresh → logout.
