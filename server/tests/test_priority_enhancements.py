# server/tests/test_priority_enhancements.py
import pytest
import uuid
from datetime import datetime, timezone, timedelta
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.models import Workspace, WorkspaceMember, User, InstagramAccount, Message, Contact, WebhookEvent, AnalyticsEvent
from app.core.database import get_db_session
from app.api.auth import create_backend_jwt
from app.engine.trigger_engine import TriggerEngine
from app.integrations.instagram.webhooks import InstagramWebhookParser

@pytest.mark.asyncio
async def test_workspace_settings_update_and_delete():
    async with get_db_session() as db:
        user = User(
            id=uuid.uuid4(),
            email=f"ws_test_{uuid.uuid4().hex[:6]}@example.com",
            full_name="Settings Test User"
        )
        ws = Workspace(
            id=uuid.uuid4(),
            name="Original Workspace",
            slug=f"ws-slug-{uuid.uuid4().hex[:6]}",
            plan_tier="FREE",
            settings={}
        )
        member = WorkspaceMember(
            workspace_id=ws.id,
            user_id=user.id,
            role="OWNER"
        )
        db.add_all([user, ws, member])
        await db.commit()

    token = create_backend_jwt(str(user.id), user.email)
    headers = {"Authorization": f"Bearer {token}"}

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Update Workspace Settings
        patch_res = await client.patch(
            "/api/workspaces/current/settings",
            headers=headers,
            json={
                "name": "Renamed Workspace",
                "notification_lead": True,
                "notification_token": True,
                "follow_check": False,
                "public_reply": True,
                "language": "Spanish"
            }
        )
        assert patch_res.status_code == 200, patch_res.text
        data = patch_res.json()
        assert data["success"] is True
        assert data["name"] == "Renamed Workspace"
        assert data["settings"]["notification_lead"] is True
        assert data["settings"]["language"] == "Spanish"

        # 2. Delete Workspace
        del_res = await client.delete("/api/workspaces/current", headers=headers)
        assert del_res.status_code == 200, del_res.text
        assert del_res.json()["success"] is True

        # Verify deletion in DB
        async with get_db_session() as db:
            deleted_ws = await db.get(Workspace, ws.id)
            assert deleted_ws is None


@pytest.mark.asyncio
async def test_analytics_timeseries_endpoint():
    async with get_db_session() as db:
        user = User(
            id=uuid.uuid4(),
            email=f"anlt_test_{uuid.uuid4().hex[:6]}@example.com",
            full_name="Analytics Test User"
        )
        ws = Workspace(
            id=uuid.uuid4(),
            name="Analytics Workspace",
            slug=f"anlt-slug-{uuid.uuid4().hex[:6]}",
            plan_tier="PRO"
        )
        member = WorkspaceMember(
            workspace_id=ws.id,
            user_id=user.id,
            role="OWNER"
        )
        db.add_all([user, ws, member])
        await db.commit()

    token = create_backend_jwt(str(user.id), user.email)
    headers = {"Authorization": f"Bearer {token}"}

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get("/api/analytics/timeseries?days=7", headers=headers)
        assert res.status_code == 200, res.text
        data = res.json()
        assert data["days"] == 7
        assert len(data["series"]) == 7
        assert "summary" in data
        assert "conversion_rate_pct" in data["summary"]


def test_story_reply_and_story_mention_webhook_parsing():
    # 1. Story Reply Payload
    story_reply_payload = {
        "entry": [{
            "id": "17841400000000001",
            "time": 1700000000,
            "messaging": [{
                "sender": {"id": "viewer_123"},
                "recipient": {"id": "17841400000000001"},
                "timestamp": 1700000000000,
                "message": {
                    "mid": "m_story_reply_mid_001",
                    "text": "Send me the link!",
                    "reply_to": {
                        "story": {
                            "id": "story_media_999",
                            "url": "https://instagram.com/stories/creator/999"
                        }
                    }
                }
            }]
        }]
    }

    events = InstagramWebhookParser.extract_events(story_reply_payload)
    assert len(events) == 1
    evt = events[0]
    assert evt["event_type"] == "STORY_REPLY"
    assert evt["story_id"] == "story_media_999"
    assert evt["sender_id"] == "viewer_123"
    assert evt["text"] == "Send me the link!"

    # 2. Story Mention Payload
    story_mention_payload = {
        "entry": [{
            "id": "17841400000000001",
            "time": 1700000000,
            "messaging": [{
                "sender": {"id": "viewer_456"},
                "recipient": {"id": "17841400000000001"},
                "timestamp": 1700000000000,
                "message": {
                    "mid": "m_story_mention_mid_002",
                    "attachments": [{
                        "type": "story_mention",
                        "payload": {
                            "url": "https://instagram.com/stories/viewer_456/123"
                        }
                    }]
                }
            }]
        }]
    }

    mention_events = InstagramWebhookParser.extract_events(story_mention_payload)
    assert len(mention_events) == 1
    m_evt = mention_events[0]
    assert m_evt["event_type"] == "STORY_MENTION"
    assert m_evt["story_url"] == "https://instagram.com/stories/viewer_456/123"


def test_trigger_engine_story_evaluations():
    # Story Reply trigger with keyword
    story_reply_trigger = {
        "type": "STORY_REPLY",
        "keywords": ["LINK", "FREE"],
        "match_mode": "CONTAINS"
    }

    match_event = {
        "event_type": "STORY_REPLY",
        "text": "Hey please send the LINK now!"
    }
    assert TriggerEngine.evaluate_trigger(story_reply_trigger, match_event) is True

    nomatch_event = {
        "event_type": "STORY_REPLY",
        "text": "Cool story bro"
    }
    assert TriggerEngine.evaluate_trigger(story_reply_trigger, nomatch_event) is False

    # Story Mention trigger (auto-reply to any story mention)
    story_mention_trigger = {
        "type": "STORY_MENTION",
        "keywords": []
    }
    mention_event = {
        "event_type": "STORY_MENTION",
        "text": ""
    }
    assert TriggerEngine.evaluate_trigger(story_mention_trigger, mention_event) is True
