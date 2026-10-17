# server/app/core/database.py
import socket
import logging
from pathlib import Path
from typing import AsyncGenerator
from urllib.parse import urlparse
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase
from app.core.config import settings

logger = logging.getLogger(__name__)

SQLITE_DEV_PATH = Path(__file__).resolve().parents[2] / "comlina_dev.db"
SQLITE_DEV_URL = f"sqlite+aiosqlite:///{SQLITE_DEV_PATH.as_posix()}"

class Base(DeclarativeBase):
    pass

def _is_service_reachable(url_str: str) -> bool:
    """Quick socket check to verify database host/port is reachable."""
    try:
        parsed = urlparse(url_str.replace("postgresql+asyncpg://", "http://"))
        host = parsed.hostname or "localhost"
        port = parsed.port or 5432
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(0.3)
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0
    except Exception:
        return False

def resolve_database_url(configured_url: str, environment: str) -> str:
    """Resolve configured database URL, falling back to SQLite in development if PostgreSQL is unreachable."""
    if environment == "development" and "postgresql" in configured_url:
        parsed = urlparse(configured_url.replace("postgresql+asyncpg://", "http://").replace("postgresql://", "http://"))
        host = (parsed.hostname or "localhost").lower()
        if host in ("localhost", "127.0.0.1", "0.0.0.0") and not _is_service_reachable(configured_url):
            logger.warning("[DEV] Local PostgreSQL is not reachable on port 5432. Falling back to SQLite development database: %s", SQLITE_DEV_PATH)
            return SQLITE_DEV_URL
    return configured_url

def get_engine_args(db_url: str):
    """Sanitize URL and configure production connection pooling and SSL for asyncpg."""
    cleaned_url = db_url
    connect_args = {}

    if "postgresql" in db_url:
        parsed = urlparse(db_url.replace("postgresql+asyncpg://", "http://").replace("postgresql://", "http://"))
        host = (parsed.hostname or "").lower()
        query = parsed.query.lower()

        # Check for SSL requirement from query string, settings, or remote host
        is_remote = host not in ("localhost", "127.0.0.1", "0.0.0.0", "postgres")
        requires_ssl = (
            "sslmode=require" in query or
            "ssl=require" in query or
            getattr(settings, "DB_SSL", False) or
            (is_remote and "sslmode=disable" not in query and "ssl=disable" not in query)
        )

        if requires_ssl:
            connect_args["ssl"] = "require"

        # Strip sslmode/ssl query parameter from asyncpg URL to prevent TypeError in asyncpg.connect()
        import re
        cleaned_url = re.sub(r'([?&])sslmode=[^&]*(&)?', r'\1', db_url)
        cleaned_url = re.sub(r'([?&])ssl=[^&]*(&)?', r'\1', cleaned_url)
        cleaned_url = cleaned_url.rstrip('?&')

        engine_kwargs = {
            "echo": False,
            "future": True,
            "pool_pre_ping": True,
            "pool_size": getattr(settings, "DB_POOL_SIZE", 10),
            "max_overflow": getattr(settings, "DB_MAX_OVERFLOW", 20),
            "pool_timeout": getattr(settings, "DB_POOL_TIMEOUT", 30),
            "pool_recycle": getattr(settings, "DB_POOL_RECYCLE", 1800),
        }
        if connect_args:
            engine_kwargs["connect_args"] = connect_args
        return cleaned_url, engine_kwargs

    # SQLite development configuration
    return cleaned_url, {
        "echo": False,
        "future": True,
        "pool_pre_ping": True,
    }

# In development, gracefully fall back to local SQLite if PostgreSQL is not currently running
database_url = resolve_database_url(settings.DATABASE_URL, settings.ENVIRONMENT)
_effective_url, _engine_kwargs = get_engine_args(database_url)

engine = create_async_engine(
    _effective_url,
    **_engine_kwargs
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
    class_=AsyncSession
)

async def init_db() -> None:
    """Ensure database tables exist (particularly in dev or sqlite mode)."""
    try:
        import app.models  # noqa: F401 - ensure models are registered
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("[DB] Database schema checked/initialized successfully.")
    except Exception as e:
        logger.error(f"[DB] Error initializing database schema: {e}")

from contextlib import asynccontextmanager

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

@asynccontextmanager
async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    session = AsyncSessionLocal()
    try:
        yield session
        await session.commit()
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()
