"""Test fixtures, and the guard that keeps the suite off production.

This file exists in its current shape because of a real incident. `backend/.env`
points `DATABASE_URL` at the production Neon database, and the suite used to
build its engine straight from `settings.DATABASE_URL`. Every run therefore
created rows in production: by 2026-10-14 that had leaked **747 test users and
724 test classrooms** into the live database. The same wiring caused the
outage that week, when a local `alembic upgrade head` stamped production at
revision 009 while the deployed image only knew 001-008, so `alembic upgrade
head` in the container could not resolve the DB's revision, exited non-zero,
and took uvicorn down with it.

Two things fix that here:

1. `TEST_DATABASE_URL` is resolved first, so tests have their own database.
2. The resolved host must be local, or collection aborts. The check happens
   *before* `app.*` is imported and the result is written back into
   `os.environ`, so it also covers the application engine used by TestClient
   and the one `create_async_engine` call in test_clist_sync_integration.py --
   not just the fixtures below.

Set `ALLOW_REMOTE_TEST_DB=1` to override deliberately. Nothing in CI should.
"""

import os
from pathlib import Path

from dotenv import dotenv_values
from sqlalchemy.engine import make_url

_LOCAL_HOSTS = {"localhost", "127.0.0.1", "::1", "", None}
_BACKEND_DIR = Path(__file__).resolve().parents[1]


def _resolve_test_db_url() -> str:
    """Pick the test database URL, preferring env vars over the .env file."""
    file_env = dotenv_values(_BACKEND_DIR / ".env")
    for source in (os.environ, file_env):
        for key in ("TEST_DATABASE_URL", "DATABASE_URL"):
            value = source.get(key)
            if value:
                return value
    raise RuntimeError("Neither TEST_DATABASE_URL nor DATABASE_URL is set")


def _guard(url: str) -> str:
    host = make_url(url).host
    if host in _LOCAL_HOSTS or os.environ.get("ALLOW_REMOTE_TEST_DB") == "1":
        return url
    raise RuntimeError(
        f"\n\nRefusing to run the test suite against a non-local database.\n"
        f"  resolved host : {host}\n"
        f"  database      : {make_url(url).database}\n\n"
        f"The suite creates and deletes rows. Pointing it at a remote host means\n"
        f"writing to production -- that is how 747 test users ended up in the live\n"
        f"database. Set TEST_DATABASE_URL to a local database, e.g.\n\n"
        f"  TEST_DATABASE_URL=postgresql+asyncpg://postgres:<pw>@localhost:5432/prognos_test\n\n"
        f"If you truly mean to target a remote database, set ALLOW_REMOTE_TEST_DB=1.\n"
    )


# Applied before any `app.*` import below: app.core.config builds its Settings
# singleton at import time, and env vars take precedence over the .env file, so
# writing it back here redirects the application engine too.
TEST_DATABASE_URL = _guard(_resolve_test_db_url())
os.environ["DATABASE_URL"] = TEST_DATABASE_URL

import uuid  # noqa: E402

import pytest_asyncio  # noqa: E402
from sqlalchemy.ext.asyncio import (  # noqa: E402
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.models.user import User  # noqa: E402


@pytest_asyncio.fixture
async def db_session():
    engine = create_async_engine(TEST_DATABASE_URL)
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as session:
        yield session
    await engine.dispose()


@pytest_asyncio.fixture
async def test_user(db_session: AsyncSession):
    user = User(
        email=f"test_{uuid.uuid4()}@test.com",
        google_id=f"gid_{uuid.uuid4()}",
        name="Test User",
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    yield user
    await db_session.delete(user)
    await db_session.commit()
