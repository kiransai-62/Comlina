# server/tests/test_simulator_and_messaging.py
import uuid
import pytest
from datetime import datetime
from unittest.mock import AsyncMock, patch
from sqlalchemy import select
from fastapi.testclient import TestClient

from app.main import app
from app.core.database import get_db_session, init_db
from app.models import InstagramAccount, Automation, Contact, Conversation, Message, WebhookEvent, Workspace
from app.core.encryption import encrypt_token
from app.integrations.instagram.messaging import InstagramMessaging
from app.jobs.send_dm import send_dm_job

@pytest.mark.asyncio
async def test_send_private_reply_with_buttons():
    client_mock = AsyncMock()
    client_mock.post.return_value = {"message_id": "mid_12345"}
    messaging = InstagramMessaging(client_mock)

    buttons = [
        {"label": "Download Guide", "url": "https://comlina.com/guide.pdf"}
    ]
    res = await messaging.send_private_reply(
        comment_id="comm_123",
        message_text="Here is your requested guide!",
        fallback_sender_id="sender_456",
        buttons=buttons
    )
    assert res == {"message_id": "mid_12345"}
    client_mock.post.assert_awaited_once()
    call_args = client_mock.post.call_args
    assert call_args[0][0] == "me/messages"
    payload = call_args[1]["json_data"]
    assert payload["recipient"] == {"comment_id": "comm_123"}
    assert payload["message"]["attachment"]["type"] == "template"
    assert payload["message"]["attachment"]["payload"]["buttons"][0]["url"] == "https://comlina.com/guide.pdf"

@pytest.mark.asyncio
async def test_send_private_reply_fallback_to_sender_id():
    client_mock = AsyncMock()
    # First call with comment_id raises exception, fallback with sender_id succeeds
    client_mock.post.side_effect = [Exception("Comment too old"), {"message_id": "mid_fallback"}]
    messaging = InstagramMessaging(client_mock)

    res = await messaging.send_private_reply(
        comment_id="expired_comm",
        message_text="Hello directly in DM",
        fallback_sender_id="ig_user_789"
    )
    assert res == {"message_id": "mid_fallback"}
    assert client_mock.post.await_count == 2
    # Verify second call used recipient id
    second_call = client_mock.post.call_args_list[1]
    assert second_call[1]["json_data"]["recipient"] == {"id": "ig_user_789"}

@pytest.mark.asyncio
async def test_messaging_webhook_send_dm_job_pipeline():
    await init_db()
    ws_id = uuid.uuid4()
    acc_id = uuid.uuid4()

    biz_ig_id = f"biz_ig_{uuid.uuid4().hex[:8]}"
    async with get_db_session() as session:
        ws = Workspace(id=ws_id, name="Test Studio WS", slug=f"test-ws-{uuid.uuid4().hex[:6]}")
        session.add(ws)

        acc = InstagramAccount(
            id=acc_id,
            workspace_id=ws_id,
            ig_user_id=biz_ig_id,
            username="business_brand",
            access_token_encrypted=encrypt_token("mock_token_123"),
            is_active=True
        )
        session.add(acc)

        # Create active DM automation
        auto = Automation(
            id=uuid.uuid4(),
            workspace_id=ws_id,
            instagram_account_id=acc_id,
            name="DM Auto Reply",
            trigger_type="DM_REPLY",
            status="ACTIVE",
            flow_definition={
                "type": "DM_REPLY",
                "replyToAll": True,
                "responseDm": {
                    "message": "Thanks for reaching out! A team member will assist you shortly."
                }
            }
        )
        session.add(auto)
        await session.commit()

    event_id = str(uuid.uuid4())
    event_data = {
        "provider_event_id": f"msg_evt_{uuid.uuid4().hex[:8]}",
        "event_type": "MESSAGING",
        "sender_id": f"viewer_user_{uuid.uuid4().hex[:6]}",
        "sender_username": "happy_customer",
        "recipient_id": biz_ig_id,
        "business_ig_id": biz_ig_id,
        "workspace_id": str(ws_id),
        "instagram_account_id": str(acc_id),
        "text": "Hello, I accepted your request!"
    }

    # Execute send_dm_job
    result = await send_dm_job({}, event_id, event_data)
    assert result["status"] == "COMPLETED"
    assert result["automations_matched"] >= 1

    # Verify Contact was upserted with is_converted=True
    async with get_db_session() as session:
        contact_res = await session.execute(
            select(Contact).where(
                Contact.workspace_id == ws_id,
                Contact.ig_user_id == event_data["sender_id"]
            )
        )
        contact = contact_res.scalar_one_or_none()
        assert contact is not None
        assert contact.is_converted is True
        assert contact.username == "happy_customer"
        assert contact.last_interaction_at is not None

        # Verify Conversation was created and status is OPEN
        conv_res = await session.execute(
            select(Conversation).where(
                Conversation.workspace_id == ws_id,
                Conversation.contact_id == contact.id
            )
        )
        conv = conv_res.scalar_one_or_none()
        assert conv is not None
        assert conv.status == "OPEN"
        assert conv.last_message_text == "Hello, I accepted your request!"

        # Verify incoming CONTACT message was recorded
        msg_res = await session.execute(
            select(Message).where(
                Message.workspace_id == ws_id,
                Message.conversation_id == conv.id,
                Message.sender_type == "CONTACT"
            )
        )
        contact_msg = msg_res.scalar_one_or_none()
        assert contact_msg is not None
        assert contact_msg.text == "Hello, I accepted your request!"

def test_simulate_comment_endpoint():
    client = TestClient(app)
    # Post to simulate-comment
    payload = {
        "text": "Can you send me the AI link?",
        "sender_username": "alex_creator",
        "sender_id": "alex_12345"
    }
    response = client.post("/webhooks/instagram/simulate-comment", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "SIMULATION_SUCCESS"
    assert "execution_result" in data
    assert "event_id" in data

    # Also test mounted /api/webhooks/instagram/simulate-comment
    response_api = client.post("/api/webhooks/instagram/simulate-comment", json=payload)
    assert response_api.status_code == 200
    assert response_api.json()["status"] == "SIMULATION_SUCCESS"
