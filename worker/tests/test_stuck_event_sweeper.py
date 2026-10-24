# worker/tests/test_stuck_event_sweeper.py
import uuid
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock
import pytest
from sqlalchemy import select
from app.core.database import get_db_session
from app.models import WebhookEvent
from worker.app.main import sweep_stuck_events


@pytest.mark.asyncio
async def test_sweep_stuck_events_requeues_and_fails():
    """
    Verify sweep_stuck_events:
    1. Re-queues PENDING events older than 5 minutes when attempt_count < 3.
    2. Increments attempt_count.
    3. Marks events with attempt_count >= 3 as FAILED.
    4. Ignores recent events (< 5 minutes) or already PROCESSED events.
    """
    now = datetime.now(timezone.utc)
    old_time = now - timedelta(minutes=10)
    recent_time = now - timedelta(minutes=2)

    event_stuck_id = uuid.uuid4()
    event_max_tries_id = uuid.uuid4()
    event_recent_id = uuid.uuid4()
    event_processed_id = uuid.uuid4()

    async with get_db_session() as session:
        # 1. Stuck event: PENDING, 10 min old, attempt 1 -> should be requeued (attempt becomes 2)
        evt_stuck = WebhookEvent(
            id=event_stuck_id,
            provider_event_id=f"stuck_{uuid.uuid4().hex[:8]}",
            event_type="comments",
            payload={"test": "comment_payload"},
            status="PENDING",
            received_at=old_time,
            attempt_count=1
        )
        session.add(evt_stuck)

        # 2. Max attempts event: PENDING, 10 min old, attempt 3 -> should be marked FAILED
        evt_max = WebhookEvent(
            id=event_max_tries_id,
            provider_event_id=f"max_{uuid.uuid4().hex[:8]}",
            event_type="comments",
            payload={"test": "max_payload"},
            status="PENDING",
            received_at=old_time,
            attempt_count=3
        )
        session.add(evt_max)

        # 3. Recent event: PENDING, 2 min old, attempt 1 -> should NOT be touched
        evt_recent = WebhookEvent(
            id=event_recent_id,
            provider_event_id=f"recent_{uuid.uuid4().hex[:8]}",
            event_type="comments",
            payload={"test": "recent_payload"},
            status="PENDING",
            received_at=recent_time,
            attempt_count=1
        )
        session.add(evt_recent)

        # 4. Already processed event: PROCESSED, 10 min old -> should NOT be touched
        evt_proc = WebhookEvent(
            id=event_processed_id,
            provider_event_id=f"proc_{uuid.uuid4().hex[:8]}",
            event_type="comments",
            payload={"test": "processed_payload"},
            status="PROCESSED",
            received_at=old_time,
            attempt_count=1
        )
        session.add(evt_proc)
        await session.commit()

    # Mock Redis context
    mock_redis = AsyncMock()
    ctx = {"redis": mock_redis}

    # Run sweeper
    requeued = await sweep_stuck_events(ctx)
    assert requeued >= 1

    # Verify mock_redis was called to enqueue job for the stuck event
    mock_redis.enqueue_job.assert_called_with(
        "process_comment_job",
        str(event_stuck_id),
        {"test": "comment_payload"}
    )

    # Verify database states
    async with get_db_session() as session:
        # Check stuck event was updated
        res_stuck = await session.execute(select(WebhookEvent).where(WebhookEvent.id == event_stuck_id))
        stuck_row = res_stuck.scalar_one()
        assert stuck_row.status == "PENDING"
        assert stuck_row.attempt_count == 2

        # Check max tries event became FAILED
        res_max = await session.execute(select(WebhookEvent).where(WebhookEvent.id == event_max_tries_id))
        max_row = res_max.scalar_one()
        assert max_row.status == "FAILED"
        assert "Exceeded max stuck-event retries" in str(max_row.error)

        # Check recent event remains untouched
        res_recent = await session.execute(select(WebhookEvent).where(WebhookEvent.id == event_recent_id))
        recent_row = res_recent.scalar_one()
        assert recent_row.status == "PENDING"
        assert recent_row.attempt_count == 1

        # Check processed event remains untouched
        res_proc = await session.execute(select(WebhookEvent).where(WebhookEvent.id == event_processed_id))
        proc_row = res_proc.scalar_one()
        assert proc_row.status == "PROCESSED"
