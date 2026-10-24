# worker/app/main.py
import logging
from typing import Dict, Any
from arq.connections import RedisSettings
from arq import cron
from app.core.config import worker_settings
from datetime import datetime, timezone, timedelta
from sqlalchemy import select, update, func
from app.models import WebhookEvent
from app.core.database import engine, SessionLocal, get_db_session
from app.jobs.process_comment import process_comment_job
from app.jobs.send_dm import send_dm_job
from app.jobs.refresh_tokens import refresh_expiring_tokens_job

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("worker")

async def process_webhook_event(ctx: Dict[str, Any], event_id: str, event_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Main job dispatcher receiving webhook events enqueued by FastAPI.
    Routes to process_comment_job or messaging handlers.
    """
    logger.info(f"ARQ Worker picked up job process_webhook_event: event_id={event_id}")
    event_type = event_data.get("event_type", "COMMENT")

    if event_type == "COMMENT":
        return await process_comment_job(ctx, event_id, event_data)
    elif event_type in ("MESSAGING", "DM"):
        return await send_dm_job(ctx, event_id, event_data)

    # F10: Mark unhandled event type as IGNORED so it doesn't remain PENDING indefinitely
    try:
        from app.jobs.process_comment import _update_webhook_event
        async with get_db_session() as session:
            await _update_webhook_event(
                session, event_id, event_data.get("provider_event_id"), "IGNORED", f"Unhandled event type: {event_type}"
            )
    except Exception as ex:
        logger.warning(f"Failed to update WebhookEvent status for unhandled event {event_id}: {ex}")

    return {"status": "IGNORED", "type": event_type}

async def sweep_stuck_events(ctx: Dict[str, Any]) -> int:
    """Re-queues webhook events stuck in PENDING for > 5 mins, capped at 3 attempts."""
    cutoff = datetime.now(timezone.utc) - timedelta(minutes=5)
    requeued_count = 0
    async with SessionLocal() as db:
        # Find stuck events in PENDING older than 5 minutes with attempt_count < 3
        stmt_find = (
            select(WebhookEvent)
            .where(
                WebhookEvent.status == "PENDING",
                WebhookEvent.received_at < cutoff,
                WebhookEvent.attempt_count < 3
            )
        )
        res = await db.execute(stmt_find)
        stuck_events = list(res.scalars().all())

        redis_client = ctx.get("redis") if isinstance(ctx, dict) else None
        for evt in stuck_events:
            evt.attempt_count += 1
            evt.updated_at = datetime.now(timezone.utc)
            requeued_count += 1
            if redis_client:
                event_type = (evt.event_type or "").lower()
                if "comment" in event_type or "feed" in event_type:
                    await redis_client.enqueue_job("process_comment_job", str(evt.id), evt.payload)
                elif "message" in event_type or "messaging" in event_type or "dm" in event_type:
                    await redis_client.enqueue_job("send_dm_job", str(evt.id), evt.payload)
                else:
                    await redis_client.enqueue_job("process_webhook_event", str(evt.id), evt.payload)

        # Mark permanently failed where attempt_count >= 3
        stmt_fail = (
            update(WebhookEvent)
            .where(
                WebhookEvent.status == "PENDING",
                WebhookEvent.attempt_count >= 3
            )
            .values(
                status="FAILED",
                error="Exceeded max stuck-event retries (3 attempts)",
                updated_at=datetime.now(timezone.utc)
            )
        )
        await db.execute(stmt_fail)
        await db.commit()
    logger.info(f"Swept stuck events: {requeued_count} re-queued.")
    return requeued_count

async def startup(ctx: Dict[str, Any]) -> None:
    logger.info(f"Comlina ARQ Worker starting up. Redis at {worker_settings.REDIS_URL}")
    try:
        # Verify database connection
        async with engine.connect() as conn:
            logger.info("Worker database connection pool successfully initialized.")
    except Exception as e:
        logger.warning(f"Worker could not connect to PostgreSQL on startup (will retry on jobs): {e}")

async def shutdown(ctx: Dict[str, Any]) -> None:
    logger.info("Comlina ARQ Worker shutting down. Disposing DB engine...")
    await engine.dispose()
    logger.info("Worker shutdown complete.")

class WorkerSettings:
    functions = [process_webhook_event, process_comment_job, send_dm_job, refresh_expiring_tokens_job, sweep_stuck_events]
    cron_jobs = [
        cron(refresh_expiring_tokens_job, hour=3, minute=15, run_at_startup=False),
        cron(sweep_stuck_events, minute={0, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55}, run_at_startup=False)
    ]
    on_startup = startup
    on_shutdown = shutdown
    redis_settings = RedisSettings.from_dsn(worker_settings.REDIS_URL)
    max_jobs = 50
    poll_delay = 0.5
    job_timeout = 60
    max_tries = 3
    retry_delay = 30
