import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, patch, MagicMock

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.core.database import get_db
from app.core.encryption import encrypt_token, decrypt_token
from app.models import User, Workspace, InstagramAccount, WorkspaceMember
from app.api.deps import get_current_user, get_current_workspace, require_workspace_owner

@pytest.fixture
def mock_user_and_workspace():
    user_id = uuid.uuid4()
    ws_id = uuid.uuid4()
    user = User(
        id=user_id,
        email="creator@comlina.ai",
        full_name="Creator User"
    )
    workspace = Workspace(
        id=ws_id,
        name="Creator Workspace",
        slug="creator-workspace",
        max_accounts=2
    )
    return user, workspace

@pytest.mark.asyncio
async def test_connection_status_not_connected(mock_user_and_workspace):
    """Verify /connection-status returns not_connected when user has no linked accounts."""
    user, workspace = mock_user_and_workspace
    mock_session = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = []
    mock_session.execute.return_value = mock_result

    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_current_workspace] = lambda: workspace
    app.dependency_overrides[get_db] = lambda: mock_session

    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get("/api/instagram/connection-status")
            assert resp.status_code == 200
            data = resp.json()
            assert data["status"] == "not_connected"
            assert data["account"] is None
            assert data["requires_connect"] is True
            assert data["requires_reconnect"] is False
    finally:
        app.dependency_overrides.clear()

@pytest.mark.asyncio
async def test_connection_status_connected_valid_token(mock_user_and_workspace):
    """Verify /connection-status returns connected with safe metadata when a valid account exists."""
    user, workspace = mock_user_and_workspace
    now = datetime.now(timezone.utc)
    account = InstagramAccount(
        id=uuid.uuid4(),
        workspace_id=workspace.id,
        user_id=user.id,
        ig_user_id="17841400123",
        username="top_creator",
        account_type="BUSINESS",
        follower_count=12500,
        access_token_encrypted=encrypt_token("valid_meta_token_12345"),
        token_expires_at=now + timedelta(days=45),
        is_active=True,
        auth_method="META_INSTAGRAM_OAUTH",
        connection_status="CONNECTED",
        last_validated_at=now,
        last_refreshed_at=now,
        connected_at=now,
        updated_at=now
    )

    mock_session = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [account]
    mock_session.execute.return_value = mock_result

    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_current_workspace] = lambda: workspace
    app.dependency_overrides[get_db] = lambda: mock_session

    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get("/api/instagram/connection-status")
            assert resp.status_code == 200
            data = resp.json()
            assert data["status"] == "connected"
            assert data["account"]["username"] == "top_creator"
            assert data["account"]["user_id"] == str(user.id)
            assert data["requires_reconnect"] is False
            # Verify no token secret exposed
            assert "access_token" not in str(data)
            assert "encrypted" not in str(data)
    finally:
        app.dependency_overrides.clear()

@pytest.mark.asyncio
async def test_connection_status_token_expiring(mock_user_and_workspace):
    """Verify /connection-status returns token_expiring when token expires within 7 days."""
    user, workspace = mock_user_and_workspace
    now = datetime.now(timezone.utc)
    account = InstagramAccount(
        id=uuid.uuid4(),
        workspace_id=workspace.id,
        user_id=user.id,
        ig_user_id="17841400123",
        username="top_creator",
        account_type="BUSINESS",
        follower_count=12500,
        access_token_encrypted=encrypt_token("valid_meta_token_12345"),
        token_expires_at=now + timedelta(days=4),
        is_active=True,
        auth_method="META_INSTAGRAM_OAUTH",
        connection_status="CONNECTED",
        last_validated_at=now,
        last_refreshed_at=now,
        connected_at=now,
        updated_at=now
    )

    mock_session = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [account]
    mock_session.execute.return_value = mock_result

    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_current_workspace] = lambda: workspace
    app.dependency_overrides[get_db] = lambda: mock_session

    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get("/api/instagram/connection-status")
            assert resp.status_code == 200
            data = resp.json()
            assert data["status"] == "token_expiring"
            assert data["account"]["username"] == "top_creator"
            assert data["requires_reconnect"] is False
    finally:
        app.dependency_overrides.clear()

