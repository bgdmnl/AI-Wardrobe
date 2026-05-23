import logging
from pathlib import Path
from typing import Optional

from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.config import settings

logger = logging.getLogger(__name__)

# SQLite file lives in backend/ (same folder as when running uvicorn)
_BACKEND_DIR = Path(__file__).resolve().parent.parent
SQLITE_URL = f"sqlite+aiosqlite:///{(_BACKEND_DIR / 'wardrobe.db').as_posix()}"


class Base(DeclarativeBase):
    pass


engine = None
async_session = None
active_database_url: Optional[str] = None
_db_initialized = False


def setup_database(url: str) -> None:
    global engine, async_session, active_database_url
    logged_url = url
    if "@" in url:
        parts = url.split("@")
        logged_url = f"{parts[0].split(':')[0]}://***:***@{parts[1]}"
    logger.info(f"Database: {logged_url}")

    connect_args = {}
    if url.startswith("sqlite"):
        connect_args["timeout"] = 30

    engine = create_async_engine(url, connect_args=connect_args, echo=False)
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    active_database_url = url


async def resolve_database_url() -> str:
    """Use configured URL, or fall back to SQLite if PostgreSQL is unreachable."""
    url = settings.DATABASE_URL
    if not url.startswith("postgresql"):
        return url

    probe = create_async_engine(url, connect_args={}, pool_pre_ping=True)
    try:
        async with probe.connect() as conn:
            await conn.execute(text("SELECT 1"))
        logger.info("PostgreSQL is reachable")
        return url
    except Exception as e:
        logger.warning(
            f"PostgreSQL not available ({e}). "
            f"Using local SQLite: {SQLITE_URL}"
        )
        return SQLITE_URL
    finally:
        await probe.dispose()


async def get_db():
    global async_session
    if async_session is None:
        raise RuntimeError("Database not initialized — wait for app startup")
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()


async def _migrate_columns(conn):
    """Add columns introduced after first deploy (SQLite / Postgres)."""
    dialect = conn.dialect.name
    if dialect == "sqlite":
        result = await conn.execute(text("PRAGMA table_info(clothing_items)"))
        columns = {row[1] for row in result.fetchall()}
        if "user_label" not in columns:
            await conn.execute(
                text("ALTER TABLE clothing_items ADD COLUMN user_label VARCHAR(255)")
            )
            logger.info("Added user_label column to clothing_items")
    else:
        await conn.execute(
            text(
                "ALTER TABLE clothing_items "
                "ADD COLUMN IF NOT EXISTS user_label VARCHAR(255)"
            )
        )


async def init_db():
    global _db_initialized
    url = await resolve_database_url()
    setup_database(url)

    logger.info("Initializing database tables...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        await _migrate_columns(conn)

    _db_initialized = True
    logger.info("Database tables initialized successfully")
