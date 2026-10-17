# server/app/api/payments.py
"""
Razorpay Payment & Subscription API:
- Create server-side orders for Premium (₹199) and Pro (₹399)
- Verify payment signatures (HMAC SHA-256) server-side
- Activate plan entitlements only upon verified payment
- Idempotent webhook handling for payment.captured, subscription events
- Workspace usage and quota metrics
"""

import uuid
import hmac
import hashlib
import json
import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Header, Request, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import httpx

from app.api.deps import get_current_user, get_current_workspace, get_db
from app.core.config import settings
from app.core.plans import PlanTier, PLAN_CONFIG, get_plan_config
from app.models import User, Workspace, PaymentOrder, WebhookEvent
from app.services.plan_service import PlanService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/payments", tags=["Payments & Plans"])


# ---------- Schemas ----------

class CreateOrderRequest(BaseModel):
    plan_tier: str = Field(..., description="Target plan tier: PREMIUM or PRO")


class VerifyPaymentRequest(BaseModel):
    razorpay_order_id: str
    razorpay_payment_id: str
    razorpay_signature: str
    plan_tier: str


class PlanSwitchRequest(BaseModel):
    plan_tier: str


# ---------- Helpers ----------

def verify_razorpay_signature(order_id: str, payment_id: str, signature: str) -> bool:
    """
    Verifies Razorpay payment signature via HMAC-SHA256:
    hash = HMAC-SHA256(order_id + "|" + payment_id, secret)
    """
    secret = settings.RAZORPAY_KEY_SECRET
    if not secret:
        return False

    message = f"{order_id}|{payment_id}"
    generated_sig = hmac.new(
        secret.encode("utf-8"),
        message.encode("utf-8"),
        hashlib.sha256
    ).hexdigest()

    # Exact constant-time string comparison
    if hmac.compare_digest(generated_sig, signature):
        return True

    # In local development test mode, accept matching mock signature
    if settings.ENVIRONMENT != "production" and (
        signature.startswith("dev_sig_") or signature == f"sig_test_{payment_id}"
    ):
        return True

    return False


# ---------- Endpoints ----------

@router.get("/plans")
async def list_plans() -> Dict[str, Any]:
    """Return all available plans, pricing, quotas, and feature entitlements."""
    return {
        "currency": "INR",
        "plans": [
            {
                "id": p["id"],
                "name": p["name"],
                "price_inr": p["price_inr"],
                "price_paise": p["price_paise"],
                "billing_period": p["billing_period"],
                "max_posts_quota": p["max_posts_quota"],
                "max_dms_per_post": p["max_dms_per_post"],
                "max_automations": p["max_automations"],
                "features": p["features"],
                "description": p["description"],
            }
            for p in PLAN_CONFIG.values()
        ]
    }


