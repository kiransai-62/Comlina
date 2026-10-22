import base64
import pytest
from starlette.testclient import TestClient
from fastapi import FastAPI
from app.core.config import Settings
from app.api.instagram import router as instagram_router
from app.api.payments import router as payments_router
from app.api.webhooks import router as webhooks_router
from app.main import app

def test_production_routes_disabled(monkeypatch):
    """
    In production mode:
    - /docs, /redoc, /openapi.json must return 404.
    - /api/instagram/connect-dev-account must return 404.
    - /api/payments/dev/switch-plan must return 404.
    - /webhooks/instagram/simulate-comment must return 404.
    """
    # Create production app instance
    prod_settings = Settings(
        ENVIRONMENT="production",
        ENABLE_DEV_ROUTES=False,
        DATABASE_URL="postgresql+asyncpg://prod_user:secret_pg_pass@prod-db.internal:5432/comlina_prod",
        REDIS_URL="rediss://:prod_redis_pass@prod-redis.internal:6379/0",
        SUPABASE_URL="https://xyzcompany.supabase.co",
        SUPABASE_JWT_SECRET="a_very_long_production_jwt_secret_with_sufficient_entropy_64chars",
        TOKEN_ENCRYPTION_KEY=base64.urlsafe_b64encode(b"01234567890123456789012345678901").decode("utf-8"),
        META_APP_ID="123456789098765",
        META_APP_SECRET="meta_app_secret_real_prod_entropy_32chars",
        META_WEBHOOK_VERIFY_TOKEN="meta_webhook_token_secure_and_long_32chars",
        ALLOWED_ORIGINS="https://app.comlina.ai,https://comlina.ai",
        RAZORPAY_KEY_ID="rzp_live_1234567890abcdef",
        RAZORPAY_KEY_SECRET="razorpay_secret_real_prod_entropy_32chars",
        RAZORPAY_WEBHOOK_SECRET="razorpay_webhook_real_prod_entropy_32chars",
    )

    prod_app = FastAPI(
        title=prod_settings.PROJECT_NAME,
        version=prod_settings.VERSION,
        docs_url="/docs" if prod_settings.ENVIRONMENT == "development" else None,
        redoc_url="/redoc" if prod_settings.ENVIRONMENT == "development" else None,
        openapi_url="/openapi.json" if prod_settings.ENVIRONMENT == "development" else None,
    )
    prod_app.include_router(instagram_router, prefix="/api")
    prod_app.include_router(payments_router, prefix="/api")
    prod_app.include_router(webhooks_router)
    prod_app.include_router(webhooks_router, prefix="/api")

    client = TestClient(prod_app)

    # Docs disabled
    assert client.get("/docs").status_code == 404
    assert client.get("/redoc").status_code == 404
    assert client.get("/openapi.json").status_code == 404

    # Dev routes disabled (not registered)
    assert client.post("/api/instagram/connect-dev-account").status_code == 404
    assert client.post("/api/payments/dev/switch-plan").status_code == 404

    # Simulation route disabled in production
    assert client.post("/webhooks/instagram/simulate-comment", json={"text": "test"}).status_code == 404
    assert client.post("/api/webhooks/instagram/simulate-comment", json={"text": "test"}).status_code == 404

def test_dev_routes_not_registered_when_flag_false():
    """When ENABLE_DEV_ROUTES is False (default), dev account routes and simulation must return 404."""
    client = TestClient(app)
    # If default server started with ENABLE_DEV_ROUTES=False:
    # connect-dev-account should return 404
    res = client.post("/api/instagram/connect-dev-account")
    assert res.status_code == 404

    res2 = client.post("/api/payments/dev/switch-plan")
    assert res2.status_code == 404

    res3 = client.post("/webhooks/instagram/simulate-comment", json={"text": "test"})
    assert res3.status_code == 404
