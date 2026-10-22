# worker/tests/test_worker_private_replies.py
import pytest
from unittest.mock import AsyncMock

from app.integrations.instagram.messaging import InstagramMessaging
from app.integrations.instagram.exceptions import MetaGraphAPIError
from app.engine.action_engine import ActionEngine

@pytest.mark.asyncio
async def test_worker_private_reply_plain_text_with_links():
    """Verify that worker send_private_reply converts CTA links into plain text."""
    client_mock = AsyncMock()
    client_mock.post.return_value = {"recipient_id": "123", "message_id": "mid_w_001"}
    messaging = InstagramMessaging(client_mock)

    buttons = [{"label": "Get PDF", "url": "https://comlina.com/file.pdf"}]
    res = await messaging.send_private_reply(
        comment_id="comm_w1",
        message_text="Download below:",
        fallback_sender_id="sender_w1",
        buttons=buttons
    )
    assert res == {"recipient_id": "123", "message_id": "mid_w_001"}
    call_payload = client_mock.post.call_args[1]["json_data"]
    assert call_payload["recipient"] == {"comment_id": "comm_w1"}
    assert "attachment" not in call_payload["message"]
    assert "Get PDF: https://comlina.com/file.pdf" in call_payload["message"]["text"]

@pytest.mark.asyncio
async def test_worker_private_reply_no_blind_fallback():
    """Verify worker never silently falls back to recipient ID on comment_id error."""
    client_mock = AsyncMock()
    client_mock.post.side_effect = MetaGraphAPIError("Expired comment", code=100)
    messaging = InstagramMessaging(client_mock)

    with pytest.raises(MetaGraphAPIError):
        await messaging.send_private_reply(
            comment_id="comm_old",
            message_text="Hi",
            fallback_sender_id="sender_w2"
        )
    assert client_mock.post.await_count == 1

@pytest.mark.asyncio
async def test_worker_action_engine_structured_error():
    """Verify worker ActionEngine records structured error metadata."""
    client_mock = AsyncMock()
    client_mock.post.side_effect = MetaGraphAPIError("Token expired", code=190, error_subcode=463)

    action = {"type": "PRIVATE_DM", "text": "Hello", "buttons": []}
    context = {"comment_id": "comm_err", "sender_id": "user_err"}

    res = await ActionEngine.execute_action(action, context, instagram_client=client_mock)
    assert res["status"] == "FAILED"
    assert res["error_code"] == 190
    assert res["meta_error"]["subcode"] == 463
