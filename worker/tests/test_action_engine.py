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

@pytest.mark.asyncio
async def test_public_reply_template_formatting():
    action = {"type": "PUBLIC_REPLY", "text": "Hello @{username}, thank you!"}
    context = {"sender_username": "alice", "comment_id": None}
    res = await ActionEngine.execute_action(action, context)
    assert res["status"] == "SUCCESS"
    assert res["text"] == "Hello @alice, thank you!"
