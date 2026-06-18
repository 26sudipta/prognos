# PROGRESS.md — Implementation Log

## Current Status: Phase 1 — In Progress
**Last Updated:** 2026-06-19

---

## Phase 1 — Foundation & Auth

### 1.1 Project Scaffolding [DONE]
**Completed:** 2026-06-19

**What was built:**
- `backend/` — FastAPI skeleton with `GET /api/v1/health` (verified: returns 200 OK)
- `frontend/` — Next.js 16 (TypeScript, App Router, Tailwind CSS)
- `backend/pyproject.toml` — uv-managed, all Phase 1 dependencies installed
- `backend/app/core/config.py` — Pydantic Settings (reads .env)
- `backend/app/core/database.py` — SQLAlchemy async engine + session factory
- `backend/app/core/security.py` — JWT issue/verify, refresh token hashing
- `backend/app/api/v1/__init__.py` — central router registry
- `backend/app/main.py` — FastAPI app factory with CORS
- `backend/alembic/` — migration environment configured (env.py, alembic.ini)
- `backend/Dockerfile` — multi-stage build for Railway
- `railway.toml` — web + worker service definitions
- `backend/.env.example` — all required vars documented
- `.gitignore` — venv, node_modules, .env excluded

**Technical decisions:**
- Python package manager: `uv` (Rust-based, 10-100x faster than pip)
- SQLAlchemy async mode with `asyncpg` driver (non-blocking DB queries)
- Swagger docs disabled in production (`docs_url=None` when `ENVIRONMENT=production`)
- CORS restricted to `FRONTEND_URL` env var (not wildcard `*`)
- Refresh tokens stored as SHA-256 hash in DB (never raw token)
- Access JWT: 15 min expiry | Refresh JWT: 7 days, httpOnly cookie

### 1.2 Database: Auth Tables [TODO]
### 1.3 Google OAuth + JWT Backend [TODO]
### 1.4 Auth Frontend [TODO]
### 1.5 Database: Handle Table [TODO]
### 1.6 Handle Verification Backend [TODO]
### 1.7 Handle Verification Frontend [TODO]

---

## Phase 2 — Personal Analytics Engine [TODO]
## Phase 3 — Contest Discovery [TODO]
## Phase 4 — Classroom System [TODO]
## Phase 5 — Mobile Companion [TODO]
## Phase 6 — AI Layer [TODO]
