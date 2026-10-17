# worker/app/main.py
import logging
from typing import Dict, Any
from arq.connections import RedisSettings
from arq import cron
from app.core.config import worker_settings
from app.core.database import engine
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
    elif event_type == "MESSAGING":
        return await send_dm_job(ctx, event_id, event_data)

    return {"status": "UNHANDLED_EVENT_TYPE", "type": event_type}

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
    functions = [process_webhook_event, process_comment_job, send_dm_job, refresh_expiring_tokens_job]
    cron_jobs = [cron(refresh_expiring_tokens_job, hour=3, minute=15, run_at_startup=False)]
    on_startup = startup
    on_shutdown = shutdown
    redis_settings = RedisSettings.from_dsn(worker_settings.REDIS_URL)
    max_jobs = 50
    poll_delay = 0.5
    job_timeout = 60
    max_tries = 3
    retry_delay = 30
