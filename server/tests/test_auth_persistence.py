# server/tests/test_auth_persistence.py
import pytest
import uuid
from datetime import datetime, timedelta, timezone
from httpx import AsyncClient, ASGITransport
from sqlalchemy import select
from app.main import app
from app.core.database import get_db_session
from app.models import User, Workspace, WorkspaceMember, InstagramAccount
from app.core.encryption import encrypt_token
from app.api.auth import create_backend_jwt


@pytest.mark.asyncio
async def test_backend_auth_tokens_and_refresh():
    """Verify access and refresh token issuance and refresh endpoint."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        email = f"persist_{uuid.uuid4().hex[:8]}@comlina.ai"
        signup_res = await ac.post("/api/auth/signup", json={
            "email": email,
            "password": "Password123!",
            "full_name": "Persist User"
        })
        assert signup_res.status_code == 200, signup_res.text
        data = signup_res.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["refresh_token"] is not None

        access_token = data["access_token"]
        refresh_token = data["refresh_token"]

        # 1. Use access token on protected endpoint /auth/me
        me_res = await ac.get("/api/auth/me", headers={"Authorization": f"Bearer {access_token}"})
        assert me_res.status_code == 200
        me_data = me_res.json()
        assert me_data["email"] == email
        assert "access_token" in me_data
        assert "refresh_token" in me_data
        assert "session" in me_data
        assert me_data["session"]["access_token"] is not None

        # 2. Refresh token CANNOT be used as access token on protected endpoint
        bad_me = await ac.get("/api/auth/me", headers={"Authorization": f"Bearer {refresh_token}"})
        assert bad_me.status_code == 401

        # 3. Call /auth/refresh with valid refresh token
        ref_res = await ac.post("/api/auth/refresh", json={"refresh_token": refresh_token})
        assert ref_res.status_code == 200
        ref_data = ref_res.json()
        assert "access_token" in ref_data
        assert "refresh_token" in ref_data
        new_access = ref_data["access_token"]
        new_refresh = ref_data["refresh_token"]

        # 4. Use new access token on protected endpoint
        new_me_res = await ac.get("/api/auth/me", headers={"Authorization": f"Bearer {new_access}"})
        assert new_me_res.status_code == 200
        assert new_me_res.json()["email"] == email

        # 5. Invalid refresh token returns 401
        invalid_res = await ac.post("/api/auth/refresh", json={"refresh_token": "invalid.jwt.token"})
        assert invalid_res.status_code == 401


@pytest.mark.asyncio
async def test_user_email_unification():
    """Verify that get_current_user resolves the same user record by email even if token sub UUID is different."""
    async with get_db_session() as session:
        email = f"unify_{uuid.uuid4().hex[:8]}@comlina.ai"
        orig_user = User(
            id=uuid.uuid4(),
            email=email,
            full_name="Original User",
            timezone="UTC"
        )
        session.add(orig_user)
        ws = Workspace(name="Original WS", slug=f"ws-{uuid.uuid4().hex[:8]}")
        session.add(ws)
        await session.flush()
        mem = WorkspaceMember(workspace_id=ws.id, user_id=orig_user.id, role="OWNER")
        session.add(mem)
        await session.commit()

        # Token generated with a different UUID (e.g. from Supabase or another provider) but matching email
        alt_uuid = str(uuid.uuid4())
        alt_token = create_backend_jwt(alt_uuid, email, token_type="access")

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.get("/api/auth/me", headers={"Authorization": f"Bearer {alt_token}"})
        assert res.status_code == 200
        body = res.json()
        assert body["email"] == email
        # Must resolve to the original user's ID and workspace!
        assert body["id"] == str(orig_user.id)
        assert body["workspace"]["id"] == str(ws.id)


@pytest.mark.asyncio
async def test_instagram_account_status_and_rebinding():
    """Verify that Instagram accounts are listed with computed status and rebound gracefully."""
    async with get_db_session() as session:
        email = f"ig_owner_{uuid.uuid4().hex[:8]}@comlina.ai"
        user = User(id=uuid.uuid4(), email=email, full_name="IG Owner")
        session.add(user)
        ws1 = Workspace(name="WS1", slug=f"ws1-{uuid.uuid4().hex[:8]}")
        ws2 = Workspace(name="WS2", slug=f"ws2-{uuid.uuid4().hex[:8]}")
        session.add_all([ws1, ws2])
        await session.flush()
        m1 = WorkspaceMember(workspace_id=ws1.id, user_id=user.id, role="OWNER")
        m2 = WorkspaceMember(workspace_id=ws2.id, user_id=user.id, role="OWNER")
        session.add_all([m1, m2])

        # Active account with upcoming expiration
        ig1 = InstagramAccount(
            workspace_id=ws1.id,
            ig_user_id=f"ig_{uuid.uuid4().hex[:10]}",
            username="active_creator",
            access_token_encrypted=encrypt_token("mock_token_1"),
            token_expires_at=datetime.now(timezone.utc) + timedelta(days=30),
            is_active=True
        )
        # Inactive account requiring reauthorization
        ig2 = InstagramAccount(
            workspace_id=ws1.id,
            ig_user_id=f"ig_{uuid.uuid4().hex[:10]}",
            username="expired_creator",
            access_token_encrypted=encrypt_token("mock_token_2"),
            token_expires_at=datetime.now(timezone.utc) - timedelta(days=1),
            is_active=False
        )
        session.add_all([ig1, ig2])
        await session.commit()

        token = create_backend_jwt(str(user.id), email)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Query accounts for ws1
        headers = {"Authorization": f"Bearer {token}", "X-Workspace-ID": str(ws1.id)}
        res = await ac.get("/api/instagram/accounts", headers=headers)
        assert res.status_code == 200
        accounts = res.json()
        assert len(accounts) == 2

        by_username = {a["username"]: a for a in accounts}
        assert by_username["active_creator"]["status"] == "CONNECTED"
        assert by_username["expired_creator"]["status"] == "REAUTHORIZATION_REQUIRED"
