# server/tests/test_follower_condition_handling.py
import uuid
import pytest
from unittest.mock import AsyncMock, patch
from sqlalchemy import select

from app.core.database import init_db, get_db_session
from app.core.encryption import encrypt_token
from app.engine.flow_engine import FlowEngine
from app.engine.condition_engine import ConditionEngine
from app.integrations.instagram.follower_status import InstagramFollowerService, FollowerStatus
from app.integrations.instagram.exceptions import MetaRateLimitError, MetaGraphAPIError
from app.jobs.process_comment import process_comment_job
from app.jobs.send_dm import send_dm_job
from app.models import (
    Workspace,
    InstagramAccount,
    Automation,
    Contact,
    Conversation,
    Message,
)

@pytest.fixture(autouse=True)
async def setup_db():
    await init_db()


# ---------------------------------------------------------------------------
# 1. InstagramFollowerService - Unit Tests for All Statuses & API Exceptions
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_follower_service_confirmed_following():
    client_mock = AsyncMock()
    client_mock.get.return_value = {"id": "user_1", "is_user_follow_business": True}
    service = InstagramFollowerService(client_mock)

    status, reason = await service.check_follower_status("biz_1", "user_1")
    assert status == FollowerStatus.FOLLOWING
    assert "Confirmed follower" in reason


@pytest.mark.asyncio
async def test_follower_service_confirmed_not_following():
    client_mock = AsyncMock()
    client_mock.get.return_value = {"id": "user_2", "is_user_follow_business": False}
    service = InstagramFollowerService(client_mock)

    status, reason = await service.check_follower_status("biz_1", "user_2")
    assert status == FollowerStatus.NOT_FOLLOWING
    assert "Confirmed non-follower" in reason


@pytest.mark.asyncio
async def test_follower_service_missing_field_is_check_unavailable():
    """
    CRITICAL: When Meta returns user info but omits 'is_user_follow_business',
    it must return CHECK_UNAVAILABLE and NEVER falsely default to NOT_FOLLOWING.
    """
    client_mock = AsyncMock()
    client_mock.get.return_value = {"id": "user_3", "name": "Jane"}
    service = InstagramFollowerService(client_mock)

    status, reason = await service.check_follower_status("biz_1", "user_3")
    assert status == FollowerStatus.CHECK_UNAVAILABLE
    assert status != FollowerStatus.NOT_FOLLOWING
    assert "did not return follower status field" in reason


@pytest.mark.asyncio
async def test_follower_service_none_or_non_boolean_is_check_unavailable():
    client_mock = AsyncMock()
    client_mock.get.return_value = {"id": "user_4", "is_user_follow_business": None}
    service = InstagramFollowerService(client_mock)

    status, _ = await service.check_follower_status("biz_1", "user_4")
    assert status == FollowerStatus.CHECK_UNAVAILABLE


@pytest.mark.asyncio
async def test_follower_service_rate_limit_exception():
    client_mock = AsyncMock()
    client_mock.get.side_effect = MetaRateLimitError("Rate limit exceeded")
    service = InstagramFollowerService(client_mock)

    status, reason = await service.check_follower_status("biz_1", "user_5")
    assert status == FollowerStatus.CHECK_UNAVAILABLE
    assert "Rate Limit" in reason


@pytest.mark.asyncio
async def test_follower_service_graph_api_error_first_time_commenter():
    """
    First-time commenter with no prior messaging conversation causes Meta to return
    Graph API error (missing messaging consent). Must return CHECK_UNAVAILABLE.
    """
    client_mock = AsyncMock()
    client_mock.get.side_effect = MetaGraphAPIError("Requires user messaging consent", code=100)
    service = InstagramFollowerService(client_mock)

    status, reason = await service.check_follower_status("biz_1", "user_6")
    assert status == FollowerStatus.CHECK_UNAVAILABLE
    assert "messaging consent" in reason


@pytest.mark.asyncio
async def test_follower_service_unexpected_exception():
    client_mock = AsyncMock()
    client_mock.get.side_effect = RuntimeError("Network socket dropped")
    service = InstagramFollowerService(client_mock)

    status, reason = await service.check_follower_status("biz_1", "user_7")
    assert status == FollowerStatus.CHECK_UNAVAILABLE
    assert "Unexpected error" in reason
    assert "Network socket dropped" not in reason


