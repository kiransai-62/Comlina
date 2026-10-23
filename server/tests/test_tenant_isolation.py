# server/tests/test_tenant_isolation.py
import uuid
import pytest
from datetime import datetime, timezone
from httpx import AsyncClient, ASGITransport
from sqlalchemy import select

from app.main import app
from app.core.database import get_db_session
from app.models import (
    User,
    Workspace,
    WorkspaceMember,
    InstagramAccount,
    Automation,
    Contact,
    Conversation,
    Message,
)
from app.api.auth import create_backend_jwt
from app.core.encryption import encrypt_token


@pytest.fixture
async def setup_two_tenants():
    """
    Sets up two isolated tenants (User A / Workspace A and User B / Workspace B)
    with populated test data across all tenant-scoped entities.
    """
    async with get_db_session() as session:
        # Tenant A
        user_a = User(
            id=uuid.uuid4(),
            email=f"user_a_{uuid.uuid4().hex[:8]}@comlina.ai",
            full_name="User A",
            timezone="UTC"
        )
        ws_a = Workspace(
            id=uuid.uuid4(),
            name="Workspace A",
            slug=f"wsa-{uuid.uuid4().hex[:8]}",
            plan_tier="PREMIUM"
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
            username="brand_a",
            account_type="BUSINESS",
            follower_count=1000,
            access_token_encrypted=encrypt_token("dummy_token_a"),
            is_active=True
        )
        auto_a = Automation(
            id=uuid.uuid4(),
            workspace_id=ws_a.id,
            instagram_account_id=ig_a.id,
            name="Automation A",
            trigger_type="COMMENT",
            flow_definition={"nodes": [], "trigger": {"triggerMode": "any_keyword"}},
            status="DRAFT"
        )
        contact_a = Contact(
            id=uuid.uuid4(),
            workspace_id=ws_a.id,
            instagram_account_id=ig_a.id,
            ig_user_id=f"ig_u_a_{uuid.uuid4().hex[:8]}",
            username="fan_of_a",
            full_name="Fan A",
            follower_status="FOLLOWING"
        )
        session.add_all([member_a, ig_a, auto_a, contact_a])
        await session.flush()

        conv_a = Conversation(
            id=uuid.uuid4(),
            workspace_id=ws_a.id,
            instagram_account_id=ig_a.id,
            contact_id=contact_a.id,
            status="OPEN"
        )
        session.add(conv_a)
        await session.flush()

        msg_a = Message(
            id=uuid.uuid4(),
            workspace_id=ws_a.id,
            conversation_id=conv_a.id,
            sender_type="CONTACT",
            text="Hello from Fan A"
        )
        session.add(msg_a)

        # Tenant B
        user_b = User(
            id=uuid.uuid4(),
            email=f"user_b_{uuid.uuid4().hex[:8]}@comlina.ai",
            full_name="User B",
            timezone="UTC"
        )
        ws_b = Workspace(
            id=uuid.uuid4(),
            name="Workspace B",
            slug=f"wsb-{uuid.uuid4().hex[:8]}",
            plan_tier="PREMIUM"
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
            username="brand_b",
            account_type="BUSINESS",
            follower_count=2000,
            access_token_encrypted=encrypt_token("dummy_token_b"),
            is_active=True
        )
        auto_b = Automation(
            id=uuid.uuid4(),
            workspace_id=ws_b.id,
            instagram_account_id=ig_b.id,
            name="Automation B",
            trigger_type="COMMENT",
            flow_definition={"nodes": [], "trigger": {"triggerMode": "any_keyword"}},
            status="DRAFT"
        )
        contact_b = Contact(
            id=uuid.uuid4(),
            workspace_id=ws_b.id,
            instagram_account_id=ig_b.id,
            ig_user_id=f"ig_u_b_{uuid.uuid4().hex[:8]}",
            username="fan_of_b",
            full_name="Fan B",
            follower_status="FOLLOWING"
        )
        session.add_all([member_b, ig_b, auto_b, contact_b])
        await session.flush()

        conv_b = Conversation(
            id=uuid.uuid4(),
            workspace_id=ws_b.id,
            instagram_account_id=ig_b.id,
            contact_id=contact_b.id,
            status="OPEN"
        )
        session.add(conv_b)
        await session.flush()

        msg_b = Message(
            id=uuid.uuid4(),
            workspace_id=ws_b.id,
            conversation_id=conv_b.id,
            sender_type="CONTACT",
            text="Hello from Fan B"
        )
        session.add(msg_b)
        await session.commit()

        token_a = create_backend_jwt(str(user_a.id), user_a.email, token_type="access")
        token_b = create_backend_jwt(str(user_b.id), user_b.email, token_type="access")

        return {
            "user_a": user_a,
            "ws_a": ws_a,
            "ig_a": ig_a,
            "auto_a": auto_a,
            "contact_a": contact_a,
            "conv_a": conv_a,
            "msg_a": msg_a,
            "token_a": token_a,
            "headers_a": {"Authorization": f"Bearer {token_a}"},
            "user_b": user_b,
            "ws_b": ws_b,
            "ig_b": ig_b,
            "auto_b": auto_b,
            "contact_b": contact_b,
            "conv_b": conv_b,
            "msg_b": msg_b,
            "token_b": token_b,
            "headers_b": {"Authorization": f"Bearer {token_b}"},
        }


