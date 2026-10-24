# server/tests/test_instagram_webhook_subscriptions.py
import uuid
import pytest
import httpx
from unittest.mock import MagicMock
from httpx import AsyncClient, ASGITransport
from sqlalchemy import select

from app.main import app
from app.core.database import get_db_session
from app.models import User, Workspace, WorkspaceMember, InstagramAccount
from app.api.auth import create_backend_jwt
from app.core.encryption import encrypt_token


@pytest.fixture
async def setup_subscription_tenants():
    """
    Sets up two isolated workspaces with connected Instagram accounts for testing webhook subscriptions.
    """
    async with get_db_session() as session:
        # Tenant A
        user_a = User(
            id=uuid.uuid4(),
            email=f"sub_owner_a_{uuid.uuid4().hex[:8]}@comlina.ai",
            full_name="Subscriber A",
            timezone="UTC"
        )
        ws_a = Workspace(
            id=uuid.uuid4(),
            name="Workspace Sub A",
            slug=f"wsa-sub-{uuid.uuid4().hex[:8]}",
            plan_tier="PREMIUM",
            max_automations=10
        )
        session.add_all([user_a, ws_a])
        await session.flush()

        member_a = WorkspaceMember(
            id=uuid.uuid4(),
            workspace_id=ws_a.id,
            user_id=user_a.id,
            role="OWNER"
        )
        ig_a = InstagramAccount(
            id=uuid.uuid4(),
            workspace_id=ws_a.id,
            user_id=user_a.id,
            ig_user_id=f"iga_{uuid.uuid4().hex[:8]}",
            username="brand_a_webhooks",
            account_type="BUSINESS",
            follower_count=5000,
            access_token_encrypted=encrypt_token("valid_token_tenant_a"),
            is_active=True,
            connection_status="CONNECTED",
            webhook_subscription_status="UNKNOWN"
        )
        session.add_all([member_a, ig_a])

        # Tenant B
        user_b = User(
            id=uuid.uuid4(),
            email=f"sub_owner_b_{uuid.uuid4().hex[:8]}@comlina.ai",
            full_name="Subscriber B",
            timezone="UTC"
        )
        ws_b = Workspace(
            id=uuid.uuid4(),
            name="Workspace Sub B",
            slug=f"wsb-sub-{uuid.uuid4().hex[:8]}",
            plan_tier="PREMIUM",
            max_automations=10
        )
        session.add_all([user_b, ws_b])
        await session.flush()

        member_b = WorkspaceMember(
            id=uuid.uuid4(),
            workspace_id=ws_b.id,
            user_id=user_b.id,
            role="OWNER"
        )
        ig_b = InstagramAccount(
            id=uuid.uuid4(),
            workspace_id=ws_b.id,
            user_id=user_b.id,
            ig_user_id=f"igb_{uuid.uuid4().hex[:8]}",
            username="brand_b_webhooks",
            account_type="BUSINESS",
            follower_count=2000,
            access_token_encrypted=encrypt_token("valid_token_tenant_b"),
            is_active=True,
            connection_status="CONNECTED",
            webhook_subscription_status="UNKNOWN"
        )
        session.add_all([member_b, ig_b])

        await session.commit()

        token_a = create_backend_jwt(str(user_a.id), user_a.email, token_type="access")
        token_b = create_backend_jwt(str(user_b.id), user_b.email, token_type="access")

        return {
            "user_a": user_a,
            "ws_a": ws_a,
            "ig_a": ig_a,
            "token_a": token_a,
            "user_b": user_b,
            "ws_b": ws_b,
            "ig_b": ig_b,
            "token_b": token_b,
        }


