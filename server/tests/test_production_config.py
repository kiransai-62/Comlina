import os
import base64
import pytest
from app.core.config import (
    Settings,
    DEV_DETERMINISTIC_FERNET_KEY,
    DEV_DETERMINISTIC_JWT_SECRET,
)
from app.core.database import resolve_database_url as server_resolve_db
from worker.app.core.config import WorkerSettings
from worker.app.core.database import resolve_database_url as worker_resolve_db

VALID_FERNET_KEY = base64.urlsafe_b64encode(b"12345678901234567890123456789012").decode("utf-8")
VALID_FERNET_KEY_2 = base64.urlsafe_b64encode(b"abcdefghijklmnopqrstuvwxyz123456").decode("utf-8")

def get_base_valid_prod_kwargs():
    return {
        "ENVIRONMENT": "production",
        "DATABASE_URL": "postgresql+asyncpg://prod_user:secret_pg_pass@prod-db.internal:5432/comlina_prod",
        "REDIS_URL": "rediss://:prod_redis_pass@prod-redis.internal:6379/0",
        "SUPABASE_URL": "https://xyzcompany.supabase.co",
        "SUPABASE_JWT_SECRET": "a_very_long_production_jwt_secret_with_sufficient_entropy_64chars",
        "BACKEND_JWT_SECRET": "",
        "SUPABASE_JWKS_URL": "",
        "TOKEN_ENCRYPTION_KEY": VALID_FERNET_KEY,
        "TOKEN_ENCRYPTION_KEYS": "",
        "META_APP_ID": "123456789098765",
        "META_APP_SECRET": "meta_app_secret_real_prod_entropy_32chars",
        "META_WEBHOOK_VERIFY_TOKEN": "meta_webhook_token_secure_and_long_32chars",
        "ALLOWED_ORIGINS": "https://app.comlina.ai,https://comlina.ai",
    }

def test_valid_production_config_passes():
    kwargs = get_base_valid_prod_kwargs()
    s = Settings(**kwargs)
    assert s.ENVIRONMENT == "production"
    assert s.get_encryption_keys() == [VALID_FERNET_KEY]
    assert s.get_allowed_origins() == ["https://app.comlina.ai", "https://comlina.ai"]

def test_dev_environment_allows_defaults():
    s = Settings(ENVIRONMENT="development", TOKEN_ENCRYPTION_KEY="", TOKEN_ENCRYPTION_KEYS="")
    assert s.ENVIRONMENT == "development"
    assert s.get_primary_encryption_key() == DEV_DETERMINISTIC_FERNET_KEY

def test_prod_fails_on_missing_or_sqlite_db():
    kwargs = get_base_valid_prod_kwargs()
    kwargs["DATABASE_URL"] = ""
    with pytest.raises(ValueError, match="DATABASE_URL"):
        Settings(**kwargs)

    kwargs["DATABASE_URL"] = "sqlite+aiosqlite:///tmp/test.db"
    with pytest.raises(ValueError, match="SQLite database fallback is strictly forbidden in production"):
        Settings(**kwargs)

    kwargs["DATABASE_URL"] = "postgresql+asyncpg://postgres:your_password@localhost:5432/comlina"
    with pytest.raises(ValueError, match="placeholder"):
        Settings(**kwargs)

def test_prod_fails_on_missing_or_invalid_redis():
    kwargs = get_base_valid_prod_kwargs()
    kwargs["REDIS_URL"] = ""
    with pytest.raises(ValueError, match="REDIS_URL"):
        Settings(**kwargs)

    kwargs["REDIS_URL"] = "http://localhost:6379"
    with pytest.raises(ValueError, match="redis:// or rediss://"):
        Settings(**kwargs)

    kwargs["REDIS_URL"] = "redis://:your_redis_password@localhost:6379"
    with pytest.raises(ValueError, match="placeholder"):
        Settings(**kwargs)

def test_prod_fails_on_missing_or_insecure_supabase_url():
    kwargs = get_base_valid_prod_kwargs()
    kwargs["SUPABASE_URL"] = ""
    with pytest.raises(ValueError, match="SUPABASE_URL"):
        Settings(**kwargs)

    kwargs["SUPABASE_URL"] = "http://api.supabase.co"
    with pytest.raises(ValueError, match="HTTPS"):
        Settings(**kwargs)

    kwargs["SUPABASE_URL"] = "https://your-project-ref.supabase.co"
    with pytest.raises(ValueError, match="real project URL"):
        Settings(**kwargs)

def test_prod_fails_on_weak_or_dev_jwt_secret():
    kwargs = get_base_valid_prod_kwargs()
    kwargs["SUPABASE_JWT_SECRET"] = DEV_DETERMINISTIC_JWT_SECRET
    kwargs["BACKEND_JWT_SECRET"] = ""
    kwargs["SUPABASE_JWKS_URL"] = ""
    with pytest.raises(ValueError, match="JWT verification key material"):
        Settings(**kwargs)

    kwargs["SUPABASE_JWT_SECRET"] = "short_secret"
    with pytest.raises(ValueError, match="JWT verification key material"):
        Settings(**kwargs)

