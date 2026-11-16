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
SessionLocal = AsyncSessionLocal

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
                ADD COLUMN IF NOT EXISTS webhook_subscribed_at TIMESTAMPTZ,
                ADD COLUMN IF NOT EXISTS ig_business_account_id VARCHAR(100),
                ADD COLUMN IF NOT EXISTS token_type VARCHAR(32) NOT NULL DEFAULT 'long_lived',
                ADD COLUMN IF NOT EXISTS is_connected BOOLEAN NOT NULL DEFAULT TRUE,
                ADD COLUMN IF NOT EXISTS scopes JSONB NOT NULL DEFAULT '[]'::jsonb,
                ADD COLUMN IF NOT EXISTS last_error TEXT;
            """))
            await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_ig_accounts_user_id ON instagram_accounts(user_id);"))
            await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_ig_accounts_status ON instagram_accounts(connection_status);"))
            await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_ig_accounts_business_id ON instagram_accounts(ig_business_account_id);"))
            await conn.execute(text("""
                ALTER TABLE automations
                ADD COLUMN IF NOT EXISTS user_id UUID REFERENCES users(id) ON DELETE SET NULL,
                ADD COLUMN IF NOT EXISTS media_id VARCHAR(100) NOT NULL DEFAULT 'ALL',
                ADD COLUMN IF NOT EXISTS match_mode VARCHAR(32) NOT NULL DEFAULT 'CONTAINS',
                ADD COLUMN IF NOT EXISTS keywords JSONB NOT NULL DEFAULT '[]'::jsonb,
                ADD COLUMN IF NOT EXISTS follow_condition JSONB NOT NULL DEFAULT '{"enabled": false}'::jsonb,
                ADD COLUMN IF NOT EXISTS response_config JSONB NOT NULL DEFAULT '{}'::jsonb,
                ADD COLUMN IF NOT EXISTS is_active BOOLEAN NOT NULL DEFAULT TRUE,
                ADD COLUMN IF NOT EXISTS stats_triggered INTEGER NOT NULL DEFAULT 0,
                ADD COLUMN IF NOT EXISTS stats_comments_replied INTEGER NOT NULL DEFAULT 0;
            """))
            await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_automations_execution_lookup ON automations(instagram_account_id, is_active, status, media_id);"))
            await conn.execute(text("""
                CREATE TABLE IF NOT EXISTS automation_executions (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    workspace_id UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
                    automation_id UUID NOT NULL REFERENCES automations(id) ON DELETE CASCADE,
                    instagram_account_id UUID NOT NULL REFERENCES instagram_accounts(id) ON DELETE CASCADE,
                    comment_id VARCHAR(100) NOT NULL,
                    media_id VARCHAR(100),
                    commenter_ig_id VARCHAR(100) NOT NULL,
                    trigger_type VARCHAR(32) NOT NULL,
                    matched_keyword VARCHAR(255),
                    follower_status VARCHAR(32) NOT NULL DEFAULT 'UNKNOWN',
                    execution_status VARCHAR(32) NOT NULL,
                    error_message TEXT,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    UNIQUE(automation_id, comment_id)
                );
            """))
            await conn.execute(text("""
                ALTER TABLE contacts
                ADD COLUMN IF NOT EXISTS automation_state VARCHAR(64);
            """))
            await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_contacts_automation_state ON contacts(automation_state);"))
            # F13 fix: dedicated password_hash column so profile updates cannot overwrite auth material
            await conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS password_hash VARCHAR(512);"))
            await conn.execute(text("ALTER TABLE webhook_events ADD COLUMN IF NOT EXISTS attempt_count INTEGER DEFAULT 1;"))
            await conn.execute(text("ALTER TABLE webhook_events ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP;"))

            # RLS Helper functions: Safe dual-context resolver (Supabase auth.uid() + FastAPI app.current_user_id)
            try:
                await conn.execute(text("""
                    CREATE OR REPLACE FUNCTION public.current_app_user_id()
                    RETURNS UUID
                    LANGUAGE plpgsql
                    STABLE
                    SECURITY DEFINER
                    SET search_path = public
                    AS $$
                    DECLARE
                        raw_setting TEXT;
                        supa_uid UUID;
                    BEGIN
                        BEGIN
                            supa_uid := auth.uid();
                            IF supa_uid IS NOT NULL THEN
                                RETURN supa_uid;
                            END IF;
                        EXCEPTION WHEN OTHERS THEN
                            supa_uid := NULL;
                        END;

                        raw_setting := NULLIF(BTRIM(current_setting('app.current_user_id', true)), '');
                        IF raw_setting IS NULL THEN
                            RETURN NULL;
                        END IF;

                        RETURN raw_setting::UUID;
                    EXCEPTION WHEN OTHERS THEN
                        RETURN NULL;
                    END;
                    $$;

                    CREATE OR REPLACE FUNCTION public.is_workspace_member(ws_id UUID)
                    RETURNS BOOLEAN
                    LANGUAGE plpgsql
                    STABLE
                    SECURITY DEFINER
                    SET search_path = public
                    AS $$
                    DECLARE
                        active_uid UUID;
                    BEGIN
                        active_uid := public.current_app_user_id();
                        IF active_uid IS NULL OR ws_id IS NULL THEN
                            RETURN FALSE;
                        END IF;

                        RETURN EXISTS (
                            SELECT 1
                            FROM public.workspace_members wm
                            WHERE wm.workspace_id = ws_id
                              AND wm.user_id = active_uid
                        );
                    END;
                    $$;
                """))
            except Exception as rls_err:
                logger.debug(f"[DB] RLS function patch notice: {rls_err}")
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
            if "ig_business_account_id" not in existing_cols:
                await conn.execute(text("ALTER TABLE instagram_accounts ADD COLUMN ig_business_account_id TEXT"))
            if "token_type" not in existing_cols:
                await conn.execute(text("ALTER TABLE instagram_accounts ADD COLUMN token_type TEXT DEFAULT 'long_lived'"))
            if "is_connected" not in existing_cols:
                await conn.execute(text("ALTER TABLE instagram_accounts ADD COLUMN is_connected BOOLEAN DEFAULT 1"))
            if "scopes" not in existing_cols:
                await conn.execute(text("ALTER TABLE instagram_accounts ADD COLUMN scopes TEXT DEFAULT '[]'"))
            if "last_error" not in existing_cols:
                await conn.execute(text("ALTER TABLE instagram_accounts ADD COLUMN last_error TEXT"))

            res_a = await conn.execute(text("PRAGMA table_info(automations)"))
            auto_cols = {row[1] for row in res_a.fetchall()}
            if "user_id" not in auto_cols:
                await conn.execute(text("ALTER TABLE automations ADD COLUMN user_id TEXT"))
            if "media_id" not in auto_cols:
                await conn.execute(text("ALTER TABLE automations ADD COLUMN media_id TEXT DEFAULT 'ALL'"))
            if "match_mode" not in auto_cols:
                await conn.execute(text("ALTER TABLE automations ADD COLUMN match_mode TEXT DEFAULT 'CONTAINS'"))
            if "keywords" not in auto_cols:
                await conn.execute(text("ALTER TABLE automations ADD COLUMN keywords TEXT DEFAULT '[]'"))
            if "follow_condition" not in auto_cols:
                await conn.execute(text("ALTER TABLE automations ADD COLUMN follow_condition TEXT DEFAULT '{\"enabled\": false}'"))
            if "response_config" not in auto_cols:
                await conn.execute(text("ALTER TABLE automations ADD COLUMN response_config TEXT DEFAULT '{}'"))
            if "is_active" not in auto_cols:
                await conn.execute(text("ALTER TABLE automations ADD COLUMN is_active BOOLEAN DEFAULT 1"))
            if "stats_triggered" not in auto_cols:
                await conn.execute(text("ALTER TABLE automations ADD COLUMN stats_triggered INTEGER DEFAULT 0"))
            if "stats_comments_replied" not in auto_cols:
                await conn.execute(text("ALTER TABLE automations ADD COLUMN stats_comments_replied INTEGER DEFAULT 0"))

            await conn.execute(text("""
                CREATE TABLE IF NOT EXISTS automation_executions (
                    id TEXT PRIMARY KEY,
                    workspace_id TEXT NOT NULL,
                    automation_id TEXT NOT NULL,
                    instagram_account_id TEXT NOT NULL,
                    comment_id TEXT NOT NULL,
                    media_id TEXT,
                    commenter_ig_id TEXT NOT NULL,
                    trigger_type TEXT NOT NULL,
                    matched_keyword TEXT,
                    follower_status TEXT DEFAULT 'UNKNOWN',
                    execution_status TEXT NOT NULL,
                    error_message TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(automation_id, comment_id)
                );
            """))

            res_c = await conn.execute(text("PRAGMA table_info(contacts)"))
            contact_cols = {row[1] for row in res_c.fetchall()}
            if "automation_state" not in contact_cols:
                await conn.execute(text("ALTER TABLE contacts ADD COLUMN automation_state TEXT"))

            # F13 fix: dedicated password_hash column so profile updates cannot overwrite auth material
            res_u = await conn.execute(text("PRAGMA table_info(users)"))
            user_cols = {row[1] for row in res_u.fetchall()}
            if "password_hash" not in user_cols:
                await conn.execute(text("ALTER TABLE users ADD COLUMN password_hash TEXT"))

            res_w = await conn.execute(text("PRAGMA table_info(webhook_events)"))
            wh_cols = {row[1] for row in res_w.fetchall()}
            if "attempt_count" not in wh_cols:
                await conn.execute(text("ALTER TABLE webhook_events ADD COLUMN attempt_count INTEGER DEFAULT 1"))
            if "updated_at" not in wh_cols:
                await conn.execute(text("ALTER TABLE webhook_events ADD COLUMN updated_at TIMESTAMP"))
    except Exception as patch_err:
        logger.debug(f"[DB] Schema patch check notice: {patch_err}")

_initialized = False

async def _ensure_db_initialized() -> None:
    global _initialized
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