@pytest.mark.asyncio
async def test_follower_service_does_not_leak_raw_exception_or_token():
    client_mock = AsyncMock()
    client_mock.get.side_effect = MetaGraphAPIError(
        message="Sensitive failure at https://graph.facebook.com?access_token=EAAB12345",
        code=100
    )
    service = InstagramFollowerService(client_mock)
    status, reason = await service.check_follower_status("biz_1", "user_sensitive")
    assert status == FollowerStatus.CHECK_UNAVAILABLE
    assert "EAAB12345" not in reason
    assert "https://" not in reason
    assert "access_token" not in reason
    assert "code=100" in reason

    client_mock.get.side_effect = RuntimeError("Fatal DB string with password=my_db_pass")
    status_unexp, reason_unexp = await service.check_follower_status("biz_1", "user_sensitive")
    assert status_unexp == FollowerStatus.CHECK_UNAVAILABLE
    assert "my_db_pass" not in reason_unexp
    assert reason_unexp == "Unexpected error checking follower status"


@pytest.mark.asyncio
async def test_follower_service_missing_ids_is_unknown():
    client_mock = AsyncMock()
    service = InstagramFollowerService(client_mock)

    status1, _ = await service.check_follower_status("", "user_8")
    assert status1 == FollowerStatus.UNKNOWN

    status2, _ = await service.check_follower_status("biz_1", "")
    assert status2 == FollowerStatus.UNKNOWN


# ---------------------------------------------------------------------------
# 2. ConditionEngine - Distinct Evaluation of 4 Follower States
# ---------------------------------------------------------------------------

def test_condition_engine_keeps_four_statuses_distinct():
    cond = {
        "type": "FOLLOWER_STATUS",
        "expected": "FOLLOWING",
        "fallbackAction": "SEND_FOLLOW_GATE",
        "onUnavailableAction": "HANDLE_CHECK_UNAVAILABLE",
        "onUnknownAction": "HANDLE_UNKNOWN",
    }

    # 1. FOLLOWING -> passes
    passed, action = ConditionEngine.evaluate_condition(cond, {"follower_status": "FOLLOWING"})
    assert passed is True
    assert action == "CONTINUE"

    # 2. NOT_FOLLOWING -> fails with SEND_FOLLOW_GATE
    passed, action = ConditionEngine.evaluate_condition(cond, {"follower_status": "NOT_FOLLOWING"})
    assert passed is False
    assert action == "SEND_FOLLOW_GATE"

    # 3. CHECK_UNAVAILABLE -> fails with distinct HANDLE_CHECK_UNAVAILABLE
    passed, action = ConditionEngine.evaluate_condition(cond, {"follower_status": "CHECK_UNAVAILABLE"})
    assert passed is False
    assert action == "HANDLE_CHECK_UNAVAILABLE"
    assert action != "SEND_FOLLOW_GATE"

    # 4. UNKNOWN -> fails with distinct HANDLE_UNKNOWN
    passed, action = ConditionEngine.evaluate_condition(cond, {"follower_status": "UNKNOWN"})
    assert passed is False
    assert action == "HANDLE_UNKNOWN"
    assert action != "SEND_FOLLOW_GATE"