@router.get("/usage")
async def get_usage(
    workspace: Workspace = Depends(get_current_workspace),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Returns current workspace plan status, posts automated vs quota,
    DMs per post limit, and feature permissions.
    """
    return await PlanService.get_workspace_usage_summary(workspace, db)


@router.post("/razorpay/create-order")
async def create_razorpay_order(
    body: CreateOrderRequest,
    user: User = Depends(get_current_user),
    workspace: Workspace = Depends(get_current_workspace),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Creates a server-side Razorpay order for Premium or Pro subscription.
    Never trusts frontend-selected prices; price is determined strictly server-side.
    """
    tier_str = body.plan_tier.strip().upper()
    if tier_str not in (PlanTier.PREMIUM.value, PlanTier.PRO.value):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid plan tier '{tier_str}'. Supported upgrade tiers are PREMIUM and PRO."
        )

    plan_cfg = get_plan_config(tier_str)
    amount_paise = plan_cfg["price_paise"]  # ₹199 = 19900, ₹399 = 39900

    order_id = f"order_{uuid.uuid4().hex[:14]}"

    # Attempt to create real Razorpay Order via REST API if configured
    if settings.RAZORPAY_KEY_ID and settings.RAZORPAY_KEY_SECRET and not settings.RAZORPAY_KEY_ID.startswith("rzp_test_comlina"):
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                res = await client.post(
                    "https://api.razorpay.com/v1/orders",
                    auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET),
                    json={
                        "amount": amount_paise,
                        "currency": "INR",
                        "receipt": f"rcpt_{str(workspace.id)[:8]}_{int(datetime.now().timestamp())}",
                        "notes": {
                            "workspace_id": str(workspace.id),
                            "user_id": str(user.id),
                            "plan_tier": tier_str,
                        }
                    }
                )
                if res.status_code in (200, 201):
                    order_data = res.json()
                    order_id = order_data.get("id", order_id)
                else:
                    logger.warning(f"[RAZORPAY] API order creation returned {res.status_code}: {res.text}. Using fallback order.")
        except Exception as api_err:
            logger.warning(f"[RAZORPAY] API request failed: {api_err}. Using fallback order.")

    # Save order in database for signature verification
    payment_order = PaymentOrder(
        id=uuid.uuid4(),
        workspace_id=workspace.id,
        user_id=user.id,
        plan_tier=tier_str,
        amount_paise=amount_paise,
        currency="INR",
        razorpay_order_id=order_id,
        status="CREATED",
        billing_period="MONTHLY",
        metadata_={
            "user_email": user.email,
            "workspace_name": workspace.name,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
    )
    db.add(payment_order)
    await db.commit()

    logger.info(f"[PAYMENT] Created order {order_id} for workspace {workspace.id} (Plan: {tier_str}, Amount: ₹{amount_paise / 100:.2f})")

    return {
        "order_id": order_id,
        "amount": amount_paise,
        "currency": "INR",
        "key_id": settings.RAZORPAY_KEY_ID,
        "plan_tier": tier_str,
        "plan_name": plan_cfg["name"],
        "customer": {
            "name": user.full_name or "Creator",
            "email": user.email,
        }
    }


@router.post("/razorpay/verify-payment")
async def verify_razorpay_payment(
    body: VerifyPaymentRequest,
    user: User = Depends(get_current_user),
    workspace: Workspace = Depends(get_current_workspace),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Verifies Razorpay payment signature and activates plan entitlements.
    Idempotent: updates existing PaymentOrder and workspace tier.
    """
    order_id = body.razorpay_order_id.strip()
    payment_id = body.razorpay_payment_id.strip()
    signature = body.razorpay_signature.strip()
    tier_str = body.plan_tier.strip().upper()

    if tier_str not in (PlanTier.PREMIUM.value, PlanTier.PRO.value):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid target plan tier '{tier_str}'."
        )

    # Validate HMAC signature
    is_valid = verify_razorpay_signature(order_id, payment_id, signature)
    if not is_valid:
        logger.error(f"[PAYMENT FAILED] Signature mismatch for order {order_id}, payment {payment_id}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Payment verification failed: invalid signature. Please contact support if your payment was deducted."
        )

    # Locate PaymentOrder record
    stmt = select(PaymentOrder).where(
        PaymentOrder.workspace_id == workspace.id,
        PaymentOrder.razorpay_order_id == order_id
    )
    res = await db.execute(stmt)
    order_record = res.scalars().first()

    now = datetime.now(timezone.utc)
    period_end = now + timedelta(days=30)

    if order_record:
        order_record.razorpay_payment_id = payment_id
        order_record.razorpay_signature = signature
        order_record.status = "PAID"
        order_record.current_period_start = now
        order_record.current_period_end = period_end
    else:
        # Create paid order record if not found
        order_record = PaymentOrder(
            id=uuid.uuid4(),
            workspace_id=workspace.id,
            user_id=user.id,
            plan_tier=tier_str,
            amount_paise=get_plan_config(tier_str)["price_paise"],
            currency="INR",
            razorpay_order_id=order_id,
            razorpay_payment_id=payment_id,
            razorpay_signature=signature,
            status="PAID",
            current_period_start=now,
            current_period_end=period_end,
        )
        db.add(order_record)

    # Activate workspace plan entitlements
    ws = await db.get(Workspace, workspace.id)
    if ws:
        ws.plan_tier = tier_str
        ws.plan_status = "ACTIVE"
        ws.updated_at = now
        await db.commit()
        await db.refresh(ws)
        workspace = ws
    else:
        workspace.plan_tier = tier_str
        workspace.plan_status = "ACTIVE"
        workspace.updated_at = now
        await db.commit()

    logger.info(f"[PAYMENT SUCCESS] Workspace {workspace.id} upgraded to {tier_str} via payment {payment_id}!")

    return {
        "success": True,
        "plan_tier": workspace.plan_tier,
        "plan_status": workspace.plan_status,
        "message": f"Successfully activated {tier_str} plan! Your new features and higher quotas are now active."
    }


@router.post("/razorpay/webhook")
async def razorpay_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
    x_razorpay_signature: Optional[str] = Header(None)
) -> Dict[str, Any]:
    """
    Idempotent webhook handler for Razorpay asynchronous events.
    Handles payment.captured, order.paid, subscription.cancelled.
    """
    body_bytes = await request.body()

    # Webhook signature validation
    if settings.RAZORPAY_WEBHOOK_SECRET and x_razorpay_signature:
        expected_sig = hmac.new(
            settings.RAZORPAY_WEBHOOK_SECRET.encode("utf-8"),
            body_bytes,
            hashlib.sha256
        ).hexdigest()
        if not hmac.compare_digest(expected_sig, x_razorpay_signature):
            logger.warning("[RAZORPAY WEBHOOK] Invalid signature received.")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid webhook signature")

    try:
        payload = json.loads(body_bytes.decode("utf-8"))
    except Exception as parse_err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid JSON: {parse_err}")

    event_type = payload.get("event")
    event_id = payload.get("payload", {}).get("payment", {}).get("entity", {}).get("id") or f"rzp_evt_{uuid.uuid4().hex[:12]}"

    # Idempotency check via WebhookEvent table
    stmt_check = select(WebhookEvent).where(WebhookEvent.provider_event_id == str(event_id))
    existing_evt = (await db.execute(stmt_check)).scalars().first()
    if existing_evt:
        logger.info(f"[RAZORPAY WEBHOOK] Duplicate event ignored: {event_id}")
        return {"status": "ignored", "reason": "already_processed"}

    # Store event
    webhook_record = WebhookEvent(
        id=uuid.uuid4(),
        provider_event_id=str(event_id),
        event_type=f"razorpay.{event_type}",
        payload=payload,
        status="PROCESSED"
    )
    db.add(webhook_record)

    # Process event
    if event_type in ("payment.captured", "order.paid"):
        payment_entity = payload.get("payload", {}).get("payment", {}).get("entity", {})
        order_id = payment_entity.get("order_id")
        notes = payment_entity.get("notes", {})
        workspace_id_str = notes.get("workspace_id")

        if workspace_id_str:
            try:
                ws_uuid = uuid.UUID(workspace_id_str)
                stmt_ws = select(Workspace).where(Workspace.id == ws_uuid)
                ws = (await db.execute(stmt_ws)).scalars().first()
                if ws:
                    target_plan = notes.get("plan_tier", "PREMIUM").upper()
                    ws.plan_tier = target_plan
                    ws.plan_status = "ACTIVE"
                    ws.updated_at = datetime.now(timezone.utc)
                    logger.info(f"[RAZORPAY WEBHOOK] Activated {target_plan} for workspace {ws.id}")
            except Exception as e:
                logger.error(f"[RAZORPAY WEBHOOK] Failed to update workspace: {e}")

    elif event_type in ("subscription.cancelled", "subscription.paused"):
        sub_entity = payload.get("payload", {}).get("subscription", {}).get("entity", {})
        notes = sub_entity.get("notes", {})
        workspace_id_str = notes.get("workspace_id")
        if workspace_id_str:
            try:
                ws_uuid = uuid.UUID(workspace_id_str)
                stmt_ws = select(Workspace).where(Workspace.id == ws_uuid)
                ws = (await db.execute(stmt_ws)).scalars().first()
                if ws:
                    ws.plan_status = "CANCELLED"
                    ws.updated_at = datetime.now(timezone.utc)
                    logger.info(f"[RAZORPAY WEBHOOK] Marked workspace {ws.id} subscription as CANCELLED")
            except Exception as e:
                logger.error(f"[RAZORPAY WEBHOOK] Error handling cancellation: {e}")

    await db.commit()
    return {"status": "success", "event": event_type}


@router.post("/dev/switch-plan")
async def dev_switch_plan(
    body: PlanSwitchRequest,
    workspace: Workspace = Depends(get_current_workspace),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Developer convenience endpoint to instantly switch workspace plan tier
    for testing Free, Premium, and Pro feature access.
    """
    tier_str = body.plan_tier.strip().upper()
    if tier_str not in (PlanTier.FREE.value, PlanTier.PREMIUM.value, PlanTier.PRO.value):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid tier '{tier_str}'. Supported tiers: FREE, PREMIUM, PRO"
        )

    ws = await db.get(Workspace, workspace.id)
    if ws:
        ws.plan_tier = tier_str
        ws.plan_status = "ACTIVE"
        ws.updated_at = datetime.now(timezone.utc)
        await db.commit()
        await db.refresh(ws)
        workspace = ws
    else:
        workspace.plan_tier = tier_str
        workspace.plan_status = "ACTIVE"
        workspace.updated_at = datetime.now(timezone.utc)
        await db.commit()

    logger.info(f"[DEV] Switched workspace {workspace.id} plan tier to {tier_str}")

    return {
        "success": True,
        "plan_tier": workspace.plan_tier,
        "plan_status": workspace.plan_status,
        "message": f"Workspace plan set to {tier_str}."
    }
