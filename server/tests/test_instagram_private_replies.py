# server/tests/test_instagram_private_replies.py
import pytest
from unittest.mock import AsyncMock, patch

from app.integrations.instagram.messaging import InstagramMessaging
from app.integrations.instagram.exceptions import MetaGraphAPIError, MetaRateLimitError
from app.engine.action_engine import ActionEngine

@pytest.mark.asyncio
async def test_private_reply_plain_text_without_buttons():
    """Verify that comment_id private reply without buttons sends simple text."""
    client_mock = AsyncMock()
    client_mock.post.return_value = {"recipient_id": "123", "message_id": "mid_001"}
    messaging = InstagramMessaging(client_mock)

    res = await messaging.send_private_reply(
        comment_id="comm_999",
        message_text="Thanks for your comment! Here is the info.",
        fallback_sender_id="sender_111"
    )
    assert res == {"recipient_id": "123", "message_id": "mid_001"}
    client_mock.post.assert_awaited_once_with(
        "me/messages",
        json_data={
            "recipient": {"comment_id": "comm_999"},
            "message": {"text": "Thanks for your comment! Here is the info."}
        }
    )

@pytest.mark.asyncio
async def test_private_reply_converts_cta_buttons_to_text_links():
    """Verify that CTA buttons with URLs are converted to plain text with URLs for comment_id."""
    client_mock = AsyncMock()
    client_mock.post.return_value = {"recipient_id": "123", "message_id": "mid_002"}
    messaging = InstagramMessaging(client_mock)

    buttons = [
        {"label": "Download Guide", "url": "https://comlina.com/guide.pdf"},
        {"title": "Join Community", "url": "https://comlina.com/discord"}
    ]
    res = await messaging.send_private_reply(
        comment_id="comm_888",
        message_text="Here are your resources:",
        fallback_sender_id="sender_222",
        buttons=buttons
    )
    assert res["message_id"] == "mid_002"
    call_payload = client_mock.post.call_args[1]["json_data"]
    assert call_payload["recipient"] == {"comment_id": "comm_888"}
    assert "attachment" not in call_payload["message"]
    assert "https://comlina.com/guide.pdf" in call_payload["message"]["text"]
    assert "Download Guide: https://comlina.com/guide.pdf" in call_payload["message"]["text"]
    assert "Join Community: https://comlina.com/discord" in call_payload["message"]["text"]

@pytest.mark.asyncio
async def test_private_reply_handles_postback_buttons_without_url():
    """Verify that postback buttons without URL do not inject template attachments."""
    client_mock = AsyncMock()
    client_mock.post.return_value = {"recipient_id": "123", "message_id": "mid_003"}
    messaging = InstagramMessaging(client_mock)

    buttons = [
        {"label": "I followed! 🚀", "payload": "VERIFY_FOLLOW"}
    ]
    await messaging.send_private_reply(
        comment_id="comm_777",
        message_text="Please follow us first!",
        fallback_sender_id="sender_333",
        buttons=buttons
    )
    call_payload = client_mock.post.call_args[1]["json_data"]
    assert call_payload["recipient"] == {"comment_id": "comm_777"}
    assert "attachment" not in call_payload["message"]
    assert "[I followed! 🚀]" in call_payload["message"]["text"]

@pytest.mark.asyncio
async def test_private_reply_never_falls_back_to_igsid_on_comment_failure():
    """
    Verify that when Meta rejects a comment_id private reply (e.g. 7-day window passed),
    the error is raised immediately and does NOT attempt direct DM to sender_id.
    """
    client_mock = AsyncMock()
    client_mock.post.side_effect = MetaGraphAPIError("Comment window expired", code=100, error_subcode=2018001)
    messaging = InstagramMessaging(client_mock)

    with pytest.raises(MetaGraphAPIError) as exc_info:
        await messaging.send_private_reply(
            comment_id="old_comment_123",
            message_text="Hello",
            fallback_sender_id="sender_444"
        )
    assert exc_info.value.code == 100
    assert exc_info.value.error_subcode == 2018001
    assert client_mock.post.await_count == 1

@pytest.mark.asyncio
async def test_private_reply_direct_dm_when_comment_id_missing():
    """Verify that when comment_id is None, it uses direct DM targeting recipient id."""
    client_mock = AsyncMock()
    client_mock.post.return_value = {"recipient_id": "sender_555", "message_id": "mid_direct"}
    messaging = InstagramMessaging(client_mock)

    buttons = [{"label": "Claim Deal", "url": "https://comlina.com/deal"}]
    res = await messaging.send_private_reply(
        comment_id=None,
        message_text="Special offer!",
        fallback_sender_id="sender_555",
        buttons=buttons
    )
    assert res["message_id"] == "mid_direct"
    call_payload = client_mock.post.call_args[1]["json_data"]
    assert call_payload["recipient"] == {"id": "sender_555"}
    # Direct DM within 24h window supports button template attachments
    assert call_payload["message"]["attachment"]["type"] == "template"

@pytest.mark.asyncio
async def test_private_reply_raises_value_error_if_no_ids():
    """Verify ValueError when neither comment_id nor fallback_sender_id is given."""
    client_mock = AsyncMock()
    messaging = InstagramMessaging(client_mock)

    with pytest.raises(ValueError, match="Neither comment_id nor fallback_sender_id provided"):
        await messaging.send_private_reply(
            comment_id=None,
            message_text="Hello",
            fallback_sender_id=None
        )

@pytest.mark.asyncio
async def test_action_engine_private_dm_preserves_structured_meta_error():
    """Verify ActionEngine captures structured error code and subcode upon failure."""
    client_mock = AsyncMock()
    client_mock.post.side_effect = MetaGraphAPIError(
        "Param recipient[comment_id] is invalid", code=100, error_subcode=2018002
    )

    action = {
        "type": "PRIVATE_DM",
        "text": "Hi {username}!",
        "buttons": [{"label": "Link", "url": "https://example.com"}]
    }
    context = {
        "comment_id": "comm_test",
        "sender_id": "user_test",
        "sender_username": "alex"
    }

    res = await ActionEngine.execute_action(action, context, instagram_client=client_mock)
    assert res["status"] == "FAILED"
    assert res["action"] == "PRIVATE_DM"
    assert "error" in res
    assert res.get("error_code") == 100
    assert res.get("meta_error") == {
        "code": 100,
        "subcode": 2018002,
        "message": "Param recipient[comment_id] is invalid"
    }
