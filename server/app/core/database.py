# server/app/core/database.py
import asyncio
import socket
import logging
from pathlib import Path
from typing import AsyncGenerator, Optional
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
        sock.settimeout(1.5)
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0
    except Exception:
        return False

def normalize_async_database_url(url: str) -> str:
    """Normalize postgres:// or postgresql:// to postgresql+asyncpg://."""
    if not url:
        return url
    if url.startswith("postgres://"):
        return "postgresql+asyncpg://" + url[len("postgres://"):]
    elif url.startswith("postgresql://") and not url.startswith("postgresql+"):
        return "postgresql+asyncpg://" + url[len("postgresql://"):]
    return url

def resolve_database_url(configured_url: str, environment: str) -> str:
    """
    Resolve configured database URL, ensuring asyncpg dialect and preventing
    accidental SQLite fallback in production.
    """
    normalized = normalize_async_database_url(configured_url)
    if environment == "production":
        if not normalized or "sqlite" in normalized.lower() or not normalized.startswith("postgresql"):
            raise ValueError("Production error: SQLite database fallback is strictly prohibited in production. A valid PostgreSQL URL is required.")
        return normalized

    if environment == "development" and "postgresql" in normalized:
        parsed = urlparse(normalized.replace("postgresql+asyncpg://", "http://"))
        host = (parsed.hostname or "localhost").lower()
        if host in ("localhost", "127.0.0.1", "0.0.0.0") and not _is_service_reachable(normalized):
            logger.warning("[DEV] Local PostgreSQL is not reachable on port 5432. Falling back to SQLite development database: %s", SQLITE_DEV_PATH)
            return SQLITE_DEV_URL
    return normalized

def get_engine_args(db_url: str):
    """Sanitize URL and configure production connection pooling and SSL for asyncpg."""
    cleaned_url = normalize_async_database_url(db_url)
    connect_args = {}

    if "postgresql" in cleaned_url:
        parsed = urlparse(cleaned_url.replace("postgresql+asyncpg://", "http://"))
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
        cleaned_url = re.sub(r'([?&])sslmode=[^&]*(&)?', r'\1', cleaned_url)
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

async def _apply_schema_patches(conn) -> None:
    """Idempotently add newly added columns across both PostgreSQL and SQLite without data loss."""
    from sqlalchemy import text
    try:
        # Check dialect
        dialect_name = engine.dialect.name
        if dialect_name == "postgresql":
            await conn.execute(text("""
                ALTER TABLE instagram_accounts
                ADD COLUMN IF NOT EXISTS user_id UUID REFERENCES users(id) ON DELETE SET NULL,
                ADD COLUMN IF NOT EXISTS auth_method VARCHAR(64) NOT NULL DEFAULT 'META_INSTAGRAM_OAUTH',
                ADD COLUMN IF NOT EXISTS connection_status VARCHAR(32) NOT NULL DEFAULT 'CONNECTED',
                ADD COLUMN IF NOT EXISTS last_validated_at TIMESTAMPTZ,
                ADD COLUMN IF NOT EXISTS last_refreshed_at TIMESTAMPTZ,
                ADD COLUMN IF NOT EXISTS last_error_code VARCHAR(64),
                ADD COLUMN IF NOT EXISTS webhook_subscription_status VARCHAR(32) DEFAULT 'UNKNOWN',
                ADD COLUMN IF NOT EXISTS webhook_subscribed_at TIMESTAMPTZ;
            """))
            await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_ig_accounts_user_id ON instagram_accounts(user_id);"))
            await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_ig_accounts_status ON instagram_accounts(connection_status);"))
            await conn.execute(text("""
                ALTER TABLE contacts
                ADD COLUMN IF NOT EXISTS automation_state VARCHAR(64);
            """))
            await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_contacts_automation_state ON contacts(automation_state);"))
        elif dialect_name == "sqlite":
            res = await conn.execute(text("PRAGMA table_info(instagram_accounts)"))
            existing_cols = {row[1] for row in res.fetchall()}
            if "user_id" not in existing_cols:
                await conn.execute(text("ALTER TABLE instagram_accounts ADD COLUMN user_id TEXT"))
            if "auth_method" not in existing_cols:
                await conn.execute(text("ALTER TABLE instagram_accounts ADD COLUMN auth_method TEXT DEFAULT 'META_INSTAGRAM_OAUTH'"))
            if "connection_status" not in existing_cols:
                await conn.execute(text("ALTER TABLE instagram_accounts ADD COLUMN connection_status TEXT DEFAULT 'CONNECTED'"))
            if "last_validated_at" not in existing_cols:
                await conn.execute(text("ALTER TABLE instagram_accounts ADD COLUMN last_validated_at TIMESTAMP"))
            if "last_refreshed_at" not in existing_cols:
                await conn.execute(text("ALTER TABLE instagram_accounts ADD COLUMN last_refreshed_at TIMESTAMP"))
            if "last_error_code" not in existing_cols:
                await conn.execute(text("ALTER TABLE instagram_accounts ADD COLUMN last_error_code TEXT"))
            if "webhook_subscription_status" not in existing_cols:
                await conn.execute(text("ALTER TABLE instagram_accounts ADD COLUMN webhook_subscription_status TEXT DEFAULT 'UNKNOWN'"))
            if "webhook_subscribed_at" not in existing_cols:
                await conn.execute(text("ALTER TABLE instagram_accounts ADD COLUMN webhook_subscribed_at TIMESTAMP"))

            res_c = await conn.execute(text("PRAGMA table_info(contacts)"))
            contact_cols = {row[1] for row in res_c.fetchall()}
            if "automation_state" not in contact_cols:
                await conn.execute(text("ALTER TABLE contacts ADD COLUMN automation_state TEXT"))
    except Exception as patch_err:
        logger.debug(f"[DB] Schema patch check notice: {patch_err}")

_initialized = False
_init_lock: Optional[asyncio.Lock] = None

async def _ensure_db_initialized() -> None:
    global _initialized, _init_lock
    if not _initialized:
        if _init_lock is None:
            _init_lock = asyncio.Lock()
        async with _init_lock:
            if not _initialized:
                await init_db()
                _initialized = True

async def init_db() -> None:
    """Ensure database tables exist and schema patches are applied."""
    global _initialized
    try:
        import app.models  # noqa: F401 - ensure models are registered
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
            await _apply_schema_patches(conn)
        _initialized = True
        logger.info("[DB] Database schema checked/initialized successfully.")
    except Exception as e:
        logger.error(f"[DB] Error initializing database schema: {e}")

from contextlib import asynccontextmanager

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    await _ensure_db_initialized()
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

@asynccontextmanager
async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    await _ensure_db_initialized()
    session = AsyncSessionLocal()
    try:
        yield session
        await session.commit()
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()
