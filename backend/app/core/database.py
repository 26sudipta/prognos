from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings

# Managed Postgres (e.g. Neon) requires TLS. asyncpg opens a default SSL
# context when `ssl=True`. Enabled in production only — local Postgres has
# no TLS. Use Neon's *direct* endpoint; if its pooled (-pooler) endpoint is
# ever used, also set statement_cache_size=0 (asyncpg + PgBouncer breaks
# prepared statements).
_connect_args = {"ssl": True} if settings.is_production else {}

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.ENVIRONMENT == "development",
    pool_pre_ping=True,
    connect_args=_connect_args,
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session
