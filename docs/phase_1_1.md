# Phase 1.1 — Project Scaffolding
**Status:** DONE  
**Date:** 2026-06-19  
**Goal:** Set up the entire project skeleton — backend, frontend, config, security, deployment — with a working health endpoint as proof.

---

## What Was Built

```
prognos/
├── backend/
│   ├── app/
│   │   ├── api/v1/routes/health.py   ← GET /api/v1/health
│   │   ├── api/v1/__init__.py        ← router registry
│   │   ├── core/config.py            ← reads .env into Python
│   │   ├── core/database.py          ← DB connection pool
│   │   ├── core/security.py          ← JWT + token hashing
│   │   └── main.py                   ← FastAPI app entry point
│   ├── alembic/                      ← DB migration environment
│   ├── Dockerfile                    ← multi-stage build for Railway
│   ├── pyproject.toml                ← uv dependencies
│   └── .env.example                  ← required env vars template
├── frontend/                         ← Next.js 16 (TypeScript + Tailwind)
├── railway.toml                      ← deployment config
└── .gitignore
```

---

## Concepts Explained

### 1. Why Two Folders (backend + frontend)?

They are two completely separate programs that talk to each other over HTTP.

- **Frontend** (`frontend/`) — what users see in the browser. Built with Next.js (React). It makes API calls to the backend and displays the results.
- **Backend** (`backend/`) — the brain. Handles data, authentication, business logic. Users never interact with it directly.

```
Browser → frontend (Next.js) → HTTP requests → backend (FastAPI) → PostgreSQL
```

This separation means you can change the UI without touching the backend, and vice versa. It also lets the Flutter mobile app (Phase 5) use the same backend with zero changes.

---

### 2. `pyproject.toml` — The Ingredients List

Equivalent to `package.json` in Node.js. Lists every Python library the app needs.

```toml
[project]
name = "prognos-backend"
requires-python = ">=3.12"
dependencies = [
    "fastapi",        # web framework
    "uvicorn",        # the server that runs FastAPI
    "sqlalchemy",     # Python ↔ PostgreSQL bridge
    "asyncpg",        # PostgreSQL driver (fast, non-blocking)
    "alembic",        # database schema migrations
    "pydantic-settings",  # reads .env into typed Python objects
    "python-jose",    # JWT creation and verification
    "httpx",          # HTTP client (calls CF API, Google)
    "python-multipart",   # handles form/file uploads
]
```

**Why `uv` instead of `pip`?**  
`uv` is written in Rust. It installs packages 10–100x faster than `pip`. It also manages the virtual environment automatically — no more manually running `python -m venv .venv`.

**Virtual environment (`.venv/`)** — an isolated Python environment just for this project. Every project gets its own `.venv` so their dependencies don't conflict with each other or your system Python.

---

### 3. `core/config.py` — Environment Variables

**The problem:** Real credentials (database passwords, API keys) must never be hardcoded in code or committed to git.

**The solution:** Store them in a `.env` file (gitignored), and read them at startup.

```python
class Settings(BaseSettings):
    DATABASE_URL: str           # required — app crashes if missing
    GOOGLE_CLIENT_ID: str       # required
    JWT_SECRET: str             # required
    REDIS_URL: str = "redis://localhost:6379/0"  # has a default
```

`pydantic-settings` reads `.env` and maps each variable to a typed Python attribute. If a required variable is missing → the app refuses to start with a clear error. This is intentional — better to fail at startup than crash in production mid-request.

**`settings = Settings()`** at the bottom creates one shared instance. Every other file imports this one object:
```python
from app.core.config import settings
print(settings.DATABASE_URL)
```

---

### 4. `core/database.py` — The Database Connection

**The problem:** Opening a new database connection for every HTTP request is slow (takes ~50ms each time).

**The solution:** A connection pool — a set of connections that stay open and get reused.

```python
engine = create_async_engine(settings.DATABASE_URL, pool_pre_ping=True)
```

- `async_engine` — non-blocking. While waiting for the DB response, FastAPI can handle other requests. This is why FastAPI can serve thousands of users simultaneously.
- `pool_pre_ping=True` — before reusing a connection, checks it's still alive. Prevents errors after DB restarts.

**`get_db()` function** — a dependency injected into route handlers:
```python
async def some_route(db: AsyncSession = Depends(get_db)):
    # db is a live session, automatically closed after this function returns
```
The `yield` in `get_db` means: give the session to the route, wait for it to finish, then close the session. No manual cleanup needed.

**`Base` class** — all SQLAlchemy models inherit from this. It lets Alembic detect your tables and generate migrations automatically.

---

### 5. `core/security.py` — How Authentication Works

#### JWT (JSON Web Token)

A JWT is a signed string in three parts: `header.payload.signature`

```
eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJ1c2VyLWlkIn0.HMAC_signature
     (header)              (payload)               (signature)
```

- The **payload** contains data: `{"sub": "user-uuid", "exp": 1234567890, "type": "access"}`
- The **signature** is created using `JWT_SECRET` — only the server knows this key
- Anyone can read the payload, but only the server can verify the signature is genuine
- This means: no database lookup on every request — the token proves identity by itself

**Why two tokens (access + refresh)?**

| Token | Expiry | Stored | Purpose |
|---|---|---|---|
| Access token | 15 minutes | Browser memory (JS) | Sent with every API request |
| Refresh token | 7 days | `httpOnly` cookie | Gets a new access token when it expires |

