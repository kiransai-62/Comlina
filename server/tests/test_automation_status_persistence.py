# server/tests/test_automation_status_persistence.py
import uuid
import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy import select

from app.main import app
from app.core.database import get_db_session
from app.models import User, Workspace, WorkspaceMember, InstagramAccount, Automation
from app.api.auth import create_backend_jwt
from app.core.encryption import encrypt_token


@pytest.fixture
async def setup_test_workspaces():
    """
    Sets up two tenants with automations in different initial states.
    """
    async with get_db_session() as session:
        # Tenant A
        user_a = User(
            id=uuid.uuid4(),
            email=f"tenant_a_{uuid.uuid4().hex[:8]}@comlina.ai",
            full_name="Tenant A",
            timezone="UTC"
        )
        ws_a = Workspace(
            id=uuid.uuid4(),
            name="Workspace A",
            slug=f"wsa-{uuid.uuid4().hex[:8]}",
            plan_tier="PRO"
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
            username="brand_a_official",
            account_type="BUSINESS",
            follower_count=5000,
            access_token_encrypted=encrypt_token("dummy_token_a"),
            is_active=True
        )
        # Active automation for Tenant A
        auto_active_a = Automation(
            id=uuid.uuid4(),
            workspace_id=ws_a.id,
            instagram_account_id=ig_a.id,
            name="Active Promo Flow",
            trigger_type="COMMENT",
            flow_definition={"nodes": [], "trigger": {"triggerMode": "any_keyword"}, "status": "ACTIVE"},
            status="ACTIVE"
        )
        # Paused automation for Tenant A
        auto_paused_a = Automation(
            id=uuid.uuid4(),
            workspace_id=ws_a.id,
            instagram_account_id=ig_a.id,
            name="Paused Webinar Flow",
            trigger_type="COMMENT",
            flow_definition={"nodes": [], "trigger": {"triggerMode": "specific_keywords"}, "status": "PAUSED"},
            status="PAUSED"
        )
        session.add_all([member_a, ig_a, auto_active_a, auto_paused_a])

        # Tenant B
        user_b = User(
            id=uuid.uuid4(),
            email=f"tenant_b_{uuid.uuid4().hex[:8]}@comlina.ai",
            full_name="Tenant B",
            timezone="UTC"
        )
        ws_b = Workspace(
            id=uuid.uuid4(),
            name="Workspace B",
            slug=f"wsb-{uuid.uuid4().hex[:8]}",
            plan_tier="FREE"
        )
        session.add_all([user_b, ws_b])
        await session.flush()

        member_b = WorkspaceMember(
            id=uuid.uuid4(),
            workspace_id=ws_b.id,
            user_id=user_b.id,
            role="OWNER"
        )
        session.add(member_b)
        await session.commit()

        token_a = create_backend_jwt(str(user_a.id), user_a.email, token_type="access")
        token_b = create_backend_jwt(str(user_b.id), user_b.email, token_type="access")

        return {
            "ws_a": ws_a,
            "user_a": user_a,
            "ig_a": ig_a,
            "auto_active_a": auto_active_a,
            "auto_paused_a": auto_paused_a,
            "headers_a": {"Authorization": f"Bearer {token_a}"},
            "ws_b": ws_b,
            "user_b": user_b,
            "headers_b": {"Authorization": f"Bearer {token_b}"},
        }


@pytest.mark.asyncio
async def test_automation_status_transition_active_to_paused(setup_test_workspaces):
    """
    Test transition ACTIVE -> PAUSED:
    1. Send PUT /api/automations/{id} with status=PAUSED.
    2. Verify 200 response with status=PAUSED.
    3. Verify DB record is persisted with status=PAUSED and flow_definition['status']=PAUSED.
    4. Verify GET /api/automations and GET /api/automations/{id} return PAUSED (refresh/reload persistence).
    5. Verify worker query for active automations excludes this paused automation.
    """
    ctx = setup_test_workspaces
    auto_id = ctx["auto_active_a"].id
    ws_id = ctx["ws_a"].id

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # 1. Update status to PAUSED
        res = await ac.put(
            f"/api/automations/{auto_id}",
            json={"status": "PAUSED"},
            headers=ctx["headers_a"]
        )
        assert res.status_code == 200, res.text
        data = res.json()
        assert data["id"] == str(auto_id)
        assert data["status"] == "PAUSED"

        # 2. Check persistence on page refresh / reload simulation via GET list
        list_res = await ac.get("/api/automations", headers=ctx["headers_a"])
        assert list_res.status_code == 200
        items = list_res.json()
        target = next((item for item in items if item["id"] == str(auto_id)), None)
        assert target is not None
        assert target["status"] == "PAUSED"

        # 3. Check persistence on GET single automation
        detail_res = await ac.get(f"/api/automations/{auto_id}", headers=ctx["headers_a"])
        assert detail_res.status_code == 200
        assert detail_res.json()["status"] == "PAUSED"

    # 4. Check direct database persistence
    async with get_db_session() as session:
        stmt = select(Automation).where(Automation.id == auto_id)
        db_auto = (await session.execute(stmt)).scalar_one()
        assert db_auto.status == "PAUSED"
        assert db_auto.flow_definition.get("status") == "PAUSED"

        # 5. Worker query parity check:
        # Worker queries: select(Automation).where(workspace_id == ..., status == "ACTIVE")
        worker_stmt = select(Automation).where(
            Automation.workspace_id == ws_id,
            Automation.status == "ACTIVE"
        )
        active_for_worker = (await session.execute(worker_stmt)).scalars().all()
        active_ids = [str(a.id) for a in active_for_worker]
        assert str(auto_id) not in active_ids, "Paused automation must not be picked up by worker query"


