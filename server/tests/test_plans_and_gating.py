# server/tests/test_plans_and_gating.py
import hmac
import hashlib
import json
import uuid
import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch
from sqlalchemy import select

from app.main import app
from app.core.database import get_db_session, init_db
from app.core.plans import (
    PlanTier,
    PLAN_CONFIG,
    has_feature,
    get_required_plan_for_feature,
    FEATURE_ASK_TO_FOLLOW,
    FEATURE_COMMENT_TEASER_REPLY,
    FEATURE_FOLLOW_UP_DMS,
    FEATURE_LIVE_COMMENT,
    FEATURE_AI_SMART_ASSISTANT,
    FEATURE_APPOINTMENT_BOOKING,
    FEATURE_DM_BUTTONS,
    FEATURE_REPLY_TO_ALL,
)
from app.models import Workspace, User, InstagramAccount, PostUsage, PaymentOrder, WebhookEvent
from app.services.plan_service import PlanService
from app.core.config import settings
from app.api.deps import get_current_user, get_current_workspace
from fastapi.testclient import TestClient


# ==========================================
# 1. PLAN CONFIGURATION TESTS
# ==========================================

def test_centralized_plan_config():
    """Verify numeric quotas and tiers match specifications."""
    free = PLAN_CONFIG[PlanTier.FREE]
    premium = PLAN_CONFIG[PlanTier.PREMIUM]
    pro = PLAN_CONFIG[PlanTier.PRO]

    # Free quotas
    assert free["max_posts_quota"] == 10
    assert free["max_dms_per_post"] == 99
    assert free["price_inr"] == 0
    assert free["price_paise"] == 0

    # Premium quotas
    assert premium["price_inr"] == 199
    assert premium["price_paise"] == 19900
    assert premium["max_posts_quota"] == 100
    assert premium["max_dms_per_post"] == 2500

    # Pro quotas
    assert pro["price_inr"] == 399
    assert pro["price_paise"] == 39900
    assert pro["max_posts_quota"] == -1  # Unlimited
    assert pro["max_dms_per_post"] == 10000

    # Feature matrix checks
    assert not has_feature(PlanTier.FREE, FEATURE_ASK_TO_FOLLOW)
    assert not has_feature(PlanTier.FREE, FEATURE_COMMENT_TEASER_REPLY)
    assert not has_feature(PlanTier.FREE, FEATURE_FOLLOW_UP_DMS)
    assert not has_feature(PlanTier.FREE, FEATURE_LIVE_COMMENT)
    assert not has_feature(PlanTier.FREE, FEATURE_AI_SMART_ASSISTANT)
    assert not has_feature(PlanTier.FREE, FEATURE_APPOINTMENT_BOOKING)

    assert has_feature(PlanTier.PREMIUM, FEATURE_ASK_TO_FOLLOW)
    assert has_feature(PlanTier.PREMIUM, FEATURE_COMMENT_TEASER_REPLY)
    assert has_feature(PlanTier.PREMIUM, FEATURE_FOLLOW_UP_DMS)
    assert not has_feature(PlanTier.PREMIUM, FEATURE_LIVE_COMMENT)
    assert not has_feature(PlanTier.PREMIUM, FEATURE_AI_SMART_ASSISTANT)

    assert has_feature(PlanTier.PRO, FEATURE_LIVE_COMMENT)
    assert has_feature(PlanTier.PRO, FEATURE_AI_SMART_ASSISTANT)
    assert has_feature(PlanTier.PRO, FEATURE_APPOINTMENT_BOOKING)


# ==========================================
# 2. FEATURE GATING SERVICE TESTS
# ==========================================

