# worker/app/core/config.py
import os
import base64
import hashlib
from pathlib import Path
from typing import List, Optional
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

DEV_FERNET_KEY_SEED = b"comlina-local-dev-fernet-key-seed-2026"
DEV_DETERMINISTIC_FERNET_KEY = base64.urlsafe_b64encode(hashlib.sha256(DEV_FERNET_KEY_SEED).digest()).decode("utf-8")

PLACEHOLDER_SUBSTRINGS = (
    "your_",
    "placeholder",
    "change_me",
    "mock",
    "dev_secret",
    "example",
    "todo",
    "xxx",
)

def is_placeholder(val: Optional[str]) -> bool:
    if not val:
        return True
    lowered = val.lower().strip()
    return any(p in lowered for p in PLACEHOLDER_SUBSTRINGS)

def get_deterministic_dev_encryption_key(environment: str = "development") -> str:
    key = os.getenv("TOKEN_ENCRYPTION_KEY", "")
    if not key and environment == "development":
        key = DEV_DETERMINISTIC_FERNET_KEY
    return key

class WorkerSettings(BaseSettings):
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/comlina")
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    META_GRAPH_API_VERSION: str = os.getenv("META_GRAPH_API_VERSION", "v21.0")
    INSTAGRAM_ACCESS_TOKEN: str = os.getenv("INSTAGRAM_ACCESS_TOKEN", "")
    TOKEN_ENCRYPTION_KEY: str = os.getenv("TOKEN_ENCRYPTION_KEY", "")
    TOKEN_ENCRYPTION_KEYS: str = os.getenv("TOKEN_ENCRYPTION_KEYS", "")

    # DB pooling & SSL
    DB_POOL_SIZE: int = int(os.getenv("DB_POOL_SIZE", "10"))
    DB_MAX_OVERFLOW: int = int(os.getenv("DB_MAX_OVERFLOW", "20"))
    DB_POOL_TIMEOUT: int = int(os.getenv("DB_POOL_TIMEOUT", "30"))
    DB_POOL_RECYCLE: int = int(os.getenv("DB_POOL_RECYCLE", "1800"))
    DB_SSL: bool = os.getenv("DB_SSL", "").lower() in ("true", "1", "yes", "require")

    def get_encryption_keys(self) -> List[str]:
        keys = []
        if self.TOKEN_ENCRYPTION_KEYS:
            for k in self.TOKEN_ENCRYPTION_KEYS.split(","):
                k_clean = k.strip()
                if k_clean and k_clean not in keys:
                    keys.append(k_clean)
        if self.TOKEN_ENCRYPTION_KEY:
            k_clean = self.TOKEN_ENCRYPTION_KEY.strip()
            if k_clean and k_clean not in keys:
                keys.insert(0, k_clean)
        if not keys and self.ENVIRONMENT == "development":
            keys.append(DEV_DETERMINISTIC_FERNET_KEY)
        return keys

    def get_primary_encryption_key(self) -> str:
        keys = self.get_encryption_keys()
        return keys[0] if keys else ""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )

    def model_post_init(self, __context) -> None:
        if self.ENVIRONMENT == "development":
            if not self.TOKEN_ENCRYPTION_KEY and not self.TOKEN_ENCRYPTION_KEYS:
                self.TOKEN_ENCRYPTION_KEY = DEV_DETERMINISTIC_FERNET_KEY
        elif self.ENVIRONMENT == "production":
            self.validate_production_secrets()

    def validate_production_secrets(self) -> None:
        """Enforce fail-fast configuration for worker production deployments."""
        if self.ENVIRONMENT != "production":
            return

        # 1. DATABASE_URL
        if not self.DATABASE_URL or is_placeholder(self.DATABASE_URL):
            raise ValueError("Worker production error: DATABASE_URL must be set and cannot be a placeholder")
        if "sqlite" in self.DATABASE_URL.lower():
            raise ValueError("Worker production error: SQLite database fallback is strictly forbidden in production; PostgreSQL is required")
        if not (self.DATABASE_URL.startswith("postgresql://") or self.DATABASE_URL.startswith("postgres://") or self.DATABASE_URL.startswith("postgresql+")):
            raise ValueError("Worker production error: DATABASE_URL must be a PostgreSQL connection URL in production")

        # 2. REDIS_URL
        if not self.REDIS_URL or is_placeholder(self.REDIS_URL):
            raise ValueError("Worker production error: REDIS_URL must be set and cannot be a placeholder")
        if not (self.REDIS_URL.startswith("redis://") or self.REDIS_URL.startswith("rediss://")):
            raise ValueError("Worker production error: REDIS_URL must be a redis:// or rediss:// connection URL")

        # 3. TOKEN_ENCRYPTION_KEY(S)
        keys = self.get_encryption_keys()
        if not keys:
            raise ValueError("Worker production error: TOKEN_ENCRYPTION_KEY or TOKEN_ENCRYPTION_KEYS must be set in production")
        for k in keys:
            if is_placeholder(k):
                raise ValueError("Worker production error: TOKEN_ENCRYPTION_KEY cannot contain placeholder values")
            if k == DEV_DETERMINISTIC_FERNET_KEY:
                raise ValueError("Worker production error: TOKEN_ENCRYPTION_KEY cannot use auto-generated or default dev key in production")
            try:
                decoded = base64.urlsafe_b64decode(k.encode("utf-8"))
                if len(decoded) != 32:
                    raise ValueError()
            except Exception:
                raise ValueError("Worker production error: TOKEN_ENCRYPTION_KEY must be a valid 32-byte urlsafe base64-encoded key")

worker_settings = WorkerSettings()

if worker_settings.ENVIRONMENT == "production":
    worker_settings.validate_production_secrets()
