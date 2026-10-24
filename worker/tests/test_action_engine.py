# worker/tests/test_action_engine.py
import pytest
from app.engine.action_engine import ActionEngine

@pytest.mark.asyncio
async def test_action_delay():
    action = {"type": "DELAY", "duration_seconds": 0}
    context = {"sender_username": "john_doe"}
    res = await ActionEngine.execute_action(action, context)
    assert res["status"] == "SUCCESS"
    assert res["action"] == "DELAY"

from unittest.mock import AsyncMock

@pytest.mark.asyncio
async def test_public_reply_template_formatting():
    mock_client = AsyncMock()
    mock_client.post = AsyncMock(return_value={"id": "reply_123"})

    action = {"type": "PUBLIC_REPLY", "text": "Hello @{username}, thank you!"}
    context = {"sender_username": "alice", "comment_id": "comm_123", "instagram_client": mock_client}
    res = await ActionEngine.execute_action(action, context, instagram_client=mock_client)
    assert res["status"] == "SUCCESS"
    assert res["text"] == "Hello @alice, thank you!"

    # Negative: Missing client must fail explicitly (F3 hardening: NO_CLIENT)
    res_no_client = await ActionEngine.execute_action(action, {"sender_username": "alice", "comment_id": "comm_123"})
    assert res_no_client["status"] == "FAILED"
    assert res_no_client["error_code"] == "NO_CLIENT"


def test_format_template_fallbacks():
    from app.engine.action_engine import format_template

    # 1. First name present
    t1 = format_template("Hey {first_name}! (@{username})", {"first_name": "Alice", "username": "alice_w"})
    assert t1 == "Hey Alice! (@alice_w)"

    # 2. First name empty/missing -> falls back to username
    t2 = format_template("Hey {first_name}!", {"first_name": "", "username": "alice_w"})
    assert t2 == "Hey alice_w!"
    t2_missing = format_template("Hey {first_name}!", {"username": "alice_w"})
    assert t2_missing == "Hey alice_w!"

    # 3. Both missing -> first_name falls back to "there", username is ""
    t3 = format_template("Hey {first_name}! {username}", {})
    assert t3 == "Hey there! "


@pytest.mark.asyncio
async def test_private_dm_template_first_name_fallback():
    from unittest.mock import AsyncMock
    mock_client = AsyncMock()
    mock_client.post = AsyncMock(return_value={"message_id": "mid_456"})

    action = {"type": "PRIVATE_DM", "text": "Hi {first_name}, check this out!"}

    # Context with user_profile having first_name
    ctx_with_profile = {
        "user_profile": {"first_name": "Bob", "username": "bob123"},
        "comment_id": "c1",
        "sender_id": "s1"
    }
    res1 = await ActionEngine.execute_action(action, ctx_with_profile, instagram_client=mock_client)
    assert res1["status"] == "SUCCESS"
    assert res1["text"] == "Hi Bob, check this out!"

    # Context with sender_username only (no first_name) -> falls back to sender_username
    ctx_username_only = {
        "sender_username": "bob123",
        "comment_id": "c1",
        "sender_id": "s1"
    }
    res2 = await ActionEngine.execute_action(action, ctx_username_only, instagram_client=mock_client)
    assert res2["status"] == "SUCCESS"
    assert res2["text"] == "Hi bob123, check this out!"

    # Context with neither -> falls back to "there"
    ctx_empty = {
        "comment_id": "c1",
        "sender_id": "s1"
    }
    res3 = await ActionEngine.execute_action(action, ctx_empty, instagram_client=mock_client)
    assert res3["status"] == "SUCCESS"
    assert res3["text"] == "Hi there, check this out!"

