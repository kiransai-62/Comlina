# server/tests/test_quota_reservation.py
import uuid
import asyncio
import pytest
from sqlalchemy import text
from app.core.database import get_db_session, init_db
from app.jobs.process_comment import reserve_quota, rollback_quota
from app.models import Workspace, InstagramAccount, PostUsage, AutomationRun


@pytest.mark.asyncio
async def test_quota_reservation_concurrent_boundary():
    """
    Verify that concurrent quota reservations at the quota boundary enforce the cap atomically
    without row-level locking deadlocks or race conditions.
    """
    await init_db()
    ws_id = uuid.uuid4()
    acc_id = uuid.uuid4()
    media_id = f"media_{uuid.uuid4().hex[:8]}"

    async with get_db_session() as session:
        ws = Workspace(id=ws_id, name="Atomic WS", slug=f"atomic-{uuid.uuid4().hex[:6]}", plan_tier="FREE")
        session.add(ws)
        acc = InstagramAccount(
            id=acc_id,
            workspace_id=ws_id,
            ig_user_id=f"ig_{uuid.uuid4().hex[:8]}",
            username="atomic_creator",
            access_token_encrypted="mock_enc_token",
            is_active=True
        )
        session.add(acc)
        # Pre-seed post_usage at 9 DMs delivered, with max_dms cap of 10 (only 1 slot remaining)
        usage = PostUsage(
            id=uuid.uuid4(),
            workspace_id=ws_id,
            instagram_account_id=acc_id,
            ig_account_id=str(acc_id),
            media_id=media_id,
            dms_delivered_count=9,
            max_dms=10
        )
        session.add(usage)
        await session.commit()

    # Attempt two concurrent reservations when only 1 slot is left
    async def try_reserve(evt_id: str):
        async with get_db_session() as session:
            return await reserve_quota(
                session,
                account_id=acc_id,
                event_id=evt_id,
                automation_id=uuid.uuid4(),
                media_id=media_id,
                max_dms=10,
                workspace_id=ws_id
            )

    evt_1 = f"evt_conc_1_{uuid.uuid4().hex[:6]}"
    evt_2 = f"evt_conc_2_{uuid.uuid4().hex[:6]}"
    res1, res2 = await asyncio.gather(
        try_reserve(evt_1),
        try_reserve(evt_2)
    )

    # Exactly one must succeed and one must be rejected (False)
    results = [res1, res2]
    assert results.count(True) == 1
    assert results.count(False) == 1

    # Verify database state has exactly 10 deliveries (capped)
    async with get_db_session() as session:
        check_usage = await session.execute(
            text("SELECT dms_delivered_count FROM post_usage WHERE media_id = :media_id"),
            {"media_id": media_id}
        )
        assert check_usage.scalar() == 10


@pytest.mark.asyncio
async def test_failed_dm_releases_quota():
    """
    Verify that if a DM fails permanently, rollback_quota releases the reserved count
    so customer quota is preserved.
    """
    await init_db()
    acc_id = uuid.uuid4()
    ws_id = uuid.uuid4()
    media_id = f"media_{uuid.uuid4().hex[:8]}"
    evt_fail = f"evt_fail_{uuid.uuid4().hex[:6]}"

    async with get_db_session() as session:
        ws = Workspace(id=ws_id, name="Rollback WS", slug=f"rb-{uuid.uuid4().hex[:6]}")
        session.add(ws)
        acc = InstagramAccount(
            id=acc_id,
            workspace_id=ws_id,
            ig_user_id=f"ig_{uuid.uuid4().hex[:8]}",
            username="rb_creator",
            access_token_encrypted="mock_token",
            is_active=True
        )
        session.add(acc)
        # Pre-seed with 5 DMs
        usage = PostUsage(
            id=uuid.uuid4(),
            workspace_id=ws_id,
            instagram_account_id=acc_id,
            ig_account_id=str(acc_id),
            media_id=media_id,
            dms_delivered_count=5,
            max_dms=10
        )
        session.add(usage)
        await session.commit()

    # Step 1: Reserve quota for event
    async with get_db_session() as session:
        reserved = await reserve_quota(
            session,
            account_id=acc_id,
            event_id=evt_fail,
            media_id=media_id,
            max_dms=10,
            workspace_id=ws_id
        )
        assert reserved is True

    # Quota is now 6
    async with get_db_session() as session:
        cnt = (await session.execute(
            text("SELECT dms_delivered_count FROM post_usage WHERE media_id = :m"),
            {"m": media_id}
        )).scalar()
        assert cnt == 6

    # Step 2: DM delivery fails, execute rollback
    async with get_db_session() as session:
        await rollback_quota(session, account_id=acc_id, media_id=media_id)

    # Quota is rolled back to 5
    async with get_db_session() as session:
        cnt = (await session.execute(
            text("SELECT dms_delivered_count FROM post_usage WHERE media_id = :m"),
            {"m": media_id}
        )).scalar()
        assert cnt == 5


@pytest.mark.asyncio
async def test_retry_does_not_double_count_reservation():
    """
    Verify that an ARQ retry with the same event_id does not increment dms_delivered_count twice.
    """
    await init_db()
    acc_id = uuid.uuid4()
    ws_id = uuid.uuid4()
    media_id = f"media_{uuid.uuid4().hex[:8]}"
    event_id = f"evt_retry_{uuid.uuid4().hex[:6]}"

    async with get_db_session() as session:
        ws = Workspace(id=ws_id, name="Retry WS", slug=f"retry-{uuid.uuid4().hex[:6]}")
        session.add(ws)
        acc = InstagramAccount(
            id=acc_id,
            workspace_id=ws_id,
            ig_user_id=f"ig_{uuid.uuid4().hex[:8]}",
            username="retry_creator",
            access_token_encrypted="mock_token",
            is_active=True
        )
        session.add(acc)
        usage = PostUsage(
            id=uuid.uuid4(),
            workspace_id=ws_id,
            instagram_account_id=acc_id,
            ig_account_id=str(acc_id),
            media_id=media_id,
            dms_delivered_count=2,
            max_dms=10
        )
        session.add(usage)
        await session.commit()

    # First attempt: reserves quota (count becomes 3)
    async with get_db_session() as session:
        r1 = await reserve_quota(
            session,
            account_id=acc_id,
            event_id=event_id,
            media_id=media_id,
            max_dms=10,
            workspace_id=ws_id
        )
        assert r1 is True

    async with get_db_session() as session:
        cnt1 = (await session.execute(
            text("SELECT dms_delivered_count FROM post_usage WHERE media_id = :m"),
            {"m": media_id}
        )).scalar()
        assert cnt1 == 3

    # Second attempt (ARQ retry with same event_id): idempotent check passes, count stays 3
    async with get_db_session() as session:
        r2 = await reserve_quota(
            session,
            account_id=acc_id,
            event_id=event_id,
            media_id=media_id,
            max_dms=10,
            workspace_id=ws_id
        )
        assert r2 is True

    async with get_db_session() as session:
        cnt2 = (await session.execute(
            text("SELECT dms_delivered_count FROM post_usage WHERE media_id = :m"),
            {"m": media_id}
        )).scalar()
        assert cnt2 == 3