@pytest.mark.asyncio
async def test_connection_status_expired_token_requires_reauthorization(mock_user_and_workspace):
    """Verify /connection-status returns reauthorization_required when token has passed expiry date."""
    user, workspace = mock_user_and_workspace
    now = datetime.now(timezone.utc)
    account = InstagramAccount(
        id=uuid.uuid4(),
        workspace_id=workspace.id,
        user_id=user.id,
        ig_user_id="17841400123",
        username="expired_creator",
        account_type="BUSINESS",
        follower_count=1000,
        access_token_encrypted=encrypt_token("expired_token"),
        token_expires_at=now - timedelta(hours=2),
        is_active=True,
        auth_method="META_INSTAGRAM_OAUTH",
        connection_status="REAUTHORIZATION_REQUIRED",
        last_error_code="TOKEN_EXPIRED",
        connected_at=now - timedelta(days=61),
        updated_at=now
    )

    mock_session = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [account]
    mock_session.execute.return_value = mock_result

    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_current_workspace] = lambda: workspace
    app.dependency_overrides[get_db] = lambda: mock_session

    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get("/api/instagram/connection-status")
            assert resp.status_code == 200
            data = resp.json()
            assert data["status"] == "reauthorization_required"
            assert data["requires_reconnect"] is True
            assert data["error_code"] == "TOKEN_EXPIRED"
    finally:
        app.dependency_overrides.clear()

@pytest.mark.asyncio
async def test_token_refresh_24h_eligibility(mock_user_and_workspace):
    """
    Verify Meta 24h refresh rule:
    If a token was refreshed <24h ago, /refresh-token skips the external Meta call
    and returns the currently valid account without raising an error.
    """
    user, workspace = mock_user_and_workspace
    now = datetime.now(timezone.utc)
    account_id = uuid.uuid4()
    account = InstagramAccount(
        id=account_id,
        workspace_id=workspace.id,
        user_id=user.id,
        ig_user_id="17841400123",
        username="active_creator",
        account_type="BUSINESS",
        follower_count=5000,
        access_token_encrypted=encrypt_token("valid_recent_token"),
        token_expires_at=now + timedelta(days=58),
        is_active=True,
        auth_method="META_INSTAGRAM_OAUTH",
        connection_status="CONNECTED",
        last_validated_at=now - timedelta(hours=2),
        last_refreshed_at=now - timedelta(hours=2), # refreshed only 2 hours ago
        connected_at=now - timedelta(days=2),
        updated_at=now
    )

    mock_session = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = account
    mock_session.execute.return_value = mock_result

    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_current_workspace] = lambda: workspace
    app.dependency_overrides[get_db] = lambda: mock_session

    try:
        with patch("app.integrations.instagram.oauth.MetaOAuth.refresh_long_lived_token") as mock_refresh:
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                resp = await client.post(f"/api/instagram/accounts/{account_id}/refresh-token")
                assert resp.status_code == 200
                data = resp.json()
                assert data["username"] == "active_creator"
                # Meta API call should be skipped because token is <24 hours old
                mock_refresh.assert_not_called()
    finally:
        app.dependency_overrides.clear()

@pytest.mark.asyncio
async def test_disconnect_instagram_account_updates_persistence_status(mock_user_and_workspace):
    """Verify disconnect_instagram_account sets connection_status to DISCONNECTED and wipes encrypted token."""
    user, workspace = mock_user_and_workspace
    now = datetime.now(timezone.utc)
    account_id = uuid.uuid4()
    account = InstagramAccount(
        id=account_id,
        workspace_id=workspace.id,
        user_id=user.id,
        ig_user_id="17841400123",
        username="disconnecting_creator",
        access_token_encrypted=encrypt_token("token_to_wipe"),
        token_expires_at=now + timedelta(days=30),
        is_active=True,
        connection_status="CONNECTED"
    )

    mock_session = AsyncMock()
    acc_res = MagicMock()
    acc_res.scalar_one_or_none.return_value = account
    auto_res = MagicMock()
    auto_res.scalars.return_value.all.return_value = []
    mock_session.execute.side_effect = [acc_res, auto_res]

    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_current_workspace] = lambda: workspace
    app.dependency_overrides[get_db] = lambda: mock_session

    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.delete(f"/api/instagram/accounts/{account_id}")
            assert resp.status_code == 204
            assert account.is_active is False
            assert account.connection_status == "DISCONNECTED"
            assert account.access_token_encrypted == ""
    finally:
        app.dependency_overrides.clear()

