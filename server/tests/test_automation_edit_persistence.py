# server/tests/test_automation_edit_persistence.py
import uuid
import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy import select, func

from app.main import app
from app.core.database import get_db_session
from app.models import User, Workspace, WorkspaceMember, InstagramAccount, Automation, AutomationVersion
from app.api.auth import create_backend_jwt
from app.core.encryption import encrypt_token


@pytest.fixture
async def setup_edit_tenants():
    """
    Sets up two isolated workspaces with initial automations and Instagram accounts.
    """
    async with get_db_session() as session:
        # Tenant A
        user_a = User(
            id=uuid.uuid4(),
            email=f"editor_a_{uuid.uuid4().hex[:8]}@comlina.ai",
            full_name="Editor A",
            timezone="UTC"
        )
        ws_a = Workspace(
            id=uuid.uuid4(),
            name="Workspace A",
            slug=f"wsa-{uuid.uuid4().hex[:8]}",
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
            username="brand_a_edit",
            account_type="BUSINESS",
            follower_count=5000,
            access_token_encrypted=encrypt_token("dummy_token_a"),
            is_active=True
        )
        ig_a2 = InstagramAccount(
            id=uuid.uuid4(),
            workspace_id=ws_a.id,
            user_id=user_a.id,
            ig_user_id=f"iga2_{uuid.uuid4().hex[:8]}",
            username="brand_a_second",
            account_type="BUSINESS",
            follower_count=3000,
            access_token_encrypted=encrypt_token("dummy_token_a2"),
            is_active=True
        )
        auto_draft_a = Automation(
            id=uuid.uuid4(),
            workspace_id=ws_a.id,
            instagram_account_id=ig_a.id,
            name="Original Draft Automation",
            description="Initial draft description",
            trigger_type="COMMENT",
            flow_definition={
                "version": 2,
                "type": "COMMENT_TO_DM",
                "trigger": {"type": "COMMENT", "triggerMode": "specific_keywords", "keywords": ["OLD"]},
                "status": "DRAFT"
            },
            status="DRAFT",
            version=1
        )
        session.add_all([member_a, ig_a, ig_a2, auto_draft_a])

        # Tenant B
        user_b = User(
            id=uuid.uuid4(),
            email=f"editor_b_{uuid.uuid4().hex[:8]}@comlina.ai",
            full_name="Editor B",
            timezone="UTC"
        )
        ws_b = Workspace(
            id=uuid.uuid4(),
            name="Workspace B",
            slug=f"wsb-{uuid.uuid4().hex[:8]}",
            plan_tier="FREE",
            max_automations=3
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
            username="brand_b_adversary",
            account_type="BUSINESS",
            follower_count=100,
            access_token_encrypted=encrypt_token("dummy_token_b"),
            is_active=True
        )
        session.add_all([member_b, ig_b])
        await session.commit()

        token_a = create_backend_jwt(str(user_a.id), user_a.email, token_type="access")
        token_b = create_backend_jwt(str(user_b.id), user_b.email, token_type="access")

        return {
            "ws_a": ws_a,
            "user_a": user_a,
            "ig_a": ig_a,
            "ig_a2": ig_a2,
            "auto_draft_a": auto_draft_a,
            "headers_a": {"Authorization": f"Bearer {token_a}"},
            "ws_b": ws_b,
            "user_b": user_b,
            "ig_b": ig_b,
            "headers_b": {"Authorization": f"Bearer {token_b}"},
        }


