import json
import logging
import base64
import hashlib
import secrets
import hmac
import time
import uuid
from typing import Optional
from fastapi import APIRouter, Request, Response, HTTPException, status, Query, Depends, Form
from app.core.replay_cache import replay_cache
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert

async def _insert_webhook_event_idempotent(
    db: AsyncSession,
    workspace_id,
    instagram_account_id,
    provider_id: str,
    event_type: str,
    payload: dict
) -> Optional[uuid.UUID]:
    dialect_name = getattr(getattr(db, "bind", None), "dialect", None)
    dialect = dialect_name.name if dialect_name else "postgresql"

    if dialect == "postgresql":
        stmt = (
            pg_insert(WebhookEvent)
            .values(
                workspace_id=workspace_id,
                instagram_account_id=instagram_account_id,
                provider_event_id=provider_id,
                event_type=event_type,
                payload=payload,
                status="PENDING",
            )
            .on_conflict_do_nothing(index_elements=["provider_event_id"])
            .returning(WebhookEvent.id)
        )
        res = await db.execute(stmt)
        row = res.fetchone()
        return row[0] if row else None
    else:
        stmt_check = select(WebhookEvent.id).where(WebhookEvent.provider_event_id == provider_id)
        existing = (await db.execute(stmt_check)).scalar_one_or_none()
        if existing:
            return None
        stmt = (
            sqlite_insert(WebhookEvent)
            .values(
                workspace_id=workspace_id,
                instagram_account_id=instagram_account_id,
                provider_event_id=provider_id,
                event_type=event_type,
                payload=payload,
                status="PENDING",
            )
            .on_conflict_do_nothing(index_elements=["provider_event_id"])
        )
        await db.execute(stmt)
        stmt_fetch = select(WebhookEvent.id).where(WebhookEvent.provider_event_id == provider_id)
        return (await db.execute(stmt_fetch)).scalar_one_or_none()
from arq import create_pool
from arq.connections import RedisSettings
from app.core.config import settings
from app.core.database import get_db
from app.core.security import verify_meta_webhook_signature
from app.core.logging import log_diagnostic_event
from app.integrations.instagram.webhooks import InstagramWebhookParser
from app.models import (WebhookEvent, InstagramAccount, Automation, AutomationVersion, Contact,
                        Conversation, Message, AnalyticsEvent)
from app.core.encryption import encrypt_token

logger = logging.getLogger("webhooks")
router = APIRouter(prefix="/webhooks/instagram", tags=["Webhooks"])

@router.get("")
async def verify_webhook_subscription(
    hub_mode: Optional[str] = Query(None, alias="hub.mode", max_length=32),
    hub_challenge: Optional[str] = Query(None, alias="hub.challenge", max_length=256),
    hub_verify_token: Optional[str] = Query(None, alias="hub.verify_token", max_length=256)
):
    """
    Meta Graph API Webhook Verification Challenge.
    Returns hub.challenge if hub.verify_token matches configured secret.
    """
    configured_token = settings.META_WEBHOOK_VERIFY_TOKEN
    if (
        hub_mode == "subscribe"
        and configured_token
        and hub_verify_token
        and hmac.compare_digest(hub_verify_token, configured_token)
    ):
        logger.info("Meta webhook verification challenge passed.")
        return Response(content=hub_challenge or "", media_type="text/plain")

    logger.warning("Meta webhook verification failed: Invalid verify token or unconfigured secret.")
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Verification token mismatch")

from pydantic import BaseModel
from fastapi import APIRouter, Request, Response, HTTPException, status, Query, Depends, Form, BackgroundTasks

async def execute_webhook_event_inprocess(event_id: str, event_data: dict) -> dict:
    """
    Executes a webhook event in-process when Redis / ARQ worker is not running.
    Dispatches to process_comment_job or send_dm_job.
    """
    event_type = event_data.get("event_type", "COMMENT")
    logger.info(f"[IN-PROCESS] Executing webhook event {event_id} ({event_type}) in-process...")
    if event_type == "COMMENT":
        from app.jobs.process_comment import process_comment_job
        return await process_comment_job({}, event_id, event_data)
    elif event_type in ("MESSAGING", "DM"):
        from app.jobs.send_dm import send_dm_job
        return await send_dm_job({}, event_id, event_data)
    return {"status": "UNHANDLED_EVENT_TYPE", "type": event_type}

class SimulateCommentRequest(BaseModel):
    text: str
    sender_username: str = "test_user"
    sender_id: str = "test_sender_123"
    post_id: Optional[str] = None
    comment_id: Optional[str] = None
    business_ig_id: Optional[str] = None
    account_id: Optional[str] = None

