# worker/app/core/config.py
import os
import base64
import hashlib
from pathlib import Path
from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

_curr_dir = Path(__file__).resolve()
_worker_dir = _curr_dir.parents[2]
_root_dir = _curr_dir.parents[3]
_server_dir = _root_dir / "server"
_client_dir = _root_dir / "client"

# Load in priority order (client/.env.local, then server/.env, worker/.env, then root .env, without overriding existing env)
for env_candidate in [
    _client_dir / ".env.local",
    _server_dir / ".env",
    _worker_dir / ".env",
    _root_dir / ".env",
]:
    if env_candidate.exists():
        load_dotenv(dotenv_path=env_candidate, override=False)

def get_deterministic_dev_encryption_key() -> str:
    key = os.getenv("TOKEN_ENCRYPTION_KEY", "")
    if not key:
        raw_seed = hashlib.sha256(b"comlina-local-dev-fernet-key-seed-2026").digest()
        key = base64.urlsafe_b64encode(raw_seed).decode("utf-8")
    return key

class WorkerSettings(BaseSettings):
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/comlina")
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    META_GRAPH_API_VERSION: str = os.getenv("META_GRAPH_API_VERSION", "v21.0")
    INSTAGRAM_ACCESS_TOKEN: str = os.getenv("INSTAGRAM_ACCESS_TOKEN", "")
    TOKEN_ENCRYPTION_KEY: str = get_deterministic_dev_encryption_key()

    # DB pooling & SSL
    DB_POOL_SIZE: int = int(os.getenv("DB_POOL_SIZE", "10"))
    DB_MAX_OVERFLOW: int = int(os.getenv("DB_MAX_OVERFLOW", "20"))
    DB_POOL_TIMEOUT: int = int(os.getenv("DB_POOL_TIMEOUT", "30"))
    DB_POOL_RECYCLE: int = int(os.getenv("DB_POOL_RECYCLE", "1800"))
    DB_SSL: bool = os.getenv("DB_SSL", "").lower() in ("true", "1", "yes", "require")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )

worker_settings = WorkerSettings()
