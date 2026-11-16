# server/tests/test_master_repair_suite.py
import hashlib
import hmac
import json
import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, patch

import pytest
from app.core.encryption import decrypt_token, encrypt_token
from app.engine.condition_engine import ConditionEngine
from app.engine.flow_engine import FlowEngine
from app.engine.trigger_engine import TriggerEngine, matches_specific_words
from app.integrations.instagram.follower_status import FollowerStatusService
from app.integrations.instagram.oauth import InstagramOAuthService
from app.services.automation_service import AutomationService


# ============================================================================
# 1. AUTHENTICATION & TOKEN PERSISTENCE TESTS
# ============================================================================

def test_deterministic_token_encryption_persists_across_reinit():
    raw_token = "IGQVJ_long_lived_meta_token_example_1234567890"
    encrypted = encrypt_token(raw_token)
    assert encrypted != raw_token
    assert decrypt_token(encrypted) == raw_token


def test_oauth_signed_state_validation():
    ws_id = str(uuid.uuid4())
    user_id = str(uuid.uuid4())
    state = InstagramOAuthService.create_signed_state(ws_id, user_id)
    assert InstagramOAuthService.verify_signed_state(state, ws_id) is True
    assert InstagramOAuthService.verify_signed_state(state, str(uuid.uuid4())) is False


@pytest.mark.asyncio
async def test_revoked_token_returns_reconnect_required():
    mock_resp = AsyncMock()
    mock_resp.status_code = 401
    mock_resp.content = b'{"error": {"message": "Error validating access token: Session has been invalidated", "code": 190}}'
    mock_resp.json = lambda: {
        "error": {
            "message": "Error validating access token: Session has been invalidated",
            "code": 190,
        }
    }

    with patch("httpx.AsyncClient.get", return_value=mock_resp):
        res = await InstagramOAuthService.fetch_and_validate_profile("revoked_token")
        assert res["valid"] is False
        assert res["revoked"] is True
        assert res["error_code"] == 190


# ============================================================================
# 2. TRIGGER ENGINE TESTS (SPECIFIC WORDS, ANY WORD, MEDIA ID, PUNCTUATION)
# ============================================================================

def test_specific_words_case_insensitive_and_punctuation():
    keywords = ["price", "details", "send link"]
    assert matches_specific_words("Can you share the PRICE?!", keywords) == "price"
    assert matches_specific_words("   DeTaIlS please  ", keywords) == "details"
    assert matches_specific_words("Hey, please SEND LINK now!", keywords) == "send link"
    assert matches_specific_words("Awesome video!", keywords) is None


def test_trigger_engine_media_id_matching():
    trigger_cfg = {
        "trigger_type": "SPECIFIC_WORDS",
        "media_id": "17895695668004550",
        "keywords": ["blueprint"],
    }
    # Matching media_id + keyword
    res_ok = TriggerEngine.evaluate(
        trigger_cfg,
        {"media_id": "17895695668004550", "comment_text": "Send me the Blueprint!"},
    )
    assert res_ok["matched"] is True
    assert res_ok["matched_keyword"] == "blueprint"

    # Wrong media_id
    res_wrong_post = TriggerEngine.evaluate(
        trigger_cfg,
        {"media_id": "99999999999999999", "comment_text": "Send me the Blueprint!"},
    )
    assert res_wrong_post["matched"] is False
    assert res_wrong_post["reason"] == "MEDIA_ID_MISMATCH"


def test_trigger_engine_any_word_and_empty_comment():
    any_word_cfg = {
        "trigger_type": "ANY_WORD",
        "media_id": "17895695668004550",
        "keywords": [],
    }
    res_any = TriggerEngine.evaluate(
        any_word_cfg,
        {"media_id": "17895695668004550", "comment_text": "🔥👏"},
    )
    assert res_any["matched"] is True
    assert res_any["trigger_type"] == "ANY_WORD"

    res_empty = TriggerEngine.evaluate(
        any_word_cfg,
        {"media_id": "17895695668004550", "comment_text": "   "},
    )
    assert res_empty["matched"] is False
    assert res_empty["reason"] == "EMPTY_COMMENT"