@pytest.mark.asyncio
async def test_inspect_webhook_subscription_success(setup_subscription_tenants, monkeypatch):
    """
    GET /accounts/{id}/webhook-subscription returns SUBSCRIBED when Meta confirms active fields.
    """
    fixture = setup_subscription_tenants
    ig_id = str(fixture["ig_a"].id)
    token = fixture["token_a"]

    orig_get = httpx.AsyncClient.get

    async def mock_get(self, url, **kwargs):
        if "graph.instagram.com" in str(url):
            assert "subscribed_apps" in str(url)
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.json.return_value = {
                "data": [
                    {
                        "id": "1234567890",
                        "name": "Comlina Automation App",
                        "subscribed_fields": ["comments", "messages"]
                    }
                ]
            }
            return mock_resp
        return await orig_get(self, url, **kwargs)

    monkeypatch.setattr(httpx.AsyncClient, "get", mock_get)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get(
            f"/api/instagram/accounts/{ig_id}/webhook-subscription",
            headers={"Authorization": f"Bearer {token}"}
        )

    assert resp.status_code == 200
    data = resp.json()
    assert data["is_subscribed"] is True
    assert data["status"] == "SUBSCRIBED"
    assert "comments" in data["subscribed_fields"]
    assert "messages" in data["subscribed_fields"]
    assert data["requires_reconnect"] is False
    assert "valid_token" not in str(data)  # Never expose tokens


@pytest.mark.asyncio
async def test_inspect_webhook_subscription_not_subscribed(setup_subscription_tenants, monkeypatch):
    """
    GET /accounts/{id}/webhook-subscription returns NOT_SUBSCRIBED when Meta returns empty data list.
    """
    fixture = setup_subscription_tenants
    ig_id = str(fixture["ig_a"].id)
    token = fixture["token_a"]

    orig_get = httpx.AsyncClient.get

    async def mock_get(self, url, **kwargs):
        if "graph.instagram.com" in str(url):
            assert "subscribed_apps" in str(url)
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.json.return_value = {"data": []}
            return mock_resp
        return await orig_get(self, url, **kwargs)

    monkeypatch.setattr(httpx.AsyncClient, "get", mock_get)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get(
            f"/api/instagram/accounts/{ig_id}/webhook-subscription",
            headers={"Authorization": f"Bearer {token}"}
        )

    assert resp.status_code == 200
    data = resp.json()
    assert data["is_subscribed"] is False
    assert data["status"] == "NOT_SUBSCRIBED"
    assert data["can_retry"] is True
    assert data["requires_reconnect"] is False


@pytest.mark.asyncio
async def test_retry_webhook_subscription_success(setup_subscription_tenants, monkeypatch):
    """
    POST /accounts/{id}/webhook-subscription succeeds and updates database subscription status.
    """
    fixture = setup_subscription_tenants
    ig_id = str(fixture["ig_a"].id)
    token = fixture["token_a"]

    orig_post = httpx.AsyncClient.post

    async def mock_post(self, url, **kwargs):
        if "graph.instagram.com" in str(url):
            assert "subscribed_apps" in str(url)
            params = kwargs.get("params", {})
            assert params.get("subscribed_fields") == "comments,messages"
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.json.return_value = {"success": True}
            return mock_resp
        return await orig_post(self, url, **kwargs)

    monkeypatch.setattr(httpx.AsyncClient, "post", mock_post)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            f"/api/instagram/accounts/{ig_id}/webhook-subscription",
            headers={"Authorization": f"Bearer {token}"}
        )

    assert resp.status_code == 200
    data = resp.json()
    assert data["is_subscribed"] is True
    assert data["status"] == "SUBSCRIBED"
    assert data["requires_reconnect"] is False

    # Verify DB update
    async with get_db_session() as session:
        stmt = select(InstagramAccount).where(InstagramAccount.id == fixture["ig_a"].id)
        account = (await session.execute(stmt)).scalar_one()
        assert account.webhook_subscription_status == "SUBSCRIBED"
        assert account.webhook_subscribed_at is not None