@pytest.mark.asyncio
async def test_multi_user_isolation(mock_user_and_workspace):
    """Verify that User A cannot view or disconnect User B's Instagram account."""
    user_a, workspace_a = mock_user_and_workspace
    user_b_id = uuid.uuid4()
    ws_b_id = uuid.uuid4()
    user_b = User(id=user_b_id, email="other@comlina.ai", full_name="User B")
    workspace_b = Workspace(id=ws_b_id, name="Other WS", slug="other-ws")

    # Account belongs to User B in Workspace B
    account_b_id = uuid.uuid4()
    account_b = InstagramAccount(
        id=account_b_id,
        workspace_id=ws_b_id,
        user_id=user_b_id,
        ig_user_id="999999",
        username="user_b_ig",
        access_token_encrypted=encrypt_token("user_b_secret"),
        is_active=True,
        connection_status="CONNECTED"
    )

    # When User A queries accounts, mock_db returns empty (because DB filter filters it out)
    mock_session = AsyncMock()
    mock_res = MagicMock()
    mock_res.scalar_one_or_none.return_value = None  # User A cannot find User B's account
    mock_res.scalars.return_value.all.return_value = []
    mock_session.execute.return_value = mock_res

    app.dependency_overrides[get_current_user] = lambda: user_a
    app.dependency_overrides[get_current_workspace] = lambda: workspace_a
    app.dependency_overrides[get_db] = lambda: mock_session

    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            # User A tries to disconnect User B's account
            resp = await client.delete(f"/api/instagram/accounts/{account_b_id}")
            assert resp.status_code == 404
            assert resp.json()["detail"] == "Instagram account not found"

            # User A lists accounts - returns empty
            list_resp = await client.get("/api/instagram/accounts")
            assert list_resp.status_code == 200
            assert list_resp.json() == []
    finally:
        app.dependency_overrides.clear()

@pytest.mark.asyncio
async def test_token_refresh_fallback_to_connected_at(mock_user_and_workspace):
    """
    Verify Meta 24h refresh rule:
    When last_refreshed_at is None, connected_at is used as fallback.
    If connected <24h ago, /refresh-token skips the external Meta call
    and preserves CONNECTED status.
    """
    user, workspace = mock_user_and_workspace
    now = datetime.now(timezone.utc)
    account_id = uuid.uuid4()
    account = InstagramAccount(
        id=account_id,
        workspace_id=workspace.id,
        user_id=user.id,
        ig_user_id="17841400123",
        username="newly_connected_creator",
        access_token_encrypted=encrypt_token("valid_recent_token"),
        account_type="BUSINESS",
        follower_count=1000,
        is_active=True,
        connection_status="CONNECTED",
        last_refreshed_at=None,
        connected_at=now - timedelta(hours=3), # connected 3 hours ago
        updated_at=now
    )

    mock_session = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = account
    mock_session.execute.return_value = mock_result

    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_current_workspace] = lambda: workspace
    app.dependency_overrides[get_db] = lambda: mock_session

    try:
        with patch("app.integrations.instagram.oauth.MetaOAuth.refresh_long_lived_token") as mock_refresh:
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                resp = await client.post(f"/api/instagram/accounts/{account_id}/refresh-token")
                assert resp.status_code == 200
                data = resp.json()
                assert data["username"] == "newly_connected_creator"
                assert data["connection_status"] == "CONNECTED"
                # Meta API call should be skipped because token was connected <24h ago
                mock_refresh.assert_not_called()
    finally:
        app.dependency_overrides.clear()

