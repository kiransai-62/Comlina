# worker/tests/test_flow_engine_v2.py
import pytest
from app.engine.flow_engine import FlowEngine

def test_extract_conditions_v2_ask_follow():
    playbook = {
        "type": "COMMENT_TO_DM",
        "askFollow": {
            "enabled": True,
            "message": "Please follow our profile first!",
            "buttonLabel": "Follow Us"
        }
    }
    conditions = FlowEngine._extract_conditions(playbook)
    assert len(conditions) == 1
    assert conditions[0]["type"] == "FOLLOWER_STATUS"
    assert conditions[0]["expected"] == "FOLLOWING"
    assert conditions[0]["message"] == "Please follow our profile first!"

def test_extract_actions_v2_comment_to_dm():
    playbook = {
        "type": "COMMENT_TO_DM",
        "teaserReply": {
            "enabled": True,
            "message": "Sent you a DM! Check your inbox 🚀"
        },
        "responseDm": {
            "message": "Here is the download link: https://comlina.com",
            "buttons": [
                {"label": "Download PDF", "url": "https://comlina.com/download.pdf"}
            ]
        }
    }
    actions = FlowEngine._extract_actions(playbook)
    assert len(actions) == 2
    assert actions[0]["type"] == "PUBLIC_REPLY"
    assert actions[0]["text"] == "Sent you a DM! Check your inbox 🚀"
    assert actions[1]["type"] == "PRIVATE_DM"
    assert "https://comlina.com" in actions[1]["text"]
    assert len(actions[1]["buttons"]) == 1

def test_extract_actions_v2_comment_reply():
    playbook = {
        "type": "COMMENT_REPLY",
        "replyText": "Thank you for supporting us!"
    }
    actions = FlowEngine._extract_actions(playbook)
    assert len(actions) == 1
    assert actions[0]["type"] == "PUBLIC_REPLY"
    assert actions[0]["text"] == "Thank you for supporting us!"

@pytest.mark.asyncio
async def test_run_flow_v2_studio_playbook():
    playbook = {
        "type": "COMMENT_TO_DM",
        "selectedPostId": "post_42",
        "replyToAll": False,
        "keywords": ["AI"],
        "teaserReply": {
            "enabled": True,
            "message": "Sent to your DMs!"
        },
        "responseDm": {
            "message": "Hey {first_name}, here is your AI template!"
        }
    }
    # Matching event
    event = {
        "event_type": "COMMENT",
        "post_id": "post_42",
        "comment_id": "comm_99",
        "sender_id": "sender_101",
        "sender_username": "sarah",
        "text": "Please share the AI template"
    }
    res = await FlowEngine.run_flow(playbook, event)
    assert res["status"] == "COMPLETED"
    assert len(res["results"]) == 2
    assert res["results"][0]["action"] == "PUBLIC_REPLY"
    assert res["results"][1]["action"] == "PRIVATE_DM"
    assert "sarah" in res["results"][1]["text"]

@pytest.mark.asyncio
async def test_run_flow_v2_trigger_mismatch():
    playbook = {
        "type": "COMMENT_TO_DM",
        "selectedPostId": "post_42",
        "replyToAll": False,
        "keywords": ["AI"]
    }
    event = {
        "event_type": "COMMENT",
        "post_id": "post_42",
        "text": "Great photo!"  # No keyword match
    }
    res = await FlowEngine.run_flow(playbook, event)
    assert res["status"] == "TRIGGER_MISMATCH"
    assert res["results"] == []