@pytest.mark.asyncio
async def test_retry_webhook_subscription_already_subscribed(setup_subscription_tenants, monkeypatch):
    """
    POST /accounts/{id}/webhook-subscription is idempotent when account is already subscribed.
    """
    fixture = setup_subscription_tenants
    ig_id = str(fixture["ig_a"].id)
    token = fixture["token_a"]

    orig_post = httpx.AsyncClient.post

    async def mock_post(self, url, **kwargs):
        if "graph.instagram.com" in str(url):
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.json.return_value = {"success": True}
            return mock_resp
        return await orig_post(self, url, **kwargs)

    monkeypatch.setattr(httpx.AsyncClient, "post", mock_post)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp1 = await client.post(
            f"/api/instagram/accounts/{ig_id}/webhook-subscription",
            headers={"Authorization": f"Bearer {token}"}
        )
        resp2 = await client.post(
            f"/api/instagram/accounts/{ig_id}/webhook-subscription",
            headers={"Authorization": f"Bearer {token}"}
        )

    assert resp1.status_code == 200
    assert resp2.status_code == 200
    assert resp2.json()["status"] == "SUBSCRIBED"


@pytest.mark.asyncio
async def test_subscription_permission_denied(setup_subscription_tenants, monkeypatch):
    """
    Meta permission denial (code 10/200) triggers PERMISSION_DENIED and marks account as REAUTHORIZATION_REQUIRED.
    """
    fixture = setup_subscription_tenants
    ig_id = str(fixture["ig_a"].id)
    token = fixture["token_a"]

    orig_post = httpx.AsyncClient.post

    async def mock_post(self, url, **kwargs):
        if "graph.instagram.com" in str(url):
            mock_resp = MagicMock()
            mock_resp.status_code = 400
            mock_resp.json.return_value = {
                "error": {
                    "message": "(#10) Application does not have permission for this action",
                    "type": "OAuthException",
                    "code": 10
                }
            }
            return mock_resp
        return await orig_post(self, url, **kwargs)

    monkeypatch.setattr(httpx.AsyncClient, "post", mock_post)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            f"/api/instagram/accounts/{ig_id}/webhook-subscription",
            headers={"Authorization": f"Bearer {token}"}
        )

    assert resp.status_code == 200
    data = resp.json()
    assert data["is_subscribed"] is False
    assert data["status"] == "PERMISSION_DENIED"
    assert data["requires_reconnect"] is True
    assert data["can_retry"] is False

    # Check DB state was updated
    async with get_db_session() as session:
        stmt = select(InstagramAccount).where(InstagramAccount.id == fixture["ig_a"].id)
        account = (await session.execute(stmt)).scalar_one()
        assert account.connection_status == "REAUTHORIZATION_REQUIRED"
        assert account.last_error_code == "PERMISSION_DENIED"


@pytest.mark.asyncio
async def test_subscription_expired_token(setup_subscription_tenants, monkeypatch):
    """
    Expired access token (code 190) returns TOKEN_EXPIRED and triggers REAUTHORIZATION_REQUIRED.
    """
    fixture = setup_subscription_tenants
    ig_id = str(fixture["ig_a"].id)
    token = fixture["token_a"]

    orig_get = httpx.AsyncClient.get

    async def mock_get(self, url, **kwargs):
        if "graph.instagram.com" in str(url):
            mock_resp = MagicMock()
            mock_resp.status_code = 400
            mock_resp.json.return_value = {
                "error": {
                    "message": "Error validating access token: Session has expired on Monday, 10-Jul-23 10:23:45 PDT.",
                    "type": "OAuthException",
                    "code": 190,
                    "error_subcode": 463
                }
            }
            return mock_resp
        return await orig_get(self, url, **kwargs)

    monkeypatch.setattr(httpx.AsyncClient, "get", mock_get)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get(
            f"/api/instagram/accounts/{ig_id}/webhook-subscription",
            headers={"Authorization": f"Bearer {token}"}
        )

    assert resp.status_code == 200
    data = resp.json()
    assert data["is_subscribed"] is False
    assert data["status"] == "TOKEN_EXPIRED"
    assert data["requires_reconnect"] is True
    assert data["can_retry"] is False

    # Check DB state
    async with get_db_session() as session:
        stmt = select(InstagramAccount).where(InstagramAccount.id == fixture["ig_a"].id)
        account = (await session.execute(stmt)).scalar_one()
        assert account.connection_status == "REAUTHORIZATION_REQUIRED"
        assert account.last_error_code == "TOKEN_EXPIRED"