def test_validate_automation_features_free_tier():
    """Ensure Free tier strictly rejects paid features and excess keywords."""
    ws = Workspace(
        id=uuid.uuid4(),
        name="Free Workspace",
        plan_tier=PlanTier.FREE.value,
    )

    # Basic free config should succeed
    basic_free = {
        "trigger_type": "KEYWORDS",
        "keywords": ["info", "price", "link"],  # 3 keywords allowed
        "reply_in_comments": False,
        "actions": [{"type": "PRIVATE_DM", "message": "Here is the link!"}],
    }
    valid, err = PlanService.validate_automation_features(ws, basic_free)
    assert valid is True
    assert err is None

    # Rejection 1: More than 3 keywords on Free
    valid, err = PlanService.validate_automation_features(ws, {
        **basic_free,
        "keywords": ["a", "b", "c", "d"],
    })
    assert valid is False
    assert err is not None
    assert "up to 3 trigger keywords" in err

    # Rejection 2: Ask to follow (Premium feature)
    valid, err = PlanService.validate_automation_features(ws, {
        **basic_free,
        "askFollowEnabled": True,
    })
    assert valid is False
    assert err is not None
    assert "Ask to Follow requires a Premium" in err

    # Rejection 3: Comment teaser reply (Premium feature)
    valid, err = PlanService.validate_automation_features(ws, {
        **basic_free,
        "teaserEnabled": True,
    })
    assert valid is False
    assert err is not None
    assert "Comment Teaser Reply requires a Premium" in err

    # Rejection 4: Buttons (Premium feature)
    valid, err = PlanService.validate_automation_features(ws, {
        **basic_free,
        "buttons": [{"label": "Buy", "url": "https://comlina.com"}],
    })
    assert valid is False
    assert err is not None
    assert "Interactive DM Buttons require a Premium" in err

    # Rejection 5: Follow up DMs (Premium feature)
    valid, err = PlanService.validate_automation_features(ws, {
        **basic_free,
        "followUpEnabled": True,
    })
    assert valid is False
    assert err is not None
    assert "Follow-up DMs require a Premium" in err

    # Rejection 6: Live comment (Pro feature)
    valid, err = PlanService.validate_automation_features(ws, {
        **basic_free,
        "liveCommentEnabled": True,
    })
    assert valid is False
    assert err is not None
    assert "Live Comment Automation is exclusive to the Pro plan" in err

    # Rejection 7: AI smart assistant (Pro feature)
    valid, err = PlanService.validate_automation_features(ws, {
        **basic_free,
        "aiSmartAssistantEnabled": True,
    })
    assert valid is False
    assert err is not None
    assert "AI Smart Assistant is exclusive to the Pro plan" in err

    # Rejection 8: Create Lead Flow (Pro feature)
    valid, err = PlanService.validate_automation_features(ws, {
        **basic_free,
        "type": "COMMENT_TO_LEAD",
    })
    assert valid is False
    assert err is not None
    assert "Create Lead Flow requires a Pro plan" in err

    # Rejection 9: DM Reply (Pro feature)
    valid, err = PlanService.validate_automation_features(ws, {
        **basic_free,
        "type": "DM_REPLY",
    })
    assert valid is False
    assert err is not None
    assert "DM Reply Flow requires a Pro plan" in err

    # Rejection 10: DM to Lead Collection (Pro feature)
    valid, err = PlanService.validate_automation_features(ws, {
        **basic_free,
        "type": "DM_TO_LEAD",
    })
    assert valid is False
    assert err is not None
    assert "DM to Lead Collection requires a Pro plan" in err


