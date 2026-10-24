# worker/app/main.py
import sys
import logging
from pathlib import Path
from typing import Dict, Any
from datetime import datetime, timezone, timedelta
from arq.connections import RedisSettings
from arq import cron
from sqlalchemy import select, update

# Ensure repository root and server directory are in sys.path
REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
SERVER_DIR = REPO_ROOT / "server"
if str(SERVER_DIR) not in sys.path:
    sys.path.insert(0, str(SERVER_DIR))

# Re-route all imports to the single source of truth in server/app
from server.app.core.config import settings
from server.app.core.database import SessionLocal, engine
from server.app.jobs.process_comment import process_comment_job
from server.app.jobs.send_dm import send_dm_job
from server.app.jobs.refresh_tokens import refresh_tokens_cron
from app.models import WebhookEvent

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("worker")


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
    logger.info(f"Comlina ARQ Worker starting up. Redis at {settings.REDIS_URL}")
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
    functions = [process_comment_job, send_dm_job, sweep_stuck_events, refresh_tokens_cron]
    cron_jobs = [
        cron(refresh_tokens_cron, hour=3, minute=15),
        cron(sweep_stuck_events, minute={0, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55})
    ]
    on_startup = startup
    on_shutdown = shutdown
    redis_settings = RedisSettings.from_dsn(settings.REDIS_URL)
    max_tries = 3