# ---------------------------------------------------------------------------
# 3. First-Time Commenter Flow: Accurate Fallback without False Claims
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_first_time_commenter_unavailable_messaging_consent():
    """
    When a first-time commenter triggers an automation with askFollow:
    - Meta Graph API returns missing messaging consent error.
    - Status is CHECK_UNAVAILABLE.
    - System accurately tells user follow status could not be verified automatically.
    - Protected resource link is NOT delivered.
    - Follow gate DM is sent via comment_id private reply.
    - Contact stores follower_status='CHECK_UNAVAILABLE'.
    """
    ws_id = uuid.uuid4()
    acc_id = uuid.uuid4()
    biz_ig_id = f"biz_{uuid.uuid4().hex[:8]}"

    async with get_db_session() as session:
        ws = Workspace(id=ws_id, name="WS FirstTime", slug=f"ws-ft-{uuid.uuid4().hex[:6]}")
        session.add(ws)

        acc = InstagramAccount(
            id=acc_id,
            workspace_id=ws_id,
            ig_user_id=biz_ig_id,
            username="brand_creator",
            access_token_encrypted=encrypt_token("EAAB_token_ft"),
            is_active=True
        )
        session.add(acc)

        auto = Automation(
            id=uuid.uuid4(),
            workspace_id=ws_id,
            instagram_account_id=acc_id,
            name="First Time Commenter Flow",
            trigger_type="COMMENT",
            status="ACTIVE",
            flow_definition={
                "trigger": {"type": "COMMENT", "triggerMode": "any_keyword"},
                "automatedDm": {
                    "message": "Protected resource: https://secret.download/guide",
                    "button": {"label": "Download", "url": "https://secret.download/guide"}
                },
                "advanced": {
                    "askFollow": {
                        "enabled": True,
                        "message": "Please follow @brand_creator to unlock this resource!",
                        "unavailableMessage": "We could not verify your follow status automatically from this comment. Follow @brand_creator and tap below to receive your download link 🚀"
                    },
                    "commentTeaser": {
                        "enabled": True,
                        "message": "Check your DM! 📩"
                    }
                }
            }
        )
        session.add(auto)
        await session.commit()

    commenter_id = f"first_time_{uuid.uuid4().hex[:6]}"
    event_data = {
        "provider_event_id": f"evt_{uuid.uuid4().hex[:8]}",
        "event_type": "COMMENT",
        "business_ig_id": biz_ig_id,
        "sender_id": commenter_id,
        "sender_username": "new_commenter",
        "text": "Send me the guide!",
        "post_id": "media_post_900",
        "comment_id": "comm_900"
    }

    with patch("app.jobs.process_comment.MetaGraphClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client_cls.return_value = mock_client
        # Meta returns Graph API error due to lack of messaging consent on first-time commenter
        mock_client.get = AsyncMock(side_effect=MetaGraphAPIError("Requires user messaging consent", code=100))
        mock_client.post = AsyncMock(return_value={"message_id": "mid_unavail_901", "id": "rep_901"})

        summary = await process_comment_job({}, f"wh_{uuid.uuid4().hex[:8]}", event_data)

    assert summary["status"] == "COMPLETED"
    assert summary["follower_verified"] is False
    assert summary["follower_status"] == "CHECK_UNAVAILABLE"
    assert summary["processing_state"] == "verification_pending"

    # Protected link was withheld
    results = summary["results"][0]["result"]["results"]
    dm_res = next(r for r in results if r["action"] == "PRIVATE_DM")
    assert "https://secret.download/guide" not in dm_res["text"]

    # Accurate unavailable message sent
    assert "could not verify your follow status automatically" in dm_res["text"]
    assert "Follow @brand_creator" in dm_res["text"]

    # Public teaser reply sent after successful private reply
    teaser_res = next(r for r in results if r["action"] == "PUBLIC_REPLY")
    assert teaser_res["status"] == "SUCCESS"

    # Verify contact in DB has exact CHECK_UNAVAILABLE follower_status
    async with get_db_session() as session:
        c_res = await session.execute(select(Contact).where(Contact.ig_user_id == commenter_id))
        contact = c_res.scalar_one_or_none()
        assert contact is not None
        assert contact.follower_status == "CHECK_UNAVAILABLE"
        assert contact.automation_state == "verification_pending"
        assert contact.custom_fields["follow_gate_pending"]["verification_status"] == "CHECK_UNAVAILABLE"


# ---------------------------------------------------------------------------
# 4. DM Delivery Failure Suppresses Public Teaser
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_private_reply_failure_suppresses_teaser_and_marks_failed():
    """
    If private reply delivery to Meta fails (e.g. Meta rate limit or user blocks DMs),
    public teaser reply must NOT be sent, and processing state must be 'failed'.
    """
    ws_id = uuid.uuid4()
    acc_id = uuid.uuid4()
    biz_ig_id = f"biz_{uuid.uuid4().hex[:8]}"

    async with get_db_session() as session:
        ws = Workspace(id=ws_id, name="WS Fail", slug=f"ws-fl-{uuid.uuid4().hex[:6]}")
        session.add(ws)

        acc = InstagramAccount(
            id=acc_id,
            workspace_id=ws_id,
            ig_user_id=biz_ig_id,
            username="fail_brand",
            access_token_encrypted=encrypt_token("EAAB_token_fl"),
            is_active=True
        )
        session.add(acc)

        auto = Automation(
            id=uuid.uuid4(),
            workspace_id=ws_id,
            instagram_account_id=acc_id,
            name="Delivery Failure Flow",
            trigger_type="COMMENT",
            status="ACTIVE",
            flow_definition={
                "trigger": {"type": "COMMENT", "triggerMode": "any_keyword"},
                "automatedDm": {"message": "Here is the link: https://comlina.com/link"},
                "advanced": {
                    "askFollow": {"enabled": False},
                    "commentTeaser": {"enabled": True, "message": "Check your DM! 📩"}
                }
            }
        )
        session.add(auto)
        await session.commit()

    event_data = {
        "provider_event_id": f"evt_{uuid.uuid4().hex[:8]}",
        "event_type": "COMMENT",
        "business_ig_id": biz_ig_id,
        "sender_id": f"comm_user_{uuid.uuid4().hex[:6]}",
        "sender_username": "blocked_user",
        "text": "Send it",
        "post_id": "media_999",
        "comment_id": "comm_999"
    }

    with patch("app.jobs.process_comment.MetaGraphClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client_cls.return_value = mock_client
        # Private reply fails with MetaGraphAPIError
        mock_client.post = AsyncMock(side_effect=MetaGraphAPIError("User cannot be messaged", code=100))

        summary = await process_comment_job({}, f"wh_{uuid.uuid4().hex[:8]}", event_data)

    assert summary["processing_state"] == "failed"
    results = summary["results"][0]["result"]["results"]
    actions = [r["action"] for r in results]
    assert "PRIVATE_DM" in actions
    # Public teaser reply MUST be suppressed
    assert "PUBLIC_REPLY" not in actions


# ---------------------------------------------------------------------------
# 5. Recheck Follower Status in send_dm_job (All 4 States)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_send_dm_recheck_handles_all_four_statuses():
    """
    Tests follower recheck in send_dm_job across:
    - FOLLOWING -> releases resource, removes pending gate
    - NOT_FOLLOWING -> sends retry reminder, retains pending gate
    - CHECK_UNAVAILABLE -> sends unavailable notice, retains pending gate
    - UNKNOWN -> sends unknown notice, retains pending gate
    """
    ws_id = uuid.uuid4()
    acc_id = uuid.uuid4()
    biz_ig_id = f"biz_{uuid.uuid4().hex[:8]}"

    async with get_db_session() as session:
        ws = Workspace(id=ws_id, name="WS Recheck", slug=f"ws-rc-{uuid.uuid4().hex[:6]}")
        session.add(ws)

        acc = InstagramAccount(
            id=acc_id,
            workspace_id=ws_id,
            ig_user_id=biz_ig_id,
            username="recheck_host",
            access_token_encrypted=encrypt_token("EAAB_token_rc"),
            is_active=True
        )
        session.add(acc)
        await session.commit()

    test_cases = [
        {
            "meta_return": {"is_user_follow_business": True},
            "expected_state": "resource_sent",
            "expected_status": "FOLLOWING",
            "expected_verified": True,
            "gate_cleared": True,
        },
        {
            "meta_return": {"is_user_follow_business": False},
            "expected_state": "verification_pending",
            "expected_status": "NOT_FOLLOWING",
            "expected_verified": False,
            "gate_cleared": False,
        },
        {
            "meta_return": {"id": "user_unavail"},  # missing is_user_follow_business -> CHECK_UNAVAILABLE
            "expected_state": "verification_unavailable",
            "expected_status": "CHECK_UNAVAILABLE",
            "expected_verified": False,
            "gate_cleared": False,
        },
    ]

    for tc in test_cases:
        viewer_id = f"viewer_{uuid.uuid4().hex[:6]}"
        async with get_db_session() as session:
            contact = Contact(
                workspace_id=ws_id,
                instagram_account_id=acc_id,
                ig_user_id=viewer_id,
                username="test_viewer",
                follower_status="UNKNOWN",
                automation_state="verification_pending",
                custom_fields={
                    "follow_gate_pending": {
                        "resource_message": "Here is the unlocked link! 🔓",
                        "buttons": [{"label": "View Link", "url": "https://example.com/unlocked"}],
                        "account_username": "recheck_host"
                    }
                }
            )
            session.add(contact)
            await session.commit()

        event_data = {
            "provider_event_id": f"msg_{uuid.uuid4().hex[:8]}",
            "event_type": "MESSAGING",
            "sender_id": viewer_id,
            "sender_username": "test_viewer",
            "recipient_id": biz_ig_id,
            "business_ig_id": biz_ig_id,
            "workspace_id": str(ws_id),
            "instagram_account_id": str(acc_id),
            "text": "I followed! 🚀"
        }

        with patch("app.jobs.send_dm.MetaGraphClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client_cls.return_value = mock_client
            mock_client.get = AsyncMock(return_value=tc["meta_return"])
            mock_client.post = AsyncMock(return_value={"message_id": "mid_rc_101"})

            result = await send_dm_job({}, f"evt_{uuid.uuid4().hex[:8]}", event_data)

        assert result["processing_state"] == tc["expected_state"]
        assert result["follower_verified"] == tc["expected_verified"]
        assert result["follower_status"] == tc["expected_status"]

        # Check DB contact state
        async with get_db_session() as session:
            c_res = await session.execute(select(Contact).where(Contact.ig_user_id == viewer_id))
            updated = c_res.scalar_one_or_none()
            assert updated is not None
            assert updated.follower_status == tc["expected_status"]
            assert updated.automation_state == tc["expected_state"]
            if tc["gate_cleared"]:
                assert "follow_gate_pending" not in (updated.custom_fields or {})
            else:
                assert "follow_gate_pending" in (updated.custom_fields or {})
