# server/tests/test_messaging_abuse.py
import uuid
import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch
from sqlalchemy import select

from app.core.database import get_db_session, init_db
from app.models import (
    InstagramAccount,
    Automation,
    Contact,
    Conversation,
    Message,
    WebhookEvent,
    Workspace,
    PostUsage
)
from app.core.encryption import encrypt_token
from app.integrations.instagram.webhooks import InstagramWebhookParser
from app.jobs.send_dm import send_dm_job
from app.jobs.process_comment import process_comment_job


def test_webhook_parser_ignores_echo_messages():
    payload = {
        "entry": [
            {
                "id": "biz_12345",
                "messaging": [
                    {
                        "message": {"is_echo": True, "text": "Echo reply"},
                        "sender": {"id": "biz_12345"},
                        "recipient": {"id": "user_999"}
                    }
                ]
            }
        ]
    }
    events = InstagramWebhookParser.extract_events(payload)
    assert len(events) == 0


def test_webhook_parser_ignores_self_dm():
    payload = {
        "entry": [
            {
                "id": "biz_12345",
                "messaging": [
                    {
                        "message": {"text": "Self DM attempt", "mid": "mid_self_1"},
                        "sender": {"id": "biz_12345"},
                        "recipient": {"id": "biz_12345"}
                    }
                ]
            }
        ]
    }
    events = InstagramWebhookParser.extract_events(payload)
    assert len(events) == 0


def test_webhook_parser_ignores_self_comment():
    payload = {
        "entry": [
            {
                "id": "biz_12345",
                "changes": [
                    {
                        "field": "comments",
                        "value": {
                            "id": "comm_self_1",
                            "from": {"id": "biz_12345", "username": "business_brand"},
                            "text": "Self comment reply"
                        }
                    }
                ]
            }
        ]
    }
    events = InstagramWebhookParser.extract_events(payload)
    assert len(events) == 0


@pytest.mark.asyncio
async def test_send_dm_job_skips_self_event():
    await init_db()
    ws_id = uuid.uuid4()
    acc_id = uuid.uuid4()
    biz_ig_id = f"biz_ig_{uuid.uuid4().hex[:8]}"

    async with get_db_session() as session:
        ws = Workspace(id=ws_id, name="Self DM Test WS", slug=f"self-dm-ws-{uuid.uuid4().hex[:6]}")
        session.add(ws)
        acc = InstagramAccount(
            id=acc_id,
            workspace_id=ws_id,
            ig_user_id=biz_ig_id,
            username="business_brand",
            access_token_encrypted=encrypt_token("low_entropy_token_123"),
            is_active=True
        )
        session.add(acc)
        await session.commit()

    event_data = {
        "event_type": "MESSAGING",
        "provider_event_id": f"mid_self_{uuid.uuid4().hex[:8]}",
        "sender_id": biz_ig_id,  # Same as account.ig_user_id
        "recipient_id": biz_ig_id,
        "text": "Self-sent loop message",
        "instagram_account_id": str(acc_id)
    }

    result = await send_dm_job({}, "mock_event_id", event_data)
    assert result["status"] == "SKIPPED_SELF_EVENT"
    assert result["reason"] == "SELF_EVENT_SKIPPED"


@pytest.mark.asyncio
async def test_process_comment_job_skips_self_comment():
    await init_db()
    ws_id = uuid.uuid4()
    acc_id = uuid.uuid4()
    biz_ig_id = f"biz_ig_{uuid.uuid4().hex[:8]}"

    async with get_db_session() as session:
        ws = Workspace(id=ws_id, name="Self Comment Test WS", slug=f"self-comm-ws-{uuid.uuid4().hex[:6]}")
        session.add(ws)
        acc = InstagramAccount(
            id=acc_id,
            workspace_id=ws_id,
            ig_user_id=biz_ig_id,
            username="business_brand",
            access_token_encrypted=encrypt_token("low_entropy_token_123"),
            is_active=True
        )
        session.add(acc)
        await session.commit()

    event_data = {
        "event_type": "COMMENT",
        "provider_event_id": f"comm_self_{uuid.uuid4().hex[:8]}",
        "sender_id": biz_ig_id,  # Same as account.ig_user_id
        "sender_username": "business_brand",
        "text": "Self comment loop trigger",
        "instagram_account_id": str(acc_id),
        "business_ig_id": biz_ig_id
    }

    result = await process_comment_job({}, "mock_event_id", event_data)
    assert result["status"] == "SKIPPED_SELF_EVENT"
    assert result["reason"] == "SELF_EVENT_SKIPPED"


