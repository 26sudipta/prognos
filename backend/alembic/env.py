import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from app.core.config import settings
from app.core.database import Base
import app.models  # noqa: F401 — registers all models with Base.metadata

# Alembic Config object
config = context.config

# Guard against migrating a remote database from a developer machine.
#
# This is the exact command that caused the 2026-10-14 outage: `alembic upgrade
# head` run locally, while DATABASE_URL pointed at production Neon, stamped
# production at revision 009. The matching code was never pushed, so the
# deployed image (which knew only 001-008) could no longer resolve the
# database's own revision, exited non-zero, and took uvicorn down with it on
# every container start. `--autogenerate` is worse still: it diffs the models
# against whatever schema it connects to.
#
# Gated on ENVIRONMENT rather than an opt-in variable on purpose. render.yaml
# sets ENVIRONMENT=production in the container, which is the one place a remote
# target is correct -- the Dockerfile runs migrations at boot. An opt-in flag
# would have to be set there too, and forgetting it would brick startup.
_LOCAL_DB_HOSTS = {"localhost", "127.0.0.1", "::1", "", None}


def _guard_remote_target(url: str) -> None:
    from sqlalchemy.engine import make_url

    parsed = make_url(url)
    if parsed.host in _LOCAL_DB_HOSTS or settings.is_production:
        return
    raise RuntimeError(
        f"\n\nRefusing to run migrations against a non-local database with "
        f"ENVIRONMENT={settings.ENVIRONMENT!r}.\n"
        f"  host     : {parsed.host}\n"
        f"  database : {parsed.database}\n\n"
        f"Migrating production from a laptop is what caused the 2026-10-14 outage:\n"
        f"it stamps a revision the deployed image may not know, and the container\n"
        f"then dies at boot. Production migrations run in the container at startup\n"
        f"(see backend/docker-entrypoint.sh), so this should not be needed.\n\n"
        f"Point DATABASE_URL at local Postgres, or set ENVIRONMENT=production if you\n"
        f"genuinely intend to migrate the live database.\n"
    )


_guard_remote_target(settings.DATABASE_URL)

# Override sqlalchemy.url with our settings (reads from .env)
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# This is the metadata Alembic uses to detect model changes (autogenerate)
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    # Managed Postgres (Neon) requires TLS; local Postgres has none.
    connect_args = {"ssl": True} if settings.is_production else {}
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
        connect_args=connect_args,
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
