# worker/tests/test_worker_follower_handling.py
import pytest
from unittest.mock import AsyncMock
from app.integrations.instagram.follower_status import InstagramFollowerService, FollowerStatus
from app.integrations.instagram.exceptions import MetaRateLimitError, MetaGraphAPIError
from app.engine.condition_engine import ConditionEngine
from app.engine.flow_engine import FlowEngine

@pytest.mark.asyncio
async def test_worker_follower_service_statuses():
    client_mock = AsyncMock()

    # FOLLOWING
    client_mock.get.return_value = {"id": "u1", "is_user_follow_business": True}
    service = InstagramFollowerService(client_mock)
    status, _ = await service.check_follower_status("b1", "u1")
    assert status == FollowerStatus.FOLLOWING

    # NOT_FOLLOWING
    client_mock.get.return_value = {"id": "u2", "is_user_follow_business": False}
    status, _ = await service.check_follower_status("b1", "u2")
    assert status == FollowerStatus.NOT_FOLLOWING

    # CHECK_UNAVAILABLE on missing field
    client_mock.get.return_value = {"id": "u3"}
    status, _ = await service.check_follower_status("b1", "u3")
    assert status == FollowerStatus.CHECK_UNAVAILABLE

    # CHECK_UNAVAILABLE on rate limit
    client_mock.get.side_effect = MetaRateLimitError("Rate limit")
    status, _ = await service.check_follower_status("b1", "u4")
    assert status == FollowerStatus.CHECK_UNAVAILABLE

    # CHECK_UNAVAILABLE on Graph error (messaging consent required)
    client_mock.get.side_effect = MetaGraphAPIError("Messaging consent required", code=100)
    status, _ = await service.check_follower_status("b1", "u5")
    assert status == FollowerStatus.CHECK_UNAVAILABLE

    # UNKNOWN on missing IDs
    status, _ = await service.check_follower_status("", "u6")
    assert status == FollowerStatus.UNKNOWN

def test_worker_condition_engine_four_statuses():
    cond = {
        "type": "FOLLOWER_STATUS",
        "expected": "FOLLOWING",
        "fallbackAction": "SEND_FOLLOW_GATE",
        "onUnavailableAction": "HANDLE_CHECK_UNAVAILABLE",
        "onUnknownAction": "HANDLE_UNKNOWN",
    }
    assert ConditionEngine.evaluate_condition(cond, {"follower_status": "FOLLOWING"}) == (True, "CONTINUE")
    assert ConditionEngine.evaluate_condition(cond, {"follower_status": "NOT_FOLLOWING"}) == (False, "SEND_FOLLOW_GATE")
    assert ConditionEngine.evaluate_condition(cond, {"follower_status": "CHECK_UNAVAILABLE"}) == (False, "HANDLE_CHECK_UNAVAILABLE")
    assert ConditionEngine.evaluate_condition(cond, {"follower_status": "UNKNOWN"}) == (False, "HANDLE_UNKNOWN")

@pytest.mark.asyncio
async def test_worker_flow_engine_unavailable_follower_handling():
    playbook = {
        "type": "COMMENT_TO_DM",
        "selectedPostId": "post_77",
        "replyToAll": True,
        "askFollow": {
            "enabled": True,
            "message": "Follow us to unlock!",
            "unavailableMessage": "Follow status check unavailable. Follow @test_brand to verify."
        },
        "responseDm": {"message": "Protected resource link: https://secret.com"},
        "teaserReply": {"enabled": True, "message": "Check your DM! 📩"}
    }
    event = {
        "event_type": "COMMENT",
        "post_id": "post_77",
        "comment_id": "comm_77",
        "sender_id": "sender_77",
        "sender_username": "alex",
        "business_username": "test_brand",
        "business_ig_id": "biz_77"
    }

    client_mock = AsyncMock()
    # Graph error simulates comment-only user without prior messaging consent
    client_mock.get.side_effect = MetaGraphAPIError("Messaging consent required", code=100)
    client_mock.post.return_value = {"message_id": "mid_77", "id": "rep_77"}

    res = await FlowEngine.run_flow(playbook, event, instagram_client=client_mock)
    assert res["status"] == "FALLBACK_EXECUTED"
    assert res["follower_verified"] is False
    assert res["follower_status"] == "CHECK_UNAVAILABLE"
    assert res["initial_state"] == "verification_unavailable"

    # Protected link is withheld
    dm_res = next(r for r in res["results"] if r["action"] == "PRIVATE_DM")
    assert "https://secret.com" not in dm_res["text"]
    assert "Follow @test_brand" in dm_res["text"]

    # Public teaser reply is sent after successful DM initiation
    teaser_res = next(r for r in res["results"] if r["action"] == "PUBLIC_REPLY")
    assert teaser_res["status"] == "SUCCESS"