@pytest.mark.asyncio
async def test_edit_automation_updates_existing_record_without_creating_duplicate(setup_edit_tenants):
    """
    Verify that PUT /api/automations/{id} updates the existing record in place
    and does NOT create a duplicate automation in the workspace.
    """
    ctx = setup_edit_tenants
    auto_id = ctx["auto_draft_a"].id
    ws_id = ctx["ws_a"].id

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        update_payload = {
            "name": "Updated Flow Title",
            "description": "Updated description content",
            "status": "DRAFT",
            "flow_definition": {
                "version": 2,
                "type": "COMMENT_TO_DM",
                "trigger": {
                    "type": "COMMENT",
                    "triggerMode": "specific_keywords",
                    "keywords": ["NEWKEYWORD", "DISCOUNT"]
                },
                "status": "DRAFT"
            }
        }
        res = await ac.put(f"/api/automations/{auto_id}", json=update_payload, headers=ctx["headers_a"])
        assert res.status_code == 200, res.text
        data = res.json()
        assert data["id"] == str(auto_id)
        assert data["name"] == "Updated Flow Title"
        assert data["description"] == "Updated description content"
        assert data["status"] == "DRAFT"
        assert data["flow_definition"]["trigger"]["keywords"] == ["NEWKEYWORD", "DISCOUNT"]

    # Verify database state: total automations count in workspace MUST remain exactly 1
    async with get_db_session() as session:
        count_stmt = select(func.count(Automation.id)).where(Automation.workspace_id == ws_id)
        total_count = (await session.execute(count_stmt)).scalar()
        assert total_count == 1, "Editing must update in place; no duplicate records allowed"

        stmt = select(Automation).where(Automation.id == auto_id)
        db_auto = (await session.execute(stmt)).scalar_one()
        assert db_auto.name == "Updated Flow Title"
        assert db_auto.status == "DRAFT"
        assert db_auto.flow_definition["trigger"]["keywords"] == ["NEWKEYWORD", "DISCOUNT"]


@pytest.mark.asyncio
async def test_edit_draft_preserves_draft_status_and_does_not_publish(setup_edit_tenants):
    """
    Verify that saving an edited automation as DRAFT preserves status='DRAFT',
    does not set published_at, and creates no version snapshot.
    """
    ctx = setup_edit_tenants
    auto_id = ctx["auto_draft_a"].id

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.put(
            f"/api/automations/{auto_id}",
            json={
                "status": "DRAFT",
                "flow_definition": {
                    "version": 2,
                    "trigger": {"triggerMode": "any_keyword"},
                    "status": "DRAFT"
                }
            },
            headers=ctx["headers_a"]
        )
        assert res.status_code == 200
        assert res.json()["status"] == "DRAFT"

    async with get_db_session() as session:
        stmt = select(Automation).where(Automation.id == auto_id)
        db_auto = (await session.execute(stmt)).scalar_one()
        assert db_auto.status == "DRAFT"
        assert db_auto.published_at is None

        # Verify no version snapshot was created
        v_stmt = select(AutomationVersion).where(AutomationVersion.automation_id == auto_id)
        versions = (await session.execute(v_stmt)).scalars().all()
        assert len(versions) == 0


@pytest.mark.asyncio
async def test_edit_and_publish_flow_updates_and_creates_version(setup_edit_tenants):
    """
    Verify that editing an automation and publishing it:
    1. Updates flow_definition via PUT /api/automations/{id}
    2. Increments version and creates snapshot via POST /api/automations/{id}/publish
    3. Sets status to ACTIVE and records published_at
    """
    ctx = setup_edit_tenants
    auto_id = ctx["auto_draft_a"].id

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Step 1: Update flow definition
        put_res = await ac.put(
            f"/api/automations/{auto_id}",
            json={
                "name": "Live Published Playbook",
                "status": "ACTIVE",
                "flow_definition": {
                    "version": 2,
                    "type": "COMMENT_TO_DM",
                    "trigger": {"triggerMode": "any_keyword"},
                    "status": "ACTIVE"
                }
            },
            headers=ctx["headers_a"]
        )
        assert put_res.status_code == 200

        # Step 2: Publish automation snapshot
        pub_res = await ac.post(f"/api/automations/{auto_id}/publish", headers=ctx["headers_a"])
        assert pub_res.status_code == 200
        pub_data = pub_res.json()
        assert pub_data["status"] == "ACTIVE"
        assert pub_data["version"] == 2
        assert pub_data["published_at"] is not None

    async with get_db_session() as session:
        stmt = select(Automation).where(Automation.id == auto_id)
        db_auto = (await session.execute(stmt)).scalar_one()
        assert db_auto.status == "ACTIVE"
        assert db_auto.version == 2

        # Verify snapshot was created in automation_versions
        v_stmt = select(AutomationVersion).where(AutomationVersion.automation_id == auto_id)
        versions = (await session.execute(v_stmt)).scalars().all()
        assert len(versions) == 1
        assert versions[0].version == 2