@pytest.mark.asyncio
async def test_automation_status_transition_paused_to_active(setup_test_workspaces):
    """
    Test transition PAUSED -> ACTIVE:
    1. Send PUT /api/automations/{id} with status=ACTIVE.
    2. Verify 200 response with status=ACTIVE.
    3. Verify DB record is persisted with status=ACTIVE, flow_definition['status']=ACTIVE, and published_at set.
    4. Verify GET /api/automations returns ACTIVE (refresh/reload persistence).
    5. Verify worker query includes this automation.
    """
    ctx = setup_test_workspaces
    auto_id = ctx["auto_paused_a"].id
    ws_id = ctx["ws_a"].id

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # 1. Update status to ACTIVE
        res = await ac.put(
            f"/api/automations/{auto_id}",
            json={"status": "ACTIVE"},
            headers=ctx["headers_a"]
        )
        assert res.status_code == 200, res.text
        data = res.json()
        assert data["id"] == str(auto_id)
        assert data["status"] == "ACTIVE"

        # 2. Check persistence on GET list
        list_res = await ac.get("/api/automations", headers=ctx["headers_a"])
        assert list_res.status_code == 200
        items = list_res.json()
        target = next((item for item in items if item["id"] == str(auto_id)), None)
        assert target is not None
        assert target["status"] == "ACTIVE"

    # 3. Check direct database persistence
    async with get_db_session() as session:
        stmt = select(Automation).where(Automation.id == auto_id)
        db_auto = (await session.execute(stmt)).scalar_one()
        assert db_auto.status == "ACTIVE"
        assert db_auto.flow_definition.get("status") == "ACTIVE"
        assert db_auto.published_at is not None

        # 4. Worker query parity check:
        worker_stmt = select(Automation).where(
            Automation.workspace_id == ws_id,
            Automation.status == "ACTIVE"
        )
        active_for_worker = (await session.execute(worker_stmt)).scalars().all()
        active_ids = [str(a.id) for a in active_for_worker]
        assert str(auto_id) in active_ids, "Activated automation must be returned by worker query"


@pytest.mark.asyncio
async def test_automation_status_invalid_transition_rejected(setup_test_workspaces):
    """
    Test schema validation rejects invalid status values (e.g. DELETED, RUNNING, or random strings).
    """
    ctx = setup_test_workspaces
    auto_id = ctx["auto_active_a"].id

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.put(
            f"/api/automations/{auto_id}",
            json={"status": "INVALID_STATE"},
            headers=ctx["headers_a"]
        )
        assert res.status_code == 422, "Invalid status values must be rejected with 422"

    # Verify status in DB was NOT changed
    async with get_db_session() as session:
        stmt = select(Automation).where(Automation.id == auto_id)
        db_auto = (await session.execute(stmt)).scalar_one()
        assert db_auto.status == "ACTIVE"


@pytest.mark.asyncio
async def test_automation_status_tenant_authorization_isolation(setup_test_workspaces):
    """
    Test that Tenant B cannot toggle or modify Tenant A's automation status (BOLA protection).
    Expects 404 Not Found so no existence leakage occurs across workspaces.
    """
    ctx = setup_test_workspaces
    auto_id_a = ctx["auto_active_a"].id

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Tenant B attempts to pause Tenant A's automation
        res = await ac.put(
            f"/api/automations/{auto_id_a}",
            json={"status": "PAUSED"},
            headers=ctx["headers_b"]
        )
        assert res.status_code == 404
        assert "not found" in res.json()["detail"].lower()

    # Verify Tenant A's automation status is completely untouched
    async with get_db_session() as session:
        stmt = select(Automation).where(Automation.id == auto_id_a)
        db_auto = (await session.execute(stmt)).scalar_one()
        assert db_auto.status == "ACTIVE"


@pytest.mark.asyncio
async def test_automation_status_unauthenticated_rejected(setup_test_workspaces):
    """
    Test unauthenticated mutation requests are rejected with 401.
    """
    ctx = setup_test_workspaces
    auto_id_a = ctx["auto_active_a"].id

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.put(
            f"/api/automations/{auto_id_a}",
            json={"status": "PAUSED"}
        )
        assert res.status_code == 401