def test_validate_automation_features_premium_and_pro():
    """Ensure Premium accepts its features but rejects Pro features; Pro accepts all."""
    premium_ws = Workspace(
        id=uuid.uuid4(),
        name="Premium Workspace",
        plan_tier=PlanTier.PREMIUM.value,
    )

    premium_config = {
        "trigger_type": "KEYWORDS",
        "keywords": ["a", "b", "c", "d", "e"],  # Unlimited keywords
        "askFollowEnabled": True,
        "teaserEnabled": True,
        "replyToAll": True,
        "buttons": [{"label": "Shop", "url": "https://comlina.com"}],
        "followUpEnabled": True,
    }
    # Succeeds on Premium
    valid, err = PlanService.validate_automation_features(premium_ws, premium_config)
    assert valid is True
    assert err is None

    # Pro features fail on Premium
    valid, err = PlanService.validate_automation_features(premium_ws, {
        **premium_config,
        "type": "COMMENT_TO_LEAD",
    })
    assert valid is False
    assert "Create Lead Flow requires a Pro plan" in err

    valid, err = PlanService.validate_automation_features(premium_ws, {
        **premium_config,
        "type": "DM_REPLY",
    })
    assert valid is False
    assert "DM Reply Flow requires a Pro plan" in err

    valid, err = PlanService.validate_automation_features(premium_ws, {
        **premium_config,
        "type": "DM_TO_LEAD",
    })
    assert valid is False
    assert "DM to Lead Collection requires a Pro plan" in err

    # Everything succeeds on Pro
    pro_ws = Workspace(
        id=uuid.uuid4(),
        name="Pro Workspace",
        plan_tier=PlanTier.PRO.value,
    )
    pro_config = {
        **premium_config,
        "liveCommentEnabled": True,
        "aiSmartAssistantEnabled": True,
        "appointmentBookingEnabled": True,
        "type": "COMMENT_TO_LEAD",
    }
    valid, err = PlanService.validate_automation_features(pro_ws, pro_config)
    assert valid is True
    assert err is None


# ==========================================
# 3. USAGE LIMITS & SERVER-SIDE TRACKING TESTS
# ==========================================

@pytest.mark.asyncio
async def test_post_quota_enforcement():
    """Test 10-post lifetime limit on Free tier and no duplicate count on re-configuration."""
    await init_db()
    async with get_db_session() as session:
        ws_id = uuid.uuid4()
        workspace = Workspace(
            id=ws_id,
            name="Quota Test Workspace",
            slug=f"ws-{ws_id.hex[:8]}",
            plan_tier=PlanTier.FREE.value,
            plan_status="ACTIVE",
        )
        session.add(workspace)
        await session.commit()

        # Seed 10 posts
        for i in range(10):
            allowed, err = await PlanService.check_and_register_post_quota(
                workspace, f"post_{i}", session
            )
            assert allowed is True
            assert err is None
        await session.commit()

        # Re-registering an already automated post must succeed without consuming new quota
        allowed, err = await PlanService.check_and_register_post_quota(
            workspace, "post_0", session
        )
        assert allowed is True
        assert err is None

        # 11th post must be blocked on Free tier
        allowed, err = await PlanService.check_and_register_post_quota(
            workspace, "post_11_fail", session
        )
        assert allowed is False
        assert err is not None
        assert "limit of 10 automated posts" in err

        # Switching to Premium allows creating the 11th post
        workspace.plan_tier = PlanTier.PREMIUM.value
        await session.commit()

        allowed, err = await PlanService.check_and_register_post_quota(
            workspace, "post_11_fail", session
        )
        assert allowed is True
        assert err is None


@pytest.mark.asyncio
async def test_dm_quota_per_post_and_delivery_recording():
    """Test 99 DM limit per post on Free tier and verified increment only."""
    await init_db()
    async with get_db_session() as session:
        ws_id = uuid.uuid4()
        workspace = Workspace(
            id=ws_id,
            name="DM Test Workspace",
            slug=f"ws-{ws_id.hex[:8]}",
            plan_tier=PlanTier.FREE.value,
        )
        session.add(workspace)
        await session.commit()

        # Register post
        await PlanService.check_and_register_post_quota(workspace, "post_dm_99", session)
        await session.commit()

        # Fast-forward delivered DMs to 98
        stmt = select(PostUsage).where(
            PostUsage.workspace_id == ws_id,
            PostUsage.media_id == "post_dm_99"
        )
        res = await session.execute(stmt)
        usage = res.scalars().first()
        assert usage is not None
        usage.dms_delivered_count = 98
        await session.commit()

        # 99th DM check should pass (allowed: True)
        allowed, err = await PlanService.check_dm_quota_for_post(
            workspace, "post_dm_99", session
        )
        assert allowed is True
        assert err is None

        # Deliver 99th DM
        await PlanService.record_dm_delivered(ws_id, "post_dm_99", session)

        # Refresh usage
        res = await session.execute(stmt)
        usage = res.scalars().first()
        assert usage is not None
        assert usage.dms_delivered_count == 99

        # 100th DM check should fail on Free tier
        allowed, err = await PlanService.check_dm_quota_for_post(
            workspace, "post_dm_99", session
        )
        assert allowed is False
        assert err is not None
        assert "Free plan allows 99 DMs per post" in err