@pytest.mark.asyncio
async def test_send_dm_job_message_deduplication():
    await init_db()
    ws_id = uuid.uuid4()
    acc_id = uuid.uuid4()
    biz_ig_id = f"biz_ig_{uuid.uuid4().hex[:8]}"
    viewer_ig_id = f"viewer_ig_{uuid.uuid4().hex[:8]}"
    mid = f"mid_dup_{uuid.uuid4().hex[:8]}"

    async with get_db_session() as session:
        ws = Workspace(id=ws_id, name="Dedup Test WS", slug=f"dedup-ws-{uuid.uuid4().hex[:6]}")
        session.add(ws)
        acc = InstagramAccount(
            id=acc_id,
            workspace_id=ws_id,
            ig_user_id=biz_ig_id,
            username="business_brand",
            access_token_encrypted=encrypt_token("low_entropy_token_123"),
            is_active=True
        )
        session.add(acc)
        # Create an active DM automation with no matching trigger to avoid sending extra DMs
        auto = Automation(
            id=uuid.uuid4(),
            workspace_id=ws_id,
            instagram_account_id=acc_id,
            name="DM Auto",
            trigger_type="DM_KEYWORD",
            status="ACTIVE",
            flow_definition={"type": "KEYWORD", "keywords": ["SPECIALKEYWORD"], "responseDm": {"text": "Reply"}}
        )
        session.add(auto)
        await session.commit()

    event_data = {
        "event_type": "MESSAGING",
        "provider_event_id": mid,
        "sender_id": viewer_ig_id,
        "recipient_id": biz_ig_id,
        "text": "Regular contact message",
        "instagram_account_id": str(acc_id)
    }

    # First delivery
    await send_dm_job({}, "evt_1", event_data)

    # Second delivery (replay/retry of the exact same event)
    await send_dm_job({}, "evt_2", event_data)

    async with get_db_session() as session:
        stmt = select(Message).where(Message.meta_message_id == mid)
        res = await session.execute(stmt)
        messages = list(res.scalars().all())
        # Must be deduplicated - only 1 message stored
        assert len(messages) == 1


@pytest.mark.asyncio
async def test_process_comment_quota_enforcement():
    await init_db()
    ws_id = uuid.uuid4()
    acc_id = uuid.uuid4()
    biz_ig_id = f"biz_ig_{uuid.uuid4().hex[:8]}"
    media_id = f"post_{uuid.uuid4().hex[:8]}"

    async with get_db_session() as session:
        # Create Free tier workspace (max 10 posts, max 99 DMs per post)
        ws = Workspace(
            id=ws_id,
            name="Quota WS",
            slug=f"quota-ws-{uuid.uuid4().hex[:6]}",
            plan_tier="FREE"
        )
        session.add(ws)
        acc = InstagramAccount(
            id=acc_id,
            workspace_id=ws_id,
            ig_user_id=biz_ig_id,
            username="business_brand",
            access_token_encrypted=encrypt_token("low_entropy_token_123"),
            is_active=True
        )
        session.add(acc)
        # PostUsage already has 100 DMs delivered (exceeds max 99 for Free)
        usage = PostUsage(
            id=uuid.uuid4(),
            workspace_id=ws_id,
            instagram_account_id=acc_id,
            media_id=media_id,
            dms_delivered_count=100,
            last_delivered_at=datetime.now(timezone.utc)
        )
        session.add(usage)
        auto = Automation(
            id=uuid.uuid4(),
            workspace_id=ws_id,
            instagram_account_id=acc_id,
            name="Comment Auto",
            trigger_type="COMMENT_REPLY",
            status="ACTIVE",
            flow_definition={"type": "COMMENT", "replyToAll": True, "responseDm": {"text": "Reply"}}
        )
        session.add(auto)
        await session.commit()

    event_data = {
        "event_type": "COMMENT",
        "provider_event_id": f"comm_{uuid.uuid4().hex[:8]}",
        "sender_id": f"viewer_{uuid.uuid4().hex[:8]}",
        "sender_username": "regular_viewer",
        "text": "Comment on capped post",
        "post_id": media_id,
        "instagram_account_id": str(acc_id),
        "business_ig_id": biz_ig_id
    }

    result = await process_comment_job({}, "evt_quota_test", event_data)
    assert result["status"] == "QUOTA_EXCEEDED"
    assert "DM_QUOTA_EXCEEDED" in result["reason"]
