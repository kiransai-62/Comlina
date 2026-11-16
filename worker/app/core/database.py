# worker/app/core/database.py
# Re-exported from server.app.core.database (single source of truth)
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
SERVER_DIR = REPO_ROOT / "server"
if str(SERVER_DIR) not in sys.path:
    sys.path.insert(0, str(SERVER_DIR))

from server.app.core.database import *
from server.app.core.database import (
    Base,
    engine,
    SessionLocal,
    AsyncSessionLocal,
    database_url,
    get_db,
    get_db_session,
    init_db,
    resolve_database_url,
    get_engine_args,
    normalize_async_database_url,
    SQLITE_DEV_PATH,
    SQLITE_DEV_URL,
    _is_service_reachable,
    _ensure_db_initialized,
    _apply_schema_patches,
)

__all__ = [
    "Base",
    "engine",
    "SessionLocal",
    "AsyncSessionLocal",
    "database_url",
    "get_db",
    "get_db_session",
    "init_db",
    "resolve_database_url",
    "get_engine_args",
    "normalize_async_database_url",
    "SQLITE_DEV_PATH",
    "SQLITE_DEV_URL",
]
