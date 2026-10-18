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

# ══════════════════════════════════════════════════════════════════════════
# NEW TRIGGER MODE SPECIFICATION TESTS: "specific_keywords" & "any_keyword"
# ══════════════════════════════════════════════════════════════════════════

def test_trigger_mode_specific_keywords_with_single_keyword():
    flow = {
        "type": "COMMENT_TO_DM",
        "trigger": {
            "type": "COMMENT",
            "triggerMode": "specific_keywords",
            "keywords": ["PRICE"],
            "matchWholeWords": True,
        }
    }
    # Matches keyword exactly / whole word
    assert TriggerEngine.evaluate_trigger(flow, {"event_type": "COMMENT", "text": "what is the price?"}) is True
    assert TriggerEngine.evaluate_trigger(flow, {"event_type": "COMMENT", "text": "PRICE"}) is True
    # Does not match non-keyword
    assert TriggerEngine.evaluate_trigger(flow, {"event_type": "COMMENT", "text": "great video!"}) is False
    # Does not match partial word (e.g. priceless)
    assert TriggerEngine.evaluate_trigger(flow, {"event_type": "COMMENT", "text": "this is priceless"}) is False

def test_trigger_mode_specific_keywords_with_multiple_keywords():
    flow = {
        "type": "COMMENT_TO_DM",
        "trigger": {
            "type": "COMMENT",
            "triggerMode": "specific_keywords",
            "keywords": ["PRICE", "LINK", "INFO"],
            "matchWholeWords": True,
        }
    }
    assert TriggerEngine.evaluate_trigger(flow, {"event_type": "COMMENT", "text": "send me the link"}) is True
    assert TriggerEngine.evaluate_trigger(flow, {"event_type": "COMMENT", "text": "more info please"}) is True
    assert TriggerEngine.evaluate_trigger(flow, {"event_type": "COMMENT", "text": "I love your content!"}) is False

def test_trigger_mode_specific_keywords_empty_keywords_does_not_trigger():
    flow = {
        "type": "COMMENT_TO_DM",
        "trigger": {
            "type": "COMMENT",
            "triggerMode": "specific_keywords",
            "keywords": [],
        }
    }
    # In specific_keywords mode, an empty keyword list must NOT trigger as any keyword
    assert TriggerEngine.evaluate_trigger(flow, {"event_type": "COMMENT", "text": "hello"}) is False

def test_trigger_mode_any_keyword_triggers_on_any_comment():
    flow = {
        "type": "COMMENT_TO_DM",
        "trigger": {
            "type": "COMMENT",
            "triggerMode": "any_keyword",
            # Even if keywords are preserved in state, any comment triggers!
            "keywords": ["PRICE", "LINK"],
        }
    }
    assert TriggerEngine.evaluate_trigger(flow, {"event_type": "COMMENT", "text": "Just saying hello! 👋"}) is True
    assert TriggerEngine.evaluate_trigger(flow, {"event_type": "COMMENT", "text": "Awesome reel 🔥"}) is True
    assert TriggerEngine.evaluate_trigger(flow, {"event_type": "COMMENT", "text": "PRICE"}) is True
    assert TriggerEngine.evaluate_trigger(flow, {"event_type": "COMMENT", "text": ""}) is True

def test_trigger_mode_any_keyword_respects_post_scope():
    flow = {
        "type": "COMMENT_TO_DM",
        "trigger": {
            "type": "COMMENT",
            "triggerMode": "any_keyword",
            "selectedPostId": "media_post_100",
        }
    }
    # Matching post triggers for any comment
    assert TriggerEngine.evaluate_trigger(flow, {
        "event_type": "COMMENT",
        "post_id": "media_post_100",
        "text": "Any comment on targeted post"
    }) is True

    # Non-matching post does not trigger even in any_keyword mode
    assert TriggerEngine.evaluate_trigger(flow, {
        "event_type": "COMMENT",
        "post_id": "media_post_999",
        "text": "Comment on different post"
    }) is False

def test_trigger_mode_any_keyword_ineligible_event_type():
    flow = {
        "type": "COMMENT_TO_DM",
        "trigger": {
            "type": "COMMENT",
            "triggerMode": "any_keyword",
        }
    }
    # Event type mismatch: DM event against comment flow
    assert TriggerEngine.evaluate_trigger(flow, {
        "event_type": "MESSAGING",
        "text": "Direct message"
    }) is False

def test_legacy_automations_without_trigger_mode():
    # Legacy flow with keywords
    legacy_flow = {
        "type": "COMMENT_TO_DM",
        "trigger": {
            "type": "COMMENT",
            "keywords": ["VIP"],
        }
    }
    assert TriggerEngine.evaluate_trigger(legacy_flow, {"event_type": "COMMENT", "text": "I am VIP"}) is True
    assert TriggerEngine.evaluate_trigger(legacy_flow, {"event_type": "COMMENT", "text": "hello"}) is False