# ==========================================
# 4. RAZORPAY INTEGRATION & SIGNATURE TESTS
# ==========================================

@pytest.mark.asyncio
async def test_razorpay_order_and_signature_verification():
    """Verify server-side price enforcement and signature verification."""
    await init_db()
    async with get_db_session() as session:
        ws_id = uuid.uuid4()
        workspace = Workspace(
            id=ws_id,
            name="Razorpay Test Workspace",
            slug=f"ws-{ws_id.hex[:8]}",
            plan_tier=PlanTier.FREE.value,
        )
        test_user = User(
            id=uuid.uuid4(),
            email=f"test_creator_{uuid.uuid4().hex[:8]}@example.com",
            full_name="Creator Test",
        )
        session.add(workspace)
        session.add(test_user)
        await session.commit()

        # Set up FastAPI dependency overrides
        app.dependency_overrides[get_current_user] = lambda: test_user
        app.dependency_overrides[get_current_workspace] = lambda: workspace

        try:
            client = TestClient(app)

            # 1. Create Order for Premium
            res = client.post("/api/payments/razorpay/create-order", json={
                "plan_tier": "PREMIUM",
            })
            assert res.status_code == 200
            data = res.json()
            assert data["amount"] == 19900  # ₹199 in paise (server-enforced)
            assert data["currency"] == "INR"
            order_id = data["order_id"]

            # Verify PaymentOrder row was created in database
            stmt = select(PaymentOrder).where(PaymentOrder.razorpay_order_id == order_id)
            order_row = (await session.execute(stmt)).scalars().first()
            assert order_row is not None
            assert order_row.amount_paise == 19900
            assert order_row.plan_tier == "PREMIUM"

            # 2. Tampered signature must fail verification
            bad_res = client.post("/api/payments/razorpay/verify-payment", json={
                "razorpay_order_id": order_id,
                "razorpay_payment_id": "pay_test_123",
                "razorpay_signature": "forged_signature_xyz",
                "plan_tier": "PREMIUM",
            })
            assert bad_res.status_code == 400
            assert "Invalid payment signature" in bad_res.json()["detail"] or "verification failed" in bad_res.json()["detail"]

            # 3. Valid HMAC-SHA256 signature must succeed and upgrade workspace
            raw_msg = f"{order_id}|pay_test_123"
            valid_sig = hmac.new(
                settings.RAZORPAY_KEY_SECRET.encode("utf-8"),
                raw_msg.encode("utf-8"),
                hashlib.sha256
            ).hexdigest()

            good_res = client.post("/api/payments/razorpay/verify-payment", json={
                "razorpay_order_id": order_id,
                "razorpay_payment_id": "pay_test_123",
                "razorpay_signature": valid_sig,
                "plan_tier": "PREMIUM",
            })
            assert good_res.status_code == 200
            body = good_res.json()
            assert body["success"] is True
            assert body["plan_tier"] == "PREMIUM"

            # Check DB workspace upgraded
            await session.refresh(workspace)
            assert workspace.plan_tier == "PREMIUM"
            assert workspace.plan_status == "ACTIVE"

        finally:
            app.dependency_overrides.clear()


# ==========================================
# 5. IDEMPOTENT WEBHOOK HANDLING TESTS
# ==========================================