@pytest.mark.asyncio
async def test_subscription_rate_limit(setup_subscription_tenants, monkeypatch):
    """
    Meta rate limit (code 4/17/32) returns RATE_LIMITED and allows retry without forcing full reconnect.
    """
    fixture = setup_subscription_tenants
    ig_id = str(fixture["ig_a"].id)
    token = fixture["token_a"]

    orig_post = httpx.AsyncClient.post

    async def mock_post(self, url, **kwargs):
        if "graph.instagram.com" in str(url):
            mock_resp = MagicMock()
            mock_resp.status_code = 400
            mock_resp.json.return_value = {
                "error": {
                    "message": "(#17) User request limit reached",
                    "type": "OAuthException",
                    "code": 17
                }
            }
            return mock_resp
        return await orig_post(self, url, **kwargs)

    monkeypatch.setattr(httpx.AsyncClient, "post", mock_post)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            f"/api/instagram/accounts/{ig_id}/webhook-subscription",
            headers={"Authorization": f"Bearer {token}"}
        )

    assert resp.status_code == 200
    data = resp.json()
    assert data["is_subscribed"] is False
    assert data["status"] == "RATE_LIMITED"
    assert data["requires_reconnect"] is False
    assert data["can_retry"] is True


@pytest.mark.asyncio
async def test_subscription_meta_api_outage(setup_subscription_tenants, monkeypatch):
    """
    Meta API 500 error or connection failure returns META_ERROR with retry allowed.
    """
    fixture = setup_subscription_tenants
    ig_id = str(fixture["ig_a"].id)
    token = fixture["token_a"]

    orig_get = httpx.AsyncClient.get

    async def mock_get(self, url, **kwargs):
        if "graph.instagram.com" in str(url):
            mock_resp = MagicMock()
            mock_resp.status_code = 503
            mock_resp.text = "Service Unavailable"
            mock_resp.json.side_effect = ValueError("Non-JSON 503")
            return mock_resp
        return await orig_get(self, url, **kwargs)

    monkeypatch.setattr(httpx.AsyncClient, "get", mock_get)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get(
            f"/api/instagram/accounts/{ig_id}/webhook-subscription",
            headers={"Authorization": f"Bearer {token}"}
        )

    assert resp.status_code == 200
    data = resp.json()
    assert data["is_subscribed"] is False
    assert data["status"] == "META_ERROR"
    assert data["can_retry"] is True
    assert data["requires_reconnect"] is False


@pytest.mark.asyncio
async def test_tenant_isolation_unauthorized_account_access(setup_subscription_tenants):
    """
    Tenant B cannot inspect or retry webhook subscriptions for Tenant A's Instagram account.
    """
    fixture = setup_subscription_tenants
    ig_a_id = str(fixture["ig_a"].id)
    token_b = fixture["token_b"]

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # GET attempt
        resp_get = await client.get(
            f"/api/instagram/accounts/{ig_a_id}/webhook-subscription",
            headers={"Authorization": f"Bearer {token_b}"}
        )
        assert resp_get.status_code == 404

        # POST attempt
        resp_post = await client.post(
            f"/api/instagram/accounts/{ig_a_id}/webhook-subscription",
            headers={"Authorization": f"Bearer {token_b}"}
        )
        assert resp_post.status_code == 404


@pytest.mark.asyncio
async def test_unauthenticated_request_rejected(setup_subscription_tenants):
    """
    Unauthenticated requests are strictly rejected with 401.
    """
    fixture = setup_subscription_tenants
    ig_id = str(fixture["ig_a"].id)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get(f"/api/instagram/accounts/{ig_id}/webhook-subscription")
        assert resp.status_code == 401