def test_prod_accepts_valid_jwks_without_secret():
    kwargs = get_base_valid_prod_kwargs()
    kwargs["SUPABASE_JWT_SECRET"] = ""
    kwargs["BACKEND_JWT_SECRET"] = ""
    kwargs["SUPABASE_JWKS_URL"] = "https://my-project.supabase.co/auth/v1/.well-known/jwks.json"
    s = Settings(**kwargs)
    assert s.SUPABASE_JWKS_URL.startswith("https://")

def test_prod_fails_on_missing_or_weak_encryption_key():
    kwargs = get_base_valid_prod_kwargs()
    kwargs["TOKEN_ENCRYPTION_KEY"] = ""
    kwargs["TOKEN_ENCRYPTION_KEYS"] = ""
    with pytest.raises(ValueError, match="TOKEN_ENCRYPTION_KEY"):
        Settings(**kwargs)

    kwargs["TOKEN_ENCRYPTION_KEY"] = DEV_DETERMINISTIC_FERNET_KEY
    with pytest.raises(ValueError, match="auto-generated or default dev key"):
        Settings(**kwargs)

    kwargs["TOKEN_ENCRYPTION_KEY"] = "not_a_valid_32_byte_key"
    with pytest.raises(ValueError, match="valid 32-byte urlsafe base64"):
        Settings(**kwargs)

def test_prod_accepts_multi_fernet_keys():
    kwargs = get_base_valid_prod_kwargs()
    kwargs["TOKEN_ENCRYPTION_KEY"] = ""
    kwargs["TOKEN_ENCRYPTION_KEYS"] = f"{VALID_FERNET_KEY},{VALID_FERNET_KEY_2}"
    s = Settings(**kwargs)
    assert s.get_encryption_keys() == [VALID_FERNET_KEY, VALID_FERNET_KEY_2]
    assert s.get_primary_encryption_key() == VALID_FERNET_KEY

def test_prod_fails_on_meta_credentials():
    kwargs = get_base_valid_prod_kwargs()
    kwargs["META_APP_ID"] = ""
    with pytest.raises(ValueError, match="META_APP_ID"):
        Settings(**kwargs)

    kwargs = get_base_valid_prod_kwargs()
    kwargs["META_APP_SECRET"] = "too_short"
    with pytest.raises(ValueError, match="META_APP_SECRET"):
        Settings(**kwargs)

    kwargs = get_base_valid_prod_kwargs()
    kwargs["META_WEBHOOK_VERIFY_TOKEN"] = "your_token_here"
    with pytest.raises(ValueError, match="META_WEBHOOK_VERIFY_TOKEN"):
        Settings(**kwargs)

def test_prod_fails_on_insecure_cors_origins():
    kwargs = get_base_valid_prod_kwargs()
    kwargs["ALLOWED_ORIGINS"] = "*"
    with pytest.raises(ValueError, match="Wildcard"):
        Settings(**kwargs)

    kwargs["ALLOWED_ORIGINS"] = "http://insecure.comlina.ai"
    with pytest.raises(ValueError, match="Insecure HTTP origin"):
        Settings(**kwargs)

    kwargs["ALLOWED_ORIGINS"] = ""
    kwargs["CORS_ORIGINS"] = []
    with pytest.raises(ValueError, match="ALLOWED_ORIGINS"):
        Settings(**kwargs)

def test_worker_settings_validation():
    # Dev mode passes
    w_dev = WorkerSettings(ENVIRONMENT="development", TOKEN_ENCRYPTION_KEY="", TOKEN_ENCRYPTION_KEYS="")
    assert w_dev.ENVIRONMENT == "development"
    assert w_dev.get_primary_encryption_key() == DEV_DETERMINISTIC_FERNET_KEY

    # Valid prod passes
    w_prod = WorkerSettings(
        ENVIRONMENT="production",
        DATABASE_URL="postgresql+asyncpg://worker:pass@prod-db.internal:5432/comlina",
        REDIS_URL="rediss://:pass@prod-redis.internal:6379/0",
        TOKEN_ENCRYPTION_KEY=VALID_FERNET_KEY,
        TOKEN_ENCRYPTION_KEYS="",
    )
    assert w_prod.ENVIRONMENT == "production"

    # Prod fails on sqlite
    with pytest.raises(ValueError, match="SQLite database fallback is strictly forbidden"):
        WorkerSettings(
            ENVIRONMENT="production",
            DATABASE_URL="sqlite+aiosqlite:///tmp/db.sqlite",
            REDIS_URL="redis://localhost:6379/0",
            TOKEN_ENCRYPTION_KEY=VALID_FERNET_KEY,
        )

    # Prod fails on dev key
    with pytest.raises(ValueError, match="dev key"):
        WorkerSettings(
            ENVIRONMENT="production",
            DATABASE_URL="postgresql+asyncpg://worker:pass@prod-db.internal:5432/comlina",
            REDIS_URL="redis://localhost:6379/0",
            TOKEN_ENCRYPTION_KEY=DEV_DETERMINISTIC_FERNET_KEY,
            TOKEN_ENCRYPTION_KEYS="",
        )

def test_resolve_database_url_rejects_sqlite_in_production():
    with pytest.raises(ValueError, match="strictly prohibited in production"):
        server_resolve_db("sqlite+aiosqlite:///local.db", "production")

    with pytest.raises(ValueError, match="strictly prohibited in production"):
        worker_resolve_db("sqlite+aiosqlite:///local.db", "production")
