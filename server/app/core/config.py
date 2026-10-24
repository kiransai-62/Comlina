import os
import base64
import hashlib
from pathlib import Path
from typing import List, Union, Optional
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

DEV_FERNET_KEY_SEED = b"comlina-local-dev-fernet-key-seed-2026"
DEV_DETERMINISTIC_FERNET_KEY = base64.urlsafe_b64encode(hashlib.sha256(DEV_FERNET_KEY_SEED).digest()).decode("utf-8")
DEV_JWT_SECRET_SEED = b"comlina-local-dev-jwt-seed-2026"
DEV_DETERMINISTIC_JWT_SECRET = hashlib.sha256(DEV_JWT_SECRET_SEED).hexdigest()
LEGACY_DEV_JWT_HASH = "7690839f0e48e6970ec9cee3efdb57774c0ef99d0366f5f58a91202a3428d6b6"

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

def is_known_dev_jwt_secret(secret: str) -> bool:
    if not secret:
        return True
    h = hashlib.sha256(secret.encode("utf-8")).hexdigest()
    return h in (
        LEGACY_DEV_JWT_HASH,
        hashlib.sha256(DEV_DETERMINISTIC_JWT_SECRET.encode("utf-8")).hexdigest(),
    )

def get_deterministic_dev_encryption_key(environment: str = "development") -> str:
    key = os.getenv("TOKEN_ENCRYPTION_KEY", "")
    if not key and environment == "development":
        key = DEV_DETERMINISTIC_FERNET_KEY
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
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "https://vrfwgoigtmixkkunvrnw.supabase.co")
    SUPABASE_ANON_KEY: str = (
        os.getenv("SUPABASE_ANON_KEY", "")
        or os.getenv("SUPABASE_PUBLISHABLE_KEY", "")
        or os.getenv("NEXT_PUBLIC_SUPABASE_ANON_KEY", "")
    )
    SUPABASE_PUBLISHABLE_KEY: str = os.getenv("SUPABASE_PUBLISHABLE_KEY", "") or os.getenv("NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY", "")
    SUPABASE_JWKS_URL: str = os.getenv("SUPABASE_JWKS_URL", "")
    SUPABASE_SECRET_KEY: str = os.getenv("SUPABASE_SECRET_KEY", "")
    SUPABASE_JWT_SECRET: str = os.getenv("SUPABASE_JWT_SECRET", "")
    BACKEND_JWT_SECRET: str = os.getenv("BACKEND_JWT_SECRET", "")

    # Database & Redis Queue
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/comlina")
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    DB_POOL_SIZE: int = int(os.getenv("DB_POOL_SIZE", "10"))
    DB_MAX_OVERFLOW: int = int(os.getenv("DB_MAX_OVERFLOW", "20"))
    DB_POOL_TIMEOUT: int = int(os.getenv("DB_POOL_TIMEOUT", "30"))
    DB_POOL_RECYCLE: int = int(os.getenv("DB_POOL_RECYCLE", "1800"))
    DB_SSL: bool = os.getenv("DB_SSL", "").lower() in ("true", "1", "yes", "require")

    # Token Encryption (AES-256-GCM / MultiFernet)
    TOKEN_ENCRYPTION_KEY: str = os.getenv("TOKEN_ENCRYPTION_KEY", "")
    TOKEN_ENCRYPTION_KEYS: str = os.getenv("TOKEN_ENCRYPTION_KEYS", "")

    # Razorpay Payments & Subscriptions
    RAZORPAY_KEY_ID: str = os.getenv("RAZORPAY_KEY_ID", "")
    RAZORPAY_KEY_SECRET: str = os.getenv("RAZORPAY_KEY_SECRET", "")
    RAZORPAY_WEBHOOK_SECRET: str = os.getenv("RAZORPAY_WEBHOOK_SECRET", "")

    # Proxy trust & dev settings
    TRUSTED_PROXY_COUNT: int = int(os.getenv("TRUSTED_PROXY_COUNT", "0"))
    FAIL_CLOSED_ON_REDIS_DOWN: bool = os.getenv("FAIL_CLOSED_ON_REDIS_DOWN", "false").lower() in ("true", "1", "yes")
    ENABLE_DEV_ROUTES: bool = os.getenv("ENABLE_DEV_ROUTES", "false").lower() in ("true", "1", "yes")

    # CORS & Allowed Origins
    ALLOWED_ORIGINS: Union[List[str], str] = os.getenv("ALLOWED_ORIGINS", "")
    CORS_ORIGINS: Union[List[str], str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "https://app.comlina.ai",
        "https://comlina.ai",
        "https://comlina.onrender.com"
    ]

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

    def get_allowed_origins(self) -> List[str]:
        if self.ALLOWED_ORIGINS:
            if isinstance(self.ALLOWED_ORIGINS, list):
                return [str(o).strip() for o in self.ALLOWED_ORIGINS if str(o).strip()]
            val = str(self.ALLOWED_ORIGINS).strip()
            if val.startswith("["):
                import json
                try:
                    parsed = json.loads(val)
                    if isinstance(parsed, list):
                        return [str(i).strip() for i in parsed if str(i).strip()]
                except Exception:
                    pass
            origins = [o.strip() for o in val.split(",") if o.strip()]
            if origins:
                return origins
        if isinstance(self.CORS_ORIGINS, list):
            return [str(o).strip() for o in self.CORS_ORIGINS if str(o).strip()]
        return [str(self.CORS_ORIGINS).strip()]

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        allowed_env = os.getenv("ALLOWED_ORIGINS", "")
        if allowed_env:
            if allowed_env.startswith("["):
                import json
                try:
                    parsed = json.loads(allowed_env)
                    if isinstance(parsed, list):
                        return [str(i).strip() for i in parsed if str(i).strip()]
                except Exception:
                    pass
            origins = [i.strip() for i in allowed_env.split(",") if i.strip()]
            if origins:
                return origins

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

    def model_post_init(self, __context) -> None:
        if self.ENVIRONMENT == "development":
            if not self.SUPABASE_JWT_SECRET:
                self.SUPABASE_JWT_SECRET = DEV_DETERMINISTIC_JWT_SECRET
            if not self.BACKEND_JWT_SECRET:
                self.BACKEND_JWT_SECRET = self.SUPABASE_JWT_SECRET
            if not self.TOKEN_ENCRYPTION_KEY and not self.TOKEN_ENCRYPTION_KEYS:
                self.TOKEN_ENCRYPTION_KEY = DEV_DETERMINISTIC_FERNET_KEY
            if not self.RAZORPAY_KEY_ID:
                self.RAZORPAY_KEY_ID = "rzp_test_comlina2026"
            if not self.RAZORPAY_KEY_SECRET:
                self.RAZORPAY_KEY_SECRET = "dev_secret_razorpay_comlina_2026"
            if not self.RAZORPAY_WEBHOOK_SECRET:
                self.RAZORPAY_WEBHOOK_SECRET = "dev_webhook_secret_comlina_2026"
        elif self.ENVIRONMENT == "production":
            if not self.BACKEND_JWT_SECRET:
                self.BACKEND_JWT_SECRET = self.SUPABASE_JWT_SECRET
            self.validate_production_secrets()

    def validate_production_secrets(self) -> None:
        """Enforce fail-fast configuration for production deployments."""
        if self.ENVIRONMENT != "production":
            return

        # 1. DATABASE_URL
        if not self.DATABASE_URL or is_placeholder(self.DATABASE_URL):
            raise ValueError("Production error: DATABASE_URL must be set and cannot be a placeholder")
        if "sqlite" in self.DATABASE_URL.lower():
            raise ValueError("Production error: SQLite database fallback is strictly forbidden in production; PostgreSQL is required")
        if not (self.DATABASE_URL.startswith("postgresql://") or self.DATABASE_URL.startswith("postgres://") or self.DATABASE_URL.startswith("postgresql+")):
            raise ValueError("Production error: DATABASE_URL must be a PostgreSQL connection URL in production")

        # 2. REDIS_URL
        if not self.REDIS_URL or is_placeholder(self.REDIS_URL):
            raise ValueError("Production error: REDIS_URL must be set and cannot be a placeholder")
        if not (self.REDIS_URL.startswith("redis://") or self.REDIS_URL.startswith("rediss://")):
            raise ValueError("Production error: REDIS_URL must be a redis:// or rediss:// connection URL")

        # 3. SUPABASE_URL
        if not self.SUPABASE_URL or is_placeholder(self.SUPABASE_URL) or "your-project-ref" in self.SUPABASE_URL:
            raise ValueError("Production error: SUPABASE_URL must be configured with a real project URL")
        if not self.SUPABASE_URL.startswith("https://"):
            raise ValueError("Production error: SUPABASE_URL must use HTTPS")

        # 4. JWT verification key material
        jwt_secret = self.BACKEND_JWT_SECRET or self.SUPABASE_JWT_SECRET
        has_valid_secret = bool(
            jwt_secret
            and not is_placeholder(jwt_secret)
            and not is_known_dev_jwt_secret(jwt_secret)
            and len(jwt_secret) >= 32
        )
        has_valid_jwks = bool(
            self.SUPABASE_JWKS_URL
            and self.SUPABASE_JWKS_URL.startswith("https://")
            and not is_placeholder(self.SUPABASE_JWKS_URL)
        )
        if not (has_valid_secret or has_valid_jwks):
            raise ValueError(
                "Production error: Strong JWT verification key material is required. "
                "Provide a non-default SUPABASE_JWT_SECRET/BACKEND_JWT_SECRET (>= 32 chars) or a valid HTTPS SUPABASE_JWKS_URL"
            )

        # 5. TOKEN_ENCRYPTION_KEY(S)
        keys = self.get_encryption_keys()
        if not keys:
            raise ValueError("Production error: TOKEN_ENCRYPTION_KEY or TOKEN_ENCRYPTION_KEYS must be set in production")
        for k in keys:
            if is_placeholder(k):
                raise ValueError("Production error: TOKEN_ENCRYPTION_KEY cannot contain placeholder values")
            if k == DEV_DETERMINISTIC_FERNET_KEY:
                raise ValueError("Production error: TOKEN_ENCRYPTION_KEY cannot use auto-generated or default dev key in production")
            try:
                decoded = base64.urlsafe_b64decode(k.encode("utf-8"))
                if len(decoded) != 32:
                    raise ValueError()
            except Exception:
                raise ValueError("Production error: TOKEN_ENCRYPTION_KEY must be a valid 32-byte urlsafe base64-encoded key")

        # 6. META_APP_ID
        if not self.META_APP_ID or is_placeholder(self.META_APP_ID):
            raise ValueError("Production error: META_APP_ID must be configured for Meta integrations")

        # 7. META_APP_SECRET
        if not self.META_APP_SECRET or is_placeholder(self.META_APP_SECRET) or len(self.META_APP_SECRET) < 16:
            raise ValueError("Production error: META_APP_SECRET must be configured with a valid secret (>= 16 chars)")

        # 8. META_WEBHOOK_VERIFY_TOKEN
        if not self.META_WEBHOOK_VERIFY_TOKEN or is_placeholder(self.META_WEBHOOK_VERIFY_TOKEN) or len(self.META_WEBHOOK_VERIFY_TOKEN) < 16:
            raise ValueError("Production error: META_WEBHOOK_VERIFY_TOKEN must be configured with a strong secret (>= 16 chars)")

        # 9. ALLOWED_ORIGINS
        origins = self.get_allowed_origins()
        if not origins:
            raise ValueError("Production error: ALLOWED_ORIGINS must be configured in production")
        if "*" in origins:
            raise ValueError("Production error: Wildcard '*' in ALLOWED_ORIGINS is prohibited in production")
        for origin in origins:
            if not origin.startswith("https://"):
                raise ValueError(f"Production error: Insecure HTTP origin '{origin}' forbidden in production; HTTPS required")

        # 10. RAZORPAY secrets
        if not self.RAZORPAY_KEY_ID or is_placeholder(self.RAZORPAY_KEY_ID):
            raise ValueError("Production error: RAZORPAY_KEY_ID must be configured for payment processing")
        if not self.RAZORPAY_KEY_SECRET or is_placeholder(self.RAZORPAY_KEY_SECRET) or len(self.RAZORPAY_KEY_SECRET) < 12:
            raise ValueError("Production error: RAZORPAY_KEY_SECRET must be a valid secret (>= 12 chars)")
        if not self.RAZORPAY_WEBHOOK_SECRET or is_placeholder(self.RAZORPAY_WEBHOOK_SECRET) or len(self.RAZORPAY_WEBHOOK_SECRET) < 16:
            raise ValueError("Production error: RAZORPAY_WEBHOOK_SECRET must be set to a strong secret (>= 16 chars) to prevent unauthenticated plan upgrades")

        # 10. Razorpay Payments Configuration
        if not self.RAZORPAY_KEY_ID or is_placeholder(self.RAZORPAY_KEY_ID) or self.RAZORPAY_KEY_ID == "rzp_test_comlina2026":
            raise ValueError("Production error: RAZORPAY_KEY_ID must be set to a valid production key in production")
        if not self.RAZORPAY_KEY_SECRET or is_placeholder(self.RAZORPAY_KEY_SECRET) or self.RAZORPAY_KEY_SECRET == "dev_secret_razorpay_comlina_2026":
            raise ValueError("Production error: RAZORPAY_KEY_SECRET must be set to a valid secret in production")
        if not self.RAZORPAY_WEBHOOK_SECRET or is_placeholder(self.RAZORPAY_WEBHOOK_SECRET) or self.RAZORPAY_WEBHOOK_SECRET == "dev_webhook_secret_comlina_2026":
            raise ValueError("Production error: RAZORPAY_WEBHOOK_SECRET must be set to a valid webhook secret in production")

settings = Settings()

if settings.ENVIRONMENT == "production":
    settings.validate_production_secrets()

worker_settings = settings