@router.post("/simulate-comment")
async def simulate_comment(
    req: SimulateCommentRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Simulator endpoint to verify Comment -> Keyword Check -> DM -> Contact/Inbox/Analytics loop in one call.
    Disabled in production and requires ENABLE_DEV_ROUTES in development.
    """
    if settings.ENVIRONMENT == "production" or not settings.ENABLE_DEV_ROUTES:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Simulation endpoint is disabled in production and requires ENABLE_DEV_ROUTES."
        )

    account = None
    if req.account_id:
        try:
            stmt_acc = select(InstagramAccount).where(
                InstagramAccount.id == uuid.UUID(req.account_id),
                InstagramAccount.is_active == True
            )
            account = (await db.execute(stmt_acc)).scalar_one_or_none()
        except ValueError:
            pass

    if not account and req.business_ig_id:
        stmt_acc = select(InstagramAccount).where(
            InstagramAccount.ig_user_id == req.business_ig_id,
            InstagramAccount.is_active == True
        )
        account = (await db.execute(stmt_acc)).scalar_one_or_none()

    if not account:
        stmt_acc = select(InstagramAccount).where(InstagramAccount.is_active == True).limit(1)
        account = (await db.execute(stmt_acc)).scalars().first()

    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No connected Instagram account found in database to simulate comment against."
        )

    provider_id = f"sim_{uuid.uuid4().hex[:12]}"
    comment_id = req.comment_id or f"sim_comm_{uuid.uuid4().hex[:8]}"
    post_id = req.post_id or "sim_post_001"

    evt = {
        "provider_event_id": provider_id,
        "event_type": "COMMENT",
        "business_ig_id": account.ig_user_id,
        "sender_id": req.sender_id,
        "sender_username": req.sender_username,
        "text": req.text,
        "post_id": post_id,
        "comment_id": comment_id,
        "workspace_id": str(account.workspace_id),
        "instagram_account_id": str(account.id),
    }

    inserted_id = await _insert_webhook_event_idempotent(
        db, account.workspace_id, account.id, provider_id, "COMMENT", evt
    )
    await db.commit()

    # Execute immediately in-process so caller receives real-time execution results
    exec_res = await execute_webhook_event_inprocess(str(inserted_id), evt)

    return {
        "status": "SIMULATION_SUCCESS",
        "provider_event_id": provider_id,
        "event_id": str(inserted_id),
        "account_id": str(account.id),
        "account_username": account.username,
        "execution_result": exec_res
    }

@router.post("")
async def receive_meta_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """
    Durable & Idempotent Meta Webhook Ingestion Pipeline:
    1. Verify HMAC SHA-256 signature (X-Hub-Signature-256).
    2. Validate payload structure.
    3. Persist to DB table 'webhook_events' with UNIQUE(provider_event_id).
    4. Fast idempotency check: If already exists in DB, skip duplicate.
    5. Enqueue background processing job into Redis via ARQ or execute in-process.
    6. Return HTTP 200 OK (< 100ms) to Meta.
    """
    corr_id = request.headers.get("x-request-id") or str(uuid.uuid4())
    signature_header = request.headers.get("X-Hub-Signature-256")
    body_bytes = await request.body()

    # 1. HMAC Verification (Strictly enforced in all environments)
    if not signature_header or not verify_meta_webhook_signature(body_bytes, signature_header):
        log_diagnostic_event(
            stage="webhook_received",
            correlation_id=corr_id,
            http_status=status.HTTP_403_FORBIDDEN,
            error_code="SIGNATURE_MISMATCH",
            details={"reason": "HMAC signature verification failed"}
        )
        logger.error("HMAC signature verification failed for incoming webhook.")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid signature")

    log_diagnostic_event(
        stage="webhook_received",
        correlation_id=corr_id,
        http_status=status.HTTP_200_OK,
        details={"bytes": len(body_bytes)}
    )

    try:
        payload = json.loads(body_bytes.decode("utf-8"))
    except Exception as e:
        logger.error(f"Failed to parse webhook JSON payload: {e}")
        return Response(content="INVALID_JSON", status_code=status.HTTP_200_OK)

    # 2. Extract normalized events
    events = InstagramWebhookParser.extract_events(payload)
    if not events:
        return Response(content="NO_EVENTS_FOUND", status_code=status.HTTP_200_OK)

    # Prepare ARQ Redis Pool
    try:
        redis_pool = await create_pool(RedisSettings.from_dsn(settings.REDIS_URL))
    except Exception as e:
        logger.warning(f"Could not connect to Redis pool in development mode: {e}")
        redis_pool = None

    for evt in events:
        provider_id = evt["provider_event_id"]
        event_type = evt["event_type"]
        business_ig_id = evt.get("business_ig_id")

        log_diagnostic_event(
            stage="event_parsed",
            correlation_id=provider_id,
            event_type=event_type,
            details={
                "provider_event_id": provider_id,
                "media_id": evt.get("post_id"),
                "comment_id": evt.get("comment_id")
            }
        )

        # Resolve workspace and account ID if possible
        workspace_id = None
        instagram_account_id = None
        if business_ig_id:
            stmt_acc = select(InstagramAccount).where(
                InstagramAccount.ig_user_id == business_ig_id,
                InstagramAccount.is_active == True
            )
            res_acc = await db.execute(stmt_acc)
            acc = res_acc.scalar_one_or_none()
            if acc:
                workspace_id = acc.workspace_id
                instagram_account_id = acc.id
                evt["workspace_id"] = str(workspace_id)
                evt["instagram_account_id"] = str(instagram_account_id)
                log_diagnostic_event(
                    stage="account_matched",
                    correlation_id=provider_id,
                    event_type=event_type,
                    workspace_id=str(workspace_id),
                    account_id=str(instagram_account_id),
                    details={"username": acc.username}
                )
            else:
                log_diagnostic_event(
                    stage="account_matched",
                    correlation_id=provider_id,
                    event_type=event_type,
                    error_code="ACCOUNT_NOT_FOUND",
                    details={"business_ig_id": business_ig_id}
                )

        inserted_id = await _insert_webhook_event_idempotent(
            db, workspace_id, instagram_account_id, provider_id, event_type, evt
        )

        if inserted_id:
            # New event -> Queue to ARQ background worker or execute in-process
            await db.commit()
            if redis_pool:
                try:
                    await redis_pool.enqueue_job("process_webhook_event", str(inserted_id), evt)
                    logger.info(f"Queued webhook event {provider_id} to ARQ worker.")
                    log_diagnostic_event(
                        stage="job_enqueued",
                        correlation_id=provider_id,
                        event_type=event_type,
                        workspace_id=str(workspace_id) if workspace_id else None,
                        account_id=str(instagram_account_id) if instagram_account_id else None,
                        details={"queue": "redis_arq", "event_id": str(inserted_id)}
                    )
                except Exception as ex:
                    logger.error(f"Failed to enqueue to Redis ARQ: {ex}")
                    background_tasks.add_task(execute_webhook_event_inprocess, str(inserted_id), evt)
                    log_diagnostic_event(
                        stage="job_enqueued",
                        correlation_id=provider_id,
                        event_type=event_type,
                        workspace_id=str(workspace_id) if workspace_id else None,
                        account_id=str(instagram_account_id) if instagram_account_id else None,
                        error_code="REDIS_ENQUEUE_FALLBACK",
                        details={"queue": "in_process_fallback", "error": str(ex)}
                    )
            else:
                background_tasks.add_task(execute_webhook_event_inprocess, str(inserted_id), evt)
                logger.info(f"Dispatched webhook event {provider_id} in-process via BackgroundTasks.")
                log_diagnostic_event(
                    stage="job_enqueued",
                    correlation_id=provider_id,
                    event_type=event_type,
                    workspace_id=str(workspace_id) if workspace_id else None,
                    account_id=str(instagram_account_id) if instagram_account_id else None,
                    details={"queue": "in_process", "event_id": str(inserted_id)}
                )
        else:
            # Duplicate event -> Already recorded in DB, ignore
            logger.info(f"Duplicate webhook event {provider_id} discarded by DB idempotency check.")

    if redis_pool:
        await redis_pool.close()

    # 4. Immediate 200 OK response
    return {"status": "EVENT_RECEIVED", "count": len(events)}


def _b64url_decode(value: str) -> bytes:
    return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))


def parse_signed_request(
    signed_request: str,
    app_secret: str,
    max_age_seconds: int = 900,
    check_replay: bool = True
) -> dict:
    if not app_secret:
        raise HTTPException(status_code=500, detail="META_APP_SECRET is not configured")
    try:
        sig_b64, payload_b64 = signed_request.split(".", 1)
        signature = _b64url_decode(sig_b64)
        payload = json.loads(_b64url_decode(payload_b64).decode("utf-8"))
    except Exception:
        raise HTTPException(status_code=400, detail="Malformed signed_request")
    if str(payload.get("algorithm", "")).upper() != "HMAC-SHA256":
        raise HTTPException(status_code=400, detail="Unsupported signed_request algorithm")
    expected = hmac.new(app_secret.encode(), payload_b64.encode(), hashlib.sha256).digest()
    if not hmac.compare_digest(signature, expected):
        raise HTTPException(status_code=400, detail="Invalid signed_request signature")
    if not payload.get("user_id"):
        raise HTTPException(status_code=400, detail="signed_request has no user_id")

    # TTL window check on issued_at timestamp
    if "issued_at" in payload:
        try:
            issued_at = int(payload["issued_at"])
            now = int(time.time())
            if now - issued_at > max_age_seconds:
                raise HTTPException(status_code=400, detail="signed_request has expired")
            if issued_at > now + 300:
                raise HTTPException(status_code=400, detail="signed_request timestamp is in the future")
        except (ValueError, TypeError):
            raise HTTPException(status_code=400, detail="Invalid issued_at timestamp in signed_request")

    # Replay protection check
    if check_replay:
        sig_hash = hashlib.sha256(sig_b64.encode("utf-8")).hexdigest()
        if not replay_cache.check_and_record_sync(sig_hash, ttl_seconds=max_age_seconds, namespace="signed_request"):
            raise HTTPException(status_code=400, detail="signed_request has already been processed or replayed")

    return payload


async def verify_and_parse_signed_request(
    signed_request: str,
    app_secret: str,
    max_age_seconds: int = 900
) -> dict:
    """
    Asynchronously parses and verifies signed_request, enforcing signature, TTL window,
    and distributed replay cache prevention using Redis (with in-memory fallback).
    """
    payload = parse_signed_request(
        signed_request,
        app_secret,
        max_age_seconds=max_age_seconds,
        check_replay=False
    )
    try:
        sig_b64 = signed_request.split(".", 1)[0]
        sig_hash = hashlib.sha256(sig_b64.encode("utf-8")).hexdigest()
    except Exception:
        raise HTTPException(status_code=400, detail="Malformed signed_request")

    is_fresh = await replay_cache.check_and_record(
        sig_hash,
        ttl_seconds=max_age_seconds,
        namespace="signed_request"
    )
    if not is_fresh:
        raise HTTPException(status_code=400, detail="signed_request has already been processed or replayed")

    return payload


async def _accounts_for(db: AsyncSession, ig_user_id: str):
    res = await db.execute(select(InstagramAccount).where(InstagramAccount.ig_user_id == str(ig_user_id)))
    return list(res.scalars().all())


@router.post("/deauthorize")
async def deauthorize_callback(signed_request: str = Form(...), db: AsyncSession = Depends(get_db)):
    payload = await verify_and_parse_signed_request(signed_request, settings.META_APP_SECRET)
    for acc in await _accounts_for(db, payload["user_id"]):
        acc.is_active = False
        acc.access_token_encrypted = encrypt_token("REVOKED")
    await db.commit()
    code = secrets.token_urlsafe(16)
    base = settings.META_REDIRECT_URI.split("/connect/")[0].rstrip("/")
    return {"url": f"{base}/data-deletion-status?code={code}", "confirmation_code": code}


@router.post("/data-deletion")
async def data_deletion_callback(signed_request: str = Form(...), db: AsyncSession = Depends(get_db)):
    payload = await verify_and_parse_signed_request(signed_request, settings.META_APP_SECRET)
    for acc in await _accounts_for(db, payload["user_id"]):
        conv_ids = select(Conversation.id).where(Conversation.instagram_account_id == acc.id)
        auto_ids = select(Automation.id).where(Automation.instagram_account_id == acc.id)
        await db.execute(delete(Message).where(Message.conversation_id.in_(conv_ids)))
        await db.execute(delete(Conversation).where(Conversation.instagram_account_id == acc.id))
        await db.execute(delete(AnalyticsEvent).where(AnalyticsEvent.instagram_account_id == acc.id))
        await db.execute(delete(AutomationVersion).where(AutomationVersion.automation_id.in_(auto_ids)))
        await db.execute(delete(Automation).where(Automation.instagram_account_id == acc.id))
        await db.execute(delete(Contact).where(Contact.instagram_account_id == acc.id))
        await db.execute(delete(WebhookEvent).where(WebhookEvent.instagram_account_id == acc.id))
        await db.execute(delete(InstagramAccount).where(InstagramAccount.id == acc.id))
    await db.commit()
    code = secrets.token_urlsafe(16)
    base = settings.META_REDIRECT_URI.split("/connect/")[0].rstrip("/")
    return {"url": f"{base}/data-deletion-status?code={code}", "confirmation_code": code}