@pytest.mark.asyncio
async def test_workspace_isolation_and_spoof_prevention(setup_two_tenants):
    """Verify workspace listing, and that spoofing X-Workspace-ID raises 403 Forbidden."""
    tenants = setup_two_tenants
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # User A only sees Workspace A
        res_a = await ac.get("/api/workspaces", headers=tenants["headers_a"])
        assert res_a.status_code == 200
        ws_ids_a = [w["id"] for w in res_a.json()]
        assert str(tenants["ws_a"].id) in ws_ids_a
        assert str(tenants["ws_b"].id) not in ws_ids_a

        # User B only sees Workspace B
        res_b = await ac.get("/api/workspaces", headers=tenants["headers_b"])
        assert res_b.status_code == 200
        ws_ids_b = [w["id"] for w in res_b.json()]
        assert str(tenants["ws_b"].id) in ws_ids_b
        assert str(tenants["ws_a"].id) not in ws_ids_b

        # User A attempts to access /workspaces/current with X-Workspace-ID of Workspace B -> 403
        spoof_headers = {
            **tenants["headers_a"],
            "X-Workspace-ID": str(tenants["ws_b"].id),
        }
        res_spoof = await ac.get("/api/workspaces/current", headers=spoof_headers)
        assert res_spoof.status_code == 403
        assert "Not a member" in res_spoof.json()["detail"]

        # User A attempts to PATCH /workspaces/current with X-Workspace-ID of Workspace B -> 403
        res_patch_spoof = await ac.patch(
            "/api/workspaces/current",
            json={"name": "Hacked Workspace"},
            headers=spoof_headers,
        )
        assert res_patch_spoof.status_code == 403

        # Malformed X-Workspace-ID returns 400
        bad_ws_headers = {
            **tenants["headers_a"],
            "X-Workspace-ID": "not-a-valid-uuid",
        }
        res_bad = await ac.get("/api/workspaces/current", headers=bad_ws_headers)
        assert res_bad.status_code == 400


@pytest.mark.asyncio
async def test_automations_cross_tenant_isolation(setup_two_tenants):
    """Verify automations CRUD and publish operations reject cross-tenant access with 404."""
    tenants = setup_two_tenants
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # 1. Listing is strictly scoped
        res_list = await ac.get("/api/automations", headers=tenants["headers_a"])
        assert res_list.status_code == 200
        auto_ids = [a["id"] for a in res_list.json()]
        assert str(tenants["auto_a"].id) in auto_ids
        assert str(tenants["auto_b"].id) not in auto_ids

        # 2. GET /automations/{id} across tenants returns 404
        res_get = await ac.get(
            f"/api/automations/{tenants['auto_b'].id}",
            headers=tenants["headers_a"]
        )
        assert res_get.status_code == 404

        # 3. PUT /automations/{id} across tenants returns 404
        res_put = await ac.put(
            f"/api/automations/{tenants['auto_b'].id}",
            json={"name": "Malicious Renaming"},
            headers=tenants["headers_a"]
        )
        assert res_put.status_code == 404

        # 4. DELETE /automations/{id} across tenants returns 404
        res_del = await ac.delete(
            f"/api/automations/{tenants['auto_b'].id}",
            headers=tenants["headers_a"]
        )
        assert res_del.status_code == 404

        # 5. POST /automations/{id}/publish across tenants returns 404
        res_pub = await ac.post(
            f"/api/automations/{tenants['auto_b'].id}/publish",
            headers=tenants["headers_a"]
        )
        assert res_pub.status_code == 404

        # 6. POST /automations with nested instagram_account_id belonging to another workspace returns 404 (BOLA protection)
        res_create_cross = await ac.post(
            "/api/automations",
            json={
                "name": "Cross-Account Automation",
                "instagram_account_id": str(tenants["ig_b"].id),
                "trigger_type": "COMMENT",
                "flow_definition": {"nodes": [], "trigger": {"triggerMode": "any_keyword"}}
            },
            headers=tenants["headers_a"]
        )
        assert res_create_cross.status_code == 404
        assert "Instagram account not found or does not belong to this workspace" in res_create_cross.json()["detail"]


