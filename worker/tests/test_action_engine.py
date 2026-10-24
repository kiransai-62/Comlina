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