@pytest.mark.asyncio
async def test_list_media_code_190_profile_check_preserves_connection(mock_user_and_workspace):
    """
    Verify that if list_media encounters MetaTokenExpiredError (code 190),
    it checks token liveness via fetch_instagram_profile before revoking.
    If profile is still valid, the account is NOT marked REAUTHORIZATION_REQUIRED.
    """
    from app.integrations.instagram.exceptions import MetaTokenExpiredError

    user, workspace = mock_user_and_workspace
    now = datetime.now(timezone.utc)
    account_id = uuid.uuid4()
    account = InstagramAccount(
        id=account_id,
        workspace_id=workspace.id,
        user_id=user.id,
        ig_user_id="17841400123",
        username="resilient_creator",
        access_token_encrypted=encrypt_token("EAA_sample_long_lived_token"),
        token_expires_at=now + timedelta(days=50),
        is_active=True,
        connection_status="CONNECTED",
        connected_at=now,
        updated_at=now
    )

    mock_session = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalars.return_value.first.return_value = account
    mock_session.execute.return_value = mock_result

    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_current_workspace] = lambda: workspace
    app.dependency_overrides[get_db] = lambda: mock_session

    try:
        with patch("app.api.instagram.MetaGraphClient") as mock_client_cls, \
             patch("app.api.instagram.MetaOAuth.fetch_instagram_profile") as mock_fetch_profile:
            mock_client = AsyncMock()
            mock_client_cls.return_value = mock_client
            # Simulate endpoint raising token expired error
            mock_client.get.side_effect = MetaTokenExpiredError("Invalid OAuth access token", 190)
            # But profile check verifies token is alive!
            mock_fetch_profile.return_value = {"id": "17841400123", "username": "resilient_creator"}

            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                resp = await client.get("/api/instagram/media")
                # Returns 502 instead of 409, and does NOT corrupt connection_status
                assert resp.status_code == 502
                assert account.connection_status == "CONNECTED"
    finally:
        app.dependency_overrides.clear()

@pytest.mark.asyncio
async def test_refresh_token_meta_error_profile_check_preserves_connection(mock_user_and_workspace):
    """
    Verify that when refresh_account_token encounters a MetaOAuthError,
    it verifies token liveness. If token is alive, connection_status is preserved.
    """
    from app.integrations.instagram.oauth import MetaOAuthError

    user, workspace = mock_user_and_workspace
    now = datetime.now(timezone.utc)
    account_id = uuid.uuid4()
    account = InstagramAccount(
        id=account_id,
        workspace_id=workspace.id,
        user_id=user.id,
        ig_user_id="17841400123",
        username="resilient_creator_2",
        access_token_encrypted=encrypt_token("sample_token_abc"),
        token_expires_at=now + timedelta(days=20),
        is_active=True,
        connection_status="CONNECTED",
        last_refreshed_at=now - timedelta(days=2), # older than 24h
        connected_at=now - timedelta(days=5),
        updated_at=now
    )

    mock_session = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = account
    mock_session.execute.return_value = mock_result

    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_current_workspace] = lambda: workspace
    app.dependency_overrides[get_db] = lambda: mock_session

    try:
        with patch("app.api.instagram.MetaOAuth.refresh_long_lived_token") as mock_refresh, \
             patch("app.api.instagram.MetaOAuth.fetch_instagram_profile") as mock_fetch_profile:
            # Simulate Meta error
            mock_refresh.side_effect = MetaOAuthError("Invalid request: temporary Meta rejection")
            # Profile check confirms token is actually active
            mock_fetch_profile.return_value = {"id": "17841400123", "username": "resilient_creator_2"}

            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                resp = await client.post(f"/api/instagram/accounts/{account_id}/refresh-token")
                assert resp.status_code == 400
                # Connection status is NOT corrupted to REAUTHORIZATION_REQUIRED
                assert account.connection_status == "CONNECTED"
    finally:
        app.dependency_overrides.clear()

