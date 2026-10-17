import os
import base64
import hashlib
from pathlib import Path
from typing import List, Union
from dotenv import load_dotenv
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# 1. Automatically bridge environment variables from all possible locations
_curr_dir = Path(__file__).resolve()
_server_dir = _curr_dir.parents[2]
_root_dir = _curr_dir.parents[3]
_client_dir = _root_dir / "client"
_worker_dir = _root_dir / "worker"

# Load in priority order (client/.env.local, then server/.env, worker/.env, then root .env, without overriding existing env)
for env_candidate in [
    _client_dir / ".env.local",
    _server_dir / ".env",
    _worker_dir / ".env",
    _root_dir / ".env",
]:
    if env_candidate.exists():
        load_dotenv(dotenv_path=env_candidate, override=False)

# Normalize cross-framework env variable names
if not os.getenv("SUPABASE_URL") and os.getenv("NEXT_PUBLIC_SUPABASE_URL"):
    os.environ["SUPABASE_URL"] = os.getenv("NEXT_PUBLIC_SUPABASE_URL", "")

if not os.getenv("SUPABASE_ANON_KEY") and os.getenv("NEXT_PUBLIC_SUPABASE_ANON_KEY"):
    os.environ["SUPABASE_ANON_KEY"] = os.getenv("NEXT_PUBLIC_SUPABASE_ANON_KEY", "")

def get_deterministic_dev_encryption_key() -> str:
    key = os.getenv("TOKEN_ENCRYPTION_KEY", "")
    if not key:
        raw_seed = hashlib.sha256(b"comlina-local-dev-fernet-key-seed-2026").digest()
        key = base64.urlsafe_b64encode(raw_seed).decode("utf-8")
    return key


class Settings(BaseSettings):
    PROJECT_NAME: str = "Comlina API"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api"
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")

    # Meta Graph API Configuration
    META_APP_ID: str = os.getenv("META_APP_ID", "")
    META_APP_SECRET: str = os.getenv("META_APP_SECRET", "")
    META_WEBHOOK_VERIFY_TOKEN: str = os.getenv("META_WEBHOOK_VERIFY_TOKEN", "")
    META_GRAPH_API_VERSION: str = os.getenv("META_GRAPH_API_VERSION", "v21.0")
    META_REDIRECT_URI: str = os.getenv("META_REDIRECT_URI", "http://localhost:3000/connect/instagram")
    INSTAGRAM_ACCESS_TOKEN: str = os.getenv("INSTAGRAM_ACCESS_TOKEN", "")

    # Supabase & Authentication
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
    SUPABASE_ANON_KEY: str = os.getenv("SUPABASE_ANON_KEY", "") or os.getenv("SUPABASE_PUBLISHABLE_KEY", "")
    SUPABASE_PUBLISHABLE_KEY: str = os.getenv("SUPABASE_PUBLISHABLE_KEY", "") or os.getenv("NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY", "")
    SUPABASE_JWKS_URL: str = os.getenv("SUPABASE_JWKS_URL", "") or (f"{os.getenv('SUPABASE_URL', '').rstrip('/')}/auth/v1/.well-known/jwks.json" if os.getenv("SUPABASE_URL") else "")
    SUPABASE_SECRET_KEY: str = os.getenv("SUPABASE_SECRET_KEY", "")
    SUPABASE_JWT_SECRET: str = os.getenv("SUPABASE_JWT_SECRET", "dev-jwt-secret-comlina-2026")
    BACKEND_JWT_SECRET: str = os.getenv("BACKEND_JWT_SECRET") or os.getenv("SUPABASE_JWT_SECRET") or "dev-jwt-secret-comlina-2026"

    # Database & Redis Queue
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/comlina")
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    DB_POOL_SIZE: int = int(os.getenv("DB_POOL_SIZE", "10"))
    DB_MAX_OVERFLOW: int = int(os.getenv("DB_MAX_OVERFLOW", "20"))
    DB_POOL_TIMEOUT: int = int(os.getenv("DB_POOL_TIMEOUT", "30"))
    DB_POOL_RECYCLE: int = int(os.getenv("DB_POOL_RECYCLE", "1800"))
    DB_SSL: bool = os.getenv("DB_SSL", "").lower() in ("true", "1", "yes", "require")

    # Token Encryption (AES-256-GCM / Fernet)
    TOKEN_ENCRYPTION_KEY: str = get_deterministic_dev_encryption_key()

    # Razorpay Payments & Subscriptions
    RAZORPAY_KEY_ID: str = os.getenv("RAZORPAY_KEY_ID", "rzp_test_comlina2026")
    RAZORPAY_KEY_SECRET: str = os.getenv("RAZORPAY_KEY_SECRET", "dev_secret_razorpay_comlina_2026")
    RAZORPAY_WEBHOOK_SECRET: str = os.getenv("RAZORPAY_WEBHOOK_SECRET", "dev_webhook_secret_comlina_2026")

    # CORS
    CORS_ORIGINS: Union[List[str], str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "https://app.comlina.ai",
        "https://comlina.ai",
        "https://comlina.onrender.com"
    ]

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str):
            if v.startswith("["):
                import json
                try:
                    parsed = json.loads(v)
                    if isinstance(parsed, list):
                        return [str(i).strip() for i in parsed if str(i).strip()]
                except Exception:
                    pass
            origins = [i.strip() for i in v.split(",") if i.strip()]
            return origins if origins else ["http://localhost:3000", "https://app.comlina.ai", "https://comlina.onrender.com"]
        elif isinstance(v, list):
            return [str(i).strip() for i in v if str(i).strip()]
        return ["http://localhost:3000", "https://app.comlina.ai", "https://comlina.onrender.com"]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )

    def validate_production_secrets(self) -> None:
        """Enforce that production deployments have real, cryptographically secure secrets."""
        if self.ENVIRONMENT != "development":
            if not self.TOKEN_ENCRYPTION_KEY or len(self.TOKEN_ENCRYPTION_KEY) < 32:
                raise ValueError("Production error: TOKEN_ENCRYPTION_KEY must be a valid 32-byte base64 key")
            if not self.SUPABASE_JWT_SECRET or "mock" in self.SUPABASE_JWT_SECRET.lower():
                raise ValueError("Production error: SUPABASE_JWT_SECRET must be configured with a valid secret")
            if not self.META_APP_SECRET or "mock" in self.META_APP_SECRET.lower():
                raise ValueError("Production error: META_APP_SECRET must be configured for Meta integrations")
            if not self.META_WEBHOOK_VERIFY_TOKEN or "mock" in self.META_WEBHOOK_VERIFY_TOKEN.lower() or "your_" in self.META_WEBHOOK_VERIFY_TOKEN.lower():
                raise ValueError("Production error: META_WEBHOOK_VERIFY_TOKEN must be configured with a strong secret")
            if "*" in self.CORS_ORIGINS:
                raise ValueError("Production error: Wildcard '*' in CORS_ORIGINS is prohibited when credentials are enabled")

settings = Settings()

if settings.ENVIRONMENT != "development":
    settings.validate_production_secrets()

worker_settings = settings
