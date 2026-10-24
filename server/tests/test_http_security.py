# server/tests/test_http_security.py
import pytest
from unittest.mock import patch
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.core.config import settings


@pytest.mark.asyncio
async def test_security_headers_present_on_responses():
    """Verify that OWASP recommended security headers are present on API responses."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.get("/health")
        assert res.status_code == 200

        # Nosniff
        assert res.headers.get("X-Content-Type-Options") == "nosniff"

        # Frame protection
        assert res.headers.get("X-Frame-Options") == "DENY"
        assert "frame-ancestors 'none'" in res.headers.get("Content-Security-Policy", "")

        # Strict Referrer
        assert res.headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"

        # Permissions Policy
        assert "camera=()" in res.headers.get("Permissions-Policy", "")
        assert "microphone=()" in res.headers.get("Permissions-Policy", "")

        # Request correlation ID
        assert "x-request-id" in res.headers
        assert len(res.headers["x-request-id"]) > 0


@pytest.mark.asyncio
async def test_hsts_header_present_in_production_only():
    """Verify HSTS header is only applied in production environment."""
    # Development: HSTS should not be set
    with patch.object(settings, "ENVIRONMENT", "development"):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            dev_res = await ac.get("/health")
            assert "Strict-Transport-Security" not in dev_res.headers

    # Production: HSTS must be set with 2-year duration and preload
    with patch.object(settings, "ENVIRONMENT", "production"):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            prod_res = await ac.get("/health")
            assert "Strict-Transport-Security" in prod_res.headers
            hsts = prod_res.headers["Strict-Transport-Security"]
            assert "max-age=63072000" in hsts
            assert "includeSubDomains" in hsts
            assert "preload" in hsts


@pytest.mark.asyncio
async def test_cors_policy_rejects_untrusted_origins_and_disables_credentials():
    """Verify CORS rejects untrusted origins, forbids wildcards, and disables credentials for Bearer auth."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Preflight from authorized origin
        auth_res = await ac.options(
            "/api/workspaces",
            headers={
                "Origin": "https://app.comlina.ai",
                "Access-Control-Request-Method": "GET",
                "Access-Control-Request-Headers": "Authorization"
            }
        )
        assert auth_res.headers.get("access-control-allow-origin") == "https://app.comlina.ai"
        # Credentials off for Bearer auth
        assert auth_res.headers.get("access-control-allow-credentials") is None or auth_res.headers.get("access-control-allow-credentials") == "false"

        # Preflight from malicious/unauthorized origin
        unauth_res = await ac.options(
            "/api/workspaces",
            headers={
                "Origin": "https://evil-phishing-site.com",
                "Access-Control-Request-Method": "GET",
                "Access-Control-Request-Headers": "Authorization"
            }
        )
        assert unauth_res.headers.get("access-control-allow-origin") is None


@pytest.mark.asyncio
async def test_generic_500_error_handler_masks_tracebacks():
    """Unhandled internal errors must return generic JSON without leaking stack traces or internal state."""
    # We trigger an unhandled error on a mock endpoint
    @app.get("/api/test-error-handling")
    async def trigger_error():
        raise RuntimeError("Internal database password secret leak failure")

    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            res = await ac.get("/api/test-error-handling")
            assert res.status_code == 500
            data = res.json()

            # Verify generic response
            assert data["error"] == "Internal Server Error"
            assert data["message"] == "An unexpected error occurred. Please try again later."
            assert "request_id" in data

            # Verify no secret or internal message leaked in response body
            body_text = res.text
            assert "RuntimeError" not in body_text
            assert "secret" not in body_text
            assert "Traceback" not in body_text
    finally:
        # Remove temporary route
        app.router.routes = [r for r in app.router.routes if getattr(r, "path", "") != "/api/test-error-handling"]