Short access token = if stolen, it's useless in 15 minutes.  
`httpOnly` cookie = JavaScript cannot read it → immune to XSS attacks.  
Refresh token is stored **hashed** in the database (SHA-256) → if the DB is leaked, raw tokens are not exposed.

```python
def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()
```

**Token rotation** — when a refresh token is used, it's immediately replaced with a new one. If someone steals an old refresh token, it's already invalid.

---

### 6. `api/v1/routes/health.py` — The Heartbeat Endpoint

```python
@router.get("/health")
async def health():
    return {"status": "ok", "service": "prognos-api"}
```

**Why it exists:** Railway (and any load balancer/monitoring tool) pings this every few seconds. If it stops returning 200 → the service is considered dead → Railway restarts it. It intentionally makes zero database calls — it only proves the Python process is alive.

---

### 7. `api/v1/__init__.py` — The Router Registry

```python
api_router = APIRouter(prefix="/api/v1")
api_router.include_router(health_router, tags=["system"])
```

All routes live in separate files (`health.py`, `auth.py`, `handles.py`, etc.). This file collects them all into one `api_router` that `main.py` mounts. Adding a new feature:
1. Create `routes/new_feature.py`
2. Add one import + one `include_router` line here

---

### 8. `app/main.py` — The Entry Point

Two important configurations here:

**CORS (Cross-Origin Resource Sharing)**  
Browsers block JavaScript from calling a server on a different domain by default. CORS tells the browser "this server allows requests from `localhost:3000`."

Without CORS:
```
Browser: "I'm on localhost:3000, can I call localhost:8000?"
Backend: (no response) → Browser blocks the request
```

With CORS configured:
```
Browser: "I'm on localhost:3000, can I call localhost:8000?"
Backend: "Yes, I allow requests from localhost:3000"
Browser: Proceeds with the request
```

**Swagger docs (`/docs`)**  
FastAPI reads your route definitions and auto-generates interactive API documentation. You can test every endpoint in the browser — no Postman needed. Disabled in production (`docs_url=None`) to avoid exposing API structure to attackers.

---

### 9. `alembic/` — Version Control for the Database

**The problem:** As the app grows, the database schema changes (new tables, new columns). You need a way to:
- Apply changes consistently across dev, staging, and production
- Roll back a bad change
- Track what changed and when

**The solution:** Alembic migration files.

Each migration has an `upgrade()` (apply the change) and `downgrade()` (undo it):

```python
def upgrade():
    op.create_table('users', ...)   # creates the table

def downgrade():
    op.drop_table('users')          # removes it
```

**`alembic/env.py`** — the configuration bridge. It connects Alembic to our SQLAlchemy models and our `.env` database URL. When you run `alembic revision --autogenerate`, it compares your Python models against the actual database and writes the migration SQL for you.

**Workflow:**
```bash
# After changing a model in Python:
alembic revision --autogenerate -m "add users table"
# Review the generated file in alembic/versions/
alembic upgrade head   # apply to database
```

---

### 10. `Dockerfile` — Packaging for Production

Multi-stage build — two separate Docker stages:

**Stage 1 (builder):** Has all build tools, installs packages into `.venv`  
**Stage 2 (runtime):** Copies only `.venv` + `app/` — no build tools, smaller image

```dockerfile
FROM python:3.12-slim AS builder
# ... install dependencies ...

FROM python:3.12-slim AS runtime
COPY --from=builder /app/.venv /app/.venv  # only the installed packages
COPY app/ ./app/                           # only the source code
CMD ["uvicorn", "app.main:app", ...]
```

Smaller image = faster deploys, less attack surface, lower costs.

---

### 11. `railway.toml` — Deployment Config

Tells Railway how to run each service:

```toml
[[services]]
name = "web"
startCommand = "uvicorn app.main:app --host 0.0.0.0 --port $PORT"
healthcheckPath = "/api/v1/health"   # Railway pings this

[[services]]
name = "worker"
startCommand = "celery -A app.workers.celery_app worker"
```

Two services share the same Docker image but run different commands. Railway provides PostgreSQL and Redis as plugins — connection strings are injected as environment variables automatically.

---

### 12. `.env` and `.env.example`

| File | Committed to git? | Purpose |
|---|---|---|
| `.env.example` | YES | Shows teammates what variables are needed |
| `.env` | NO (gitignored) | Contains the actual secret values |

The JWT secrets were generated using Python's `secrets` module — cryptographically secure random bytes:
```python
secrets.token_hex(32)  # 64-character hex string
```

Never use short/predictable JWT secrets. If someone knows your `JWT_SECRET`, they can forge tokens and impersonate any user.

---

## Verification

```bash
# Start the server
cd backend
.venv/bin/uvicorn app.main:app --reload

# Test health endpoint
curl http://localhost:8000/api/v1/health
# → {"status": "ok", "service": "prognos-api"}

# View auto-generated API docs
open http://localhost:8000/docs
```

**Result:** `200 OK` ✅ — Server starts, reads config, CORS is active, Swagger loads.

---

## Key Takeaways

1. **Backend and frontend are separate programs** — they communicate only via HTTP JSON.
2. **`.env` holds secrets, `.env.example` holds the template** — never commit real credentials.
3. **JWT = tamper-proof wristband** — server can verify identity without a DB lookup.
4. **`httpOnly` cookie for refresh tokens** — JavaScript cannot steal it.
5. **Alembic = Git for your database** — every schema change is versioned and reversible.
6. **Connection pool** — one set of DB connections shared across all requests, not one per request.

---

## Next: Phase 1.2 — Database Migration: Auth Tables
Create the `users` and `refresh_tokens` tables using Alembic. First real database work.