@pytest.mark.asyncio
async def test_contacts_isolation_and_export(setup_two_tenants):
    """Verify contacts listing and CSV export never leak data across tenants."""
    tenants = setup_two_tenants
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Listing contacts
        res_a = await ac.get("/api/contacts", headers=tenants["headers_a"])
        assert res_a.status_code == 200
        contacts_a = res_a.json()
        usernames_a = [c["username"] for c in contacts_a]
        assert "fan_of_a" in usernames_a
        assert "fan_of_b" not in usernames_a

        # Exporting CSV
        res_csv_a = await ac.get("/api/contacts/export-csv", headers=tenants["headers_a"])
        assert res_csv_a.status_code == 200
        csv_text_a = res_csv_a.text
        assert "fan_of_a" in csv_text_a
        assert "fan_of_b" not in csv_text_a


@pytest.mark.asyncio
async def test_conversations_and_messages_cross_tenant_isolation(setup_two_tenants):
    """Verify conversations and nested message endpoints enforce multi-tenant isolation."""
    tenants = setup_two_tenants
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # List conversations
        res_convs = await ac.get("/api/conversations", headers=tenants["headers_a"])
        assert res_convs.status_code == 200
        conv_ids = [c["id"] for c in res_convs.json()]
        assert str(tenants["conv_a"].id) in conv_ids
        assert str(tenants["conv_b"].id) not in conv_ids

        # GET messages for other tenant's conversation returns 404
        res_cross_msgs = await ac.get(
            f"/api/conversations/{tenants['conv_b'].id}/messages",
            headers=tenants["headers_a"]
        )
        assert res_cross_msgs.status_code == 404

        # POST message to other tenant's conversation returns 404
        res_send_cross = await ac.post(
            f"/api/conversations/{tenants['conv_b'].id}/messages",
            json={"text": "Cross-tenant intrusion attempt"},
            headers=tenants["headers_a"]
        )
        assert res_send_cross.status_code == 404


@pytest.mark.asyncio
async def test_analytics_and_payments_usage_isolation(setup_two_tenants):
    """Verify analytics and usage endpoints return data isolated to current workspace."""
    tenants = setup_two_tenants
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Analytics summary
        res_analytics_a = await ac.get("/api/analytics/summary", headers=tenants["headers_a"])
        assert res_analytics_a.status_code == 200
        data_a = res_analytics_a.json()
        assert "automations" in data_a or "total_automations" in data_a or "kpis" in data_a

        # Payments usage summary
        res_usage_a = await ac.get("/api/payments/usage", headers=tenants["headers_a"])
        assert res_usage_a.status_code == 200
        usage_data = res_usage_a.json()
        assert usage_data["workspace_id"] == str(tenants["ws_a"].id)
        assert usage_data["plan_tier"] == "PREMIUM"


@pytest.mark.asyncio
async def test_instagram_accounts_cross_tenant_isolation(setup_two_tenants):
    """Verify Instagram account listing, token refresh, sync, and deletion are isolated."""
    tenants = setup_two_tenants
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # 1. Accounts list is strictly scoped
        res_accs = await ac.get("/api/instagram/accounts", headers=tenants["headers_a"])
        assert res_accs.status_code == 200
        acc_ids = [a["id"] for a in res_accs.json()]
        assert str(tenants["ig_a"].id) in acc_ids
        assert str(tenants["ig_b"].id) not in acc_ids

        # 2. Refresh token for other tenant's account returns 404
        res_ref = await ac.post(
            f"/api/instagram/accounts/{tenants['ig_b'].id}/refresh-token",
            headers=tenants["headers_a"]
        )
        assert res_ref.status_code == 404

        # 3. Sync profile for other tenant's account returns 404
        res_sync = await ac.post(
            f"/api/instagram/accounts/{tenants['ig_b'].id}/sync-profile",
            headers=tenants["headers_a"]
        )
        assert res_sync.status_code == 404

        # Also verify /sync endpoint directly
        res_sync_orig = await ac.post(
            f"/api/instagram/accounts/{tenants['ig_b'].id}/sync",
            headers=tenants["headers_a"]
        )
        assert res_sync_orig.status_code == 404

        # 4. Delete/disconnect other tenant's account returns 404
        res_del = await ac.delete(
            f"/api/instagram/accounts/{tenants['ig_b'].id}",
            headers=tenants["headers_a"]
        )
        assert res_del.status_code == 404