@pytest.mark.asyncio
async def test_razorpay_webhook_idempotency():
    """Ensure webhook updates subscription idempotently and ignores duplicate events.
    Enforces F2 security: plan comes strictly from stored PaymentOrder, never from notes.
    """
    await init_db()
    async with get_db_session() as session:
        ws_id = uuid.uuid4()
        workspace = Workspace(
            id=ws_id,
            name="Webhook Test Workspace",
            slug=f"ws-{ws_id.hex[:8]}",
            plan_tier=PlanTier.PREMIUM.value,
        )
        session.add(workspace)

        # Seed matching order to verify plan tier extraction from DB, not payload notes
        order_id = f"order_{uuid.uuid4().hex[:10]}"
        payment_order = PaymentOrder(
            id=uuid.uuid4(),
            workspace_id=ws_id,
            plan_tier="PRO",
            amount_paise=39900,
            currency="INR",
            razorpay_order_id=order_id,
            status="CREATED"
        )
        session.add(payment_order)
        await session.commit()

        client = TestClient(app)

        event_id = f"evt_test_{uuid.uuid4().hex[:12]}"
        webhook_payload = {
            "entity": "event",
            "account_id": "acc_123",
            "event": "payment.captured",
            "contains": ["payment"],
            "payload": {
                "payment": {
                    "entity": {
                        "id": event_id,
                        "order_id": order_id,
                        "notes": {
                            "workspace_id": str(ws_id),
                            "plan_tier": "ENTERPRISE"  # Malicious attempt in notes: must be IGNORED in favor of DB order
                        }
                    }
                }
            }
        }
        body_bytes = json.dumps(webhook_payload).encode("utf-8")
        sig = hmac.new(
            settings.RAZORPAY_WEBHOOK_SECRET.encode("utf-8"),
            body_bytes,
            hashlib.sha256
        ).hexdigest()

        # Negative 1: Unsigned webhook must return 400
        res_unsigned = client.post(
            "/api/payments/razorpay/webhook",
            content=body_bytes,
            headers={
                "x-razorpay-event-id": event_id,
                "content-type": "application/json"
            }
        )
        assert res_unsigned.status_code == 400
        assert "signature" in res_unsigned.json().get("detail", "").lower()

        # Negative 2: Signed webhook with no matching order in DB -> no upgrade
        bad_order_payload = {
            "entity": "event",
            "account_id": "acc_123",
            "event": "payment.captured",
            "contains": ["payment"],
            "payload": {
                "payment": {
                    "entity": {
                        "id": f"evt_bad_{uuid.uuid4().hex[:8]}",
                        "order_id": "order_nonexistent_999",
                        "notes": {
                            "workspace_id": str(ws_id),
                            "plan_tier": "ENTERPRISE"
                        }
                    }
                }
            }
        }
        bad_order_bytes = json.dumps(bad_order_payload).encode("utf-8")
        bad_order_sig = hmac.new(
            settings.RAZORPAY_WEBHOOK_SECRET.encode("utf-8"),
            bad_order_bytes,
            hashlib.sha256
        ).hexdigest()
        res_no_order = client.post(
            "/api/payments/razorpay/webhook",
            content=bad_order_bytes,
            headers={
                "x-razorpay-signature": bad_order_sig,
                "content-type": "application/json"
            }
        )
        assert res_no_order.status_code == 200
        await session.refresh(workspace)
        assert workspace.plan_tier == PlanTier.PREMIUM.value  # NOT upgraded to ENTERPRISE!

        # Positive: Signed webhook delivery with valid order: upgrades workspace to PRO (from DB order, NOT ENTERPRISE from notes)
        res1 = client.post(
            "/api/payments/razorpay/webhook",
            content=body_bytes,
            headers={
                "x-razorpay-signature": sig,
                "x-razorpay-event-id": event_id,
                "content-type": "application/json"
            }
        )
        assert res1.status_code == 200
        assert res1.json()["status"] == "success"

        await session.refresh(workspace)
        assert workspace.plan_tier == "PRO"

        # Second delivery of same webhook event: must return already_processed idempotently
        res2 = client.post(
            "/api/payments/razorpay/webhook",
            content=body_bytes,
            headers={
                "x-razorpay-signature": sig,
                "x-razorpay-event-id": event_id,
                "content-type": "application/json"
            }
        )
        assert res2.status_code == 200
        assert res2.json()["reason"] == "already_processed"

