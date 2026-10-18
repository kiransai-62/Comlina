# worker/app/core/database.py
import logging, socket
from pathlib import Path
from urllib.parse import urlparse
from typing import AsyncGenerator
from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase
from app.core.config import worker_settings

logger = logging.getLogger(__name__)

# Must match server: <repo>/server/comlina_dev.db
SQLITE_DEV_PATH = Path(__file__).resolve().parents[3] / "server" / "comlina_dev.db"
SQLITE_DEV_URL = f"sqlite+aiosqlite:///{SQLITE_DEV_PATH.as_posix()}"


class Base(DeclarativeBase):
    pass


def _is_service_reachable(url_str: str) -> bool:
    try:
        parsed = urlparse(url_str.replace("postgresql+asyncpg://", "http://"))
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1.5)
        result = sock.connect_ex((parsed.hostname or "localhost", parsed.port or 5432))
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
            logger.warning("[DEV] PostgreSQL not reachable. Worker falling back to %s", SQLITE_DEV_PATH)
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

        # Check for SSL requirement from query string or remote host
        is_remote = host not in ("localhost", "127.0.0.1", "0.0.0.0", "postgres")
        requires_ssl = (
            "sslmode=require" in query or
            "ssl=require" in query or
            getattr(worker_settings, "DB_SSL", False) or
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
            "echo": worker_settings.ENVIRONMENT == "development",
            "future": True,
            "pool_pre_ping": True,
            "pool_size": getattr(worker_settings, "DB_POOL_SIZE", 10),
            "max_overflow": getattr(worker_settings, "DB_MAX_OVERFLOW", 20),
            "pool_timeout": getattr(worker_settings, "DB_POOL_TIMEOUT", 30),
            "pool_recycle": getattr(worker_settings, "DB_POOL_RECYCLE", 1800),
        }
        if connect_args:
            engine_kwargs["connect_args"] = connect_args
        return cleaned_url, engine_kwargs

    # SQLite development configuration
    return cleaned_url, {
        "echo": worker_settings.ENVIRONMENT == "development",
        "future": True,
        "pool_pre_ping": True,
    }

database_url = resolve_database_url(worker_settings.DATABASE_URL, worker_settings.ENVIRONMENT)
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

@asynccontextmanager
async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Async context manager providing a scoped database session with automatic commit/rollback.
    """
    session = AsyncSessionLocal()
    try:
        yield session
        await session.commit()
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()
