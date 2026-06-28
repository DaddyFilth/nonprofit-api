import os

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base

# Use env var, default to local SQLite DB for easy dev
DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "sqlite+aiosqlite:///./nonprofit.db",
)

# Detect if we should use async engine
is_async = "sqlite+aiosqlite" in DATABASE_URL or "postgresql+asyncpg" in DATABASE_URL

if is_async:
    engine = create_async_engine(
        DATABASE_URL,
        echo=False,
        future=True,
    )
    AsyncSessionLocal = async_sessionmaker(
        engine,
        expire_on_commit=False,
    )
else:
    # Fallback for sync tools like Alembic
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    engine = create_engine(DATABASE_URL.replace("+aiosqlite", "").replace("+asyncpg", ""))
    AsyncSessionLocal = sessionmaker(bind=engine)

Base = declarative_base()


async def get_session() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session