@pytest.mark.asyncio
async def test_cross_workspace_edit_blocked_by_authorization(setup_edit_tenants):
    """
    Verify Tenant B cannot update Tenant A's automation (BOLA prevention).
    Returns 404 Not Found to prevent metadata and existence leakage.
    """
    ctx = setup_edit_tenants
    auto_id_a = ctx["auto_draft_a"].id

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.put(
            f"/api/automations/{auto_id_a}",
            json={"name": "Attacker Hijacked Title"},
            headers=ctx["headers_b"]
        )
        assert res.status_code == 404

    async with get_db_session() as session:
        stmt = select(Automation).where(Automation.id == auto_id_a)
        db_auto = (await session.execute(stmt)).scalar_one()
        assert db_auto.name == "Original Draft Automation", "Target automation must be untouched"


@pytest.mark.asyncio
async def test_edit_automation_cross_workspace_instagram_account_rejected(setup_edit_tenants):
    """
    Verify Tenant A cannot update their automation to point to Tenant B's Instagram account.
    Returns 404 Not Found.
    """
    ctx = setup_edit_tenants
    auto_id_a = ctx["auto_draft_a"].id
    ig_b_id = ctx["ig_b"].id

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.put(
            f"/api/automations/{auto_id_a}",
            json={"instagram_account_id": str(ig_b_id)},
            headers=ctx["headers_a"]
        )
        assert res.status_code == 404
        assert "not found or does not belong to this workspace" in res.json()["detail"].lower()

    async with get_db_session() as session:
        stmt = select(Automation).where(Automation.id == auto_id_a)
        db_auto = (await session.execute(stmt)).scalar_one()
        assert db_auto.instagram_account_id == ctx["ig_a"].id


@pytest.mark.asyncio
async def test_edit_automation_valid_account_switch_allowed(setup_edit_tenants):
    """
    Verify Tenant A can switch their automation to another Instagram account belonging to Workspace A.
    """
    ctx = setup_edit_tenants
    auto_id_a = ctx["auto_draft_a"].id
    ig_a2_id = ctx["ig_a2"].id

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.put(
            f"/api/automations/{auto_id_a}",
            json={"instagram_account_id": str(ig_a2_id)},
            headers=ctx["headers_a"]
        )
        assert res.status_code == 200
        assert res.json()["instagram_account_id"] == str(ig_a2_id)

    async with get_db_session() as session:
        stmt = select(Automation).where(Automation.id == auto_id_a)
        db_auto = (await session.execute(stmt)).scalar_one()
        assert db_auto.instagram_account_id == ig_a2_id


@pytest.mark.asyncio
async def test_edit_failure_does_not_create_duplicate(setup_edit_tenants):
    """
    Verify that an invalid update (e.g. invalid triggerMode) fails with 422
    and creates no duplicate records.
    """
    ctx = setup_edit_tenants
    auto_id = ctx["auto_draft_a"].id
    ws_id = ctx["ws_a"].id

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.put(
            f"/api/automations/{auto_id}",
            json={
                "flow_definition": {
                    "version": 2,
                    "triggerMode": "invalid_mode_string",
                    "trigger": {"triggerMode": "invalid_mode_string"}
                }
            },
            headers=ctx["headers_a"]
        )
        assert res.status_code == 422

    async with get_db_session() as session:
        count_stmt = select(func.count(Automation.id)).where(Automation.workspace_id == ws_id)
        total_count = (await session.execute(count_stmt)).scalar()
        assert total_count == 1
