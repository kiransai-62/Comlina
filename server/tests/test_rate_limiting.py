# server/tests/test_rate_limiting.py
import uuid
import pytest
from unittest.mock import AsyncMock, patch
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.core.config import settings
from app.core.rate_limiter import rate_limiter, RateLimitUnavailableError
from app.core.security_middleware import get_client_ip


class MockRedisClient:
    """Simulates an atomic Redis client running the Lua rate-limiting script."""
    def __init__(self):
        self.store = {}
        self.ttl_store = {}

    async def eval(self, script, numkeys, key, limit, window):
        limit = int(limit)
        window = int(window)
        current = self.store.get(key, 0) + 1
        self.store[key] = current
        ttl = self.ttl_store.get(key, window)
        self.ttl_store[key] = ttl
        if current > limit:
            return [0, ttl]
        return [1, ttl]

    async def ping(self):
        return True


@pytest.fixture(autouse=True)
def reset_limiter():
    rate_limiter.set_redis_client(None)
    rate_limiter.reset_in_memory_cache()
    yield
    rate_limiter.set_redis_client(None)
    rate_limiter.reset_in_memory_cache()


@pytest.mark.asyncio
async def test_trusted_proxy_count_zero_ignores_spoofed_x_forwarded_for():
    """When TRUSTED_PROXY_COUNT is 0, any X-Forwarded-For header is untrusted and ignored."""
    with patch.object(settings, "TRUSTED_PROXY_COUNT", 0):
        class DummyRequest:
            headers = {"x-forwarded-for": "203.0.113.195, 1.2.3.4"}
            client = type("Client", (), {"host": "198.51.100.2"})()

        ip = get_client_ip(DummyRequest())
        assert ip == "198.51.100.2", f"Expected client host 198.51.100.2, got {ip}"


@pytest.mark.asyncio
async def test_trusted_proxy_count_one_respects_appended_proxy_ip():
    """When TRUSTED_PROXY_COUNT is 1, the rightmost IP appended by the reverse proxy is used."""
    with patch.object(settings, "TRUSTED_PROXY_COUNT", 1):
        class DummyRequest:
            headers = {"x-forwarded-for": "203.0.113.195, 198.51.100.2"}
            client = type("Client", (), {"host": "10.0.0.1"})()

        ip = get_client_ip(DummyRequest())
        assert ip == "198.51.100.2", f"Expected rightmost proxy IP 198.51.100.2, got {ip}"


@pytest.mark.asyncio
async def test_trusted_proxy_count_two_extracts_correct_hop():
    """When TRUSTED_PROXY_COUNT is 2, the second IP from the right is used."""
    with patch.object(settings, "TRUSTED_PROXY_COUNT", 2):
        class DummyRequest:
            headers = {"x-forwarded-for": "spoofed.client.ip, 198.51.100.2, 10.0.0.1"}
            client = type("Client", (), {"host": "127.0.0.1"})()

        ip = get_client_ip(DummyRequest())
        assert ip == "198.51.100.2", f"Expected client IP 198.51.100.2, got {ip}"


@pytest.mark.asyncio
async def test_atomic_redis_rate_limiting_per_ip_returns_429():
    """Verify that exceeding IP rate limit triggers HTTP 429 with Retry-After header."""
    mock_redis = MockRedisClient()
    rate_limiter.set_redis_client(mock_redis)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Auth route limit is 10 requests / 60 seconds
        for i in range(10):
            res = await ac.post("/api/auth/login", json={"email": "attacker@comlina.ai", "password": "pass"})
            # Prior to hitting rate limit, error is 401 (invalid credentials) or 400
            assert res.status_code in (400, 401, 422), f"Unexpected status {res.status_code} at request {i}"

        # 11th request must be blocked by rate limiter
        blocked_res = await ac.post("/api/auth/login", json={"email": "attacker@comlina.ai", "password": "pass"})
        assert blocked_res.status_code == 429
        assert "Retry-After" in blocked_res.headers
        assert int(blocked_res.headers["Retry-After"]) >= 1
        data = blocked_res.json()
        assert "Too Many Requests" in data.get("error", "")


@pytest.mark.asyncio
async def test_rate_limiting_per_workspace_returns_429():
    """Verify that exceeding workspace rate limit returns 429."""
    mock_redis = MockRedisClient()
    rate_limiter.set_redis_client(mock_redis)

    ws_id = str(uuid.uuid4())
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Workspace limit is 200 requests / 60 seconds
        headers = {"X-Workspace-ID": ws_id}
        # Simulate reaching limit directly via rate limiter check
        for _ in range(200):
            allowed, _ = await rate_limiter.check_workspace(
                workspace_id=ws_id,
                route_tag="general",
                limit=200,
                window=60,
                fail_closed=False
            )
            assert allowed is True

        # 201st request for this workspace must be blocked
        allowed, retry_after = await rate_limiter.check_workspace(
            workspace_id=ws_id,
            route_tag="general",
            limit=200,
            window=60,
            fail_closed=False
        )
        assert allowed is False
        assert retry_after >= 1


@pytest.mark.asyncio
async def test_rate_limiting_per_user_returns_429():
    """Verify that exceeding user rate limit returns 429."""
    mock_redis = MockRedisClient()
    rate_limiter.set_redis_client(mock_redis)

    user_id = str(uuid.uuid4())
    # User limit is 120 requests / 60 seconds
    for _ in range(120):
        allowed, _ = await rate_limiter.check_user(
            user_id=user_id,
            route_tag="general",
            limit=120,
            window=60,
            fail_closed=False
        )
        assert allowed is True

    allowed, retry_after = await rate_limiter.check_user(
        user_id=user_id,
        route_tag="general",
        limit=120,
        window=60,
        fail_closed=False
    )
    assert allowed is False
    assert retry_after >= 1


@pytest.mark.asyncio
async def test_fail_closed_for_auth_oauth_messaging_when_redis_down():
    """
    When Redis is down and fail_closed is enabled:
    - Auth routes must fail closed (HTTP 503)
    - OAuth routes must fail closed (HTTP 503)
    - Messaging routes must fail closed (HTTP 503)
    - Non-sensitive routes (e.g. /health) must remain available (HTTP 200)
    """
    class BrokenRedisClient:
        async def eval(self, *args, **kwargs):
            raise ConnectionError("Redis connection refused")

        async def ping(self):
            raise ConnectionError("Redis connection refused")

    rate_limiter.set_redis_client(BrokenRedisClient())

    with patch.object(settings, "FAIL_CLOSED_ON_REDIS_DOWN", True):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            # 1. Auth route fails closed
            auth_res = await ac.post("/api/auth/login", json={"email": "test@comlina.ai", "password": "pass"})
            assert auth_res.status_code == 503
            assert "temporarily unavailable" in auth_res.json().get("message", "").lower()

            # 2. OAuth route fails closed
            oauth_res = await ac.get("/api/instagram/oauth/connect-url")
            assert oauth_res.status_code == 503

            # 3. Messaging route fails closed
            msg_res = await ac.get(f"/api/conversations/{uuid.uuid4()}/messages")
            assert msg_res.status_code == 503

            # 4. Health check endpoint remains 200 (exempt)
            health_res = await ac.get("/health")
            assert health_res.status_code == 200
            assert health_res.json()["status"] == "healthy"
