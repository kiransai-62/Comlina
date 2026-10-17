# worker/tests/test_trigger_engine.py
import pytest
from app.engine.trigger_engine import TriggerEngine

def test_v1_trigger_all_comments():
    trigger = {"type": "COMMENT", "postsScope": "ALL"}
    event = {"event_type": "COMMENT", "text": "hello world"}
    assert TriggerEngine.evaluate_trigger(trigger, event) is True

def test_v1_trigger_specific_post():
    trigger = {"type": "COMMENT", "postsScope": "SPECIFIC", "postIds": ["post_123", "post_456"]}
    assert TriggerEngine.evaluate_trigger(trigger, {"event_type": "COMMENT", "post_id": "post_123", "text": "hi"}) is True
    assert TriggerEngine.evaluate_trigger(trigger, {"event_type": "COMMENT", "post_id": "post_999", "text": "hi"}) is False

def test_v2_playbook_single_keyword():
    trigger = {
        "type": "COMMENT_TO_DM",
        "replyToAll": False,
        "keywords": ["AI", "link"]
    }
    # Case-insensitive match on "ai"
    assert TriggerEngine.evaluate_trigger(trigger, {"event_type": "COMMENT", "text": "I love AI tools!"}) is True
    assert TriggerEngine.evaluate_trigger(trigger, {"event_type": "COMMENT", "text": "Send me the link please"}) is True
    # Word boundary prevents partial match on "train" or "blink"
    assert TriggerEngine.evaluate_trigger(trigger, {"event_type": "COMMENT", "text": "Let us train together"}) is False
    assert TriggerEngine.evaluate_trigger(trigger, {"event_type": "COMMENT", "text": "Don't blink"}) is False

def test_v2_playbook_multi_word_phrase():
    trigger = {
        "type": "COMMENT_TO_DM",
        "replyToAll": False,
        "keywords": ["send me", "check dm"]
    }
    # Matches exact multi-word phrase case-insensitively
    assert TriggerEngine.evaluate_trigger(trigger, {"event_type": "COMMENT", "text": "Could you SEND ME the guide?"}) is True
    assert TriggerEngine.evaluate_trigger(trigger, {"event_type": "COMMENT", "text": "Please check dm when you can"}) is True
    # Non-match returns False (Ignore)
    assert TriggerEngine.evaluate_trigger(trigger, {"event_type": "COMMENT", "text": "Nice video, good job!"}) is False

def test_v2_playbook_reply_to_all():
    trigger = {
        "type": "COMMENT_TO_DM",
        "replyToAll": True,
        "keywords": []
    }
    assert TriggerEngine.evaluate_trigger(trigger, {"event_type": "COMMENT", "text": "Any comment matches!"}) is True
    assert TriggerEngine.evaluate_trigger(trigger, {"event_type": "COMMENT", "text": "🔥"}) is True

def test_v2_playbook_selected_post_id():
    trigger = {
        "type": "COMMENT_TO_DM",
        "selectedPostId": "media_777",
        "replyToAll": True
    }
    assert TriggerEngine.evaluate_trigger(trigger, {"event_type": "COMMENT", "post_id": "media_777", "text": "hi"}) is True
    assert TriggerEngine.evaluate_trigger(trigger, {"event_type": "COMMENT", "post_id": "media_888", "text": "hi"}) is False

def test_v2_playbook_all_posts():
    trigger = {
        "type": "COMMENT_TO_DM",
        "selectedPostId": "all",
        "replyToAll": True
    }
    assert TriggerEngine.evaluate_trigger(trigger, {"event_type": "COMMENT", "post_id": "media_999", "text": "hi"}) is True

def test_v2_playbook_event_type_mismatch():
    trigger = {"type": "COMMENT_TO_DM", "replyToAll": True}
    # Messaging event against comment trigger
    assert TriggerEngine.evaluate_trigger(trigger, {"event_type": "MESSAGING", "text": "hi"}) is False