# ============================================================================
# 3. FOLLOW CONDITION & LIMITATION HANDLING TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_follow_condition_never_fakes_follower_on_api_limitation():
    mock_resp = AsyncMock()
    mock_resp.status_code = 200
    mock_resp.content = b'{"id": "12345", "username": "test_user"}'
    # Meta omits `is_user_follow_business` when scope/thread is not established
    mock_resp.json = lambda: {"id": "12345", "username": "test_user"}

    with patch("httpx.AsyncClient.get", return_value=mock_resp):
        status_res = await FollowerStatusService.check_follower_status("12345", "valid_token")
        assert status_res["status"] == "CHECK_UNAVAILABLE"
        assert status_res["is_following"] is False
        assert "is_user_follow_business" in status_res["limitation"]


def test_condition_engine_follow_enabled_vs_disabled():
    # Disabled follow condition passes immediately
    res_disabled = ConditionEngine.evaluate(
        [{"type": "IS_FOLLOWER", "enabled": False}],
        {"follower_status": "NOT_FOLLOWING"},
    )
    assert res_disabled["passed"] is True

    # Enabled follow condition with FOLLOWING passes
    res_following = ConditionEngine.evaluate(
        [{"type": "IS_FOLLOWER", "enabled": True}],
        {"follower_status": "FOLLOWING"},
    )
    assert res_following["passed"] is True

    # Enabled follow condition with NOT_FOLLOWING triggers Follow-to-Unlock gate
    res_not_following = ConditionEngine.evaluate(
        [{"type": "IS_FOLLOWER", "enabled": True, "prompt_message": "Follow first!"}],
        {"follower_status": "NOT_FOLLOWING"},
    )
    assert res_not_following["passed"] is False
    assert res_not_following["follow_gate_required"] is True
    assert res_not_following["prompt_message"] == "Follow first!"


# ============================================================================
# 4. AUTOMATION PAYLOAD VALIDATION & END-TO-END FLOW ENGINE TESTS
# ============================================================================

def test_automation_service_payload_validation():
    normalized = AutomationService.validate_and_normalize_payload({
        "automation_name": "Reel Lead Magnet",
        "media_id": "179000111222333",
        "trigger_type": "SPECIFIC_WORDS",
        "keywords": ["guide", "link"],
        "follow_condition": {"enabled": True},
        "response_config": {
            "comment_reply": "Check your DMs! 📩",
            "dm_text": "Here is your free guide: https://comlina.ai/guide",
        },
        "is_active": True,
    })
    assert normalized["name"] == "Reel Lead Magnet"
    assert normalized["media_id"] == "179000111222333"
    assert normalized["trigger_type"] == "SPECIFIC_WORDS"
    assert normalized["keywords"] == ["guide", "link"]
    assert normalized["follow_condition"]["enabled"] is True
    assert normalized["is_active"] is True
    assert normalized["status"] == "ACTIVE"
    assert len(normalized["flow_definition"]["actions"]) == 2


@pytest.mark.asyncio
async def test_end_to_end_flow_engine_execution():
    normalized = AutomationService.validate_and_normalize_payload({
        "automation_name": "Instant Link DM",
        "media_id": "179000111222333",
        "trigger_type": "SPECIFIC_WORDS",
        "keywords": ["price"],
        "follow_condition": {"enabled": True},
        "response_config": {
            "comment_reply": "Sent you the details!",
            "dm_text": "Here is the pricing link: https://comlina.ai/pricing",
        },
    })

    with patch(
        "app.engine.action_engine.ActionEngine.send_comment_reply",
        new=AsyncMock(return_value={"success": True, "reply_id": "rep_1"}),
    ), patch(
        "app.engine.action_engine.ActionEngine.send_private_reply_dm",
        new=AsyncMock(return_value={"success": True, "message_id": "msg_1"}),
    ):
        result = await FlowEngine.execute(
            flow_definition=normalized["flow_definition"],
            event_context={
                "ig_business_id": "17841400000000",
                "access_token": "test_token",
                "comment_id": "17888888888",
                "comment_text": "What is the PRICE?",
                "commenter_id": "9988776655",
                "media_id": "179000111222333",
                "follower_status": "FOLLOWING",
            },
        )
        assert result["status"] == "COMPLETED"
        assert result["matched_keyword"] == "price"
        assert result["dm_sent"] is True
        assert result["comment_replied"] is True
