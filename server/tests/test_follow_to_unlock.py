# server/tests/test_follow_to_unlock.py
import uuid
import pytest
from unittest.mock import AsyncMock, patch
from sqlalchemy import select

from app.core.database import init_db, get_db_session
from app.core.encryption import encrypt_token
from app.engine.flow_engine import FlowEngine
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
    WebhookEvent,
    AnalyticsEvent
)

@pytest.fixture(autouse=True)
async def setup_db():
    await init_db()

@pytest.mark.asyncio
async def test_scenario_1_existing_follower_receives_resource():
    """
    Scenario 1: Existing follower receives the requested link via DM.
    - Ask to follow message is NOT sent.
    - Protected resource DM is sent.
    - Public teaser reply 'Check your DM! 📩' is sent after successful DM.
    - State is resource_sent / teaser_reply_sent.
    """
    ws_id = uuid.uuid4()
    acc_id = uuid.uuid4()
    biz_ig_id = f"biz_{uuid.uuid4().hex[:8]}"

    async with get_db_session() as session:
        ws = Workspace(id=ws_id, name="Test WS 1", slug=f"ws1-{uuid.uuid4().hex[:6]}")
        session.add(ws)

        acc = InstagramAccount(
            id=acc_id,
            workspace_id=ws_id,
            ig_user_id=biz_ig_id,
            username="creator_brand",
            access_token_encrypted=encrypt_token("EAAB_valid_token_1"),
            is_active=True
        )
        session.add(acc)

        auto = Automation(
            id=uuid.uuid4(),
            workspace_id=ws_id,
            instagram_account_id=acc_id,
            name="Follower Unlock Flow",
            trigger_type="COMMENT",
            status="ACTIVE",
            flow_definition={
                "trigger": {
                    "type": "COMMENT",
                    "triggerMode": "specific_keywords",
                    "keywords": ["GUIDE"],
                    "matchWholeWords": True,
                    "matchBehavior": "contains"
                },
                "automatedDm": {
                    "message": "Here is your exclusive guide! 🎁",
                    "button": {
                        "label": "Download Guide",
                        "url": "https://example.com/guide.pdf"
                    }
                },
                "advanced": {
                    "askFollow": {
                        "enabled": True,
                        "message": "Please follow @creator_brand to unlock this resource!"
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

    commenter_id = f"commenter_{uuid.uuid4().hex[:6]}"
    event_data = {
        "provider_event_id": f"evt_{uuid.uuid4().hex[:8]}",
        "event_type": "COMMENT",
        "business_ig_id": biz_ig_id,
        "sender_id": commenter_id,
        "sender_username": "loyal_follower",
        "text": "Please send me the GUIDE!",
        "post_id": "media_post_100",
        "comment_id": "comm_100"
    }

    # Mock Meta client so follower check returns True (follower confirmed)
    with patch("app.jobs.process_comment.MetaGraphClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client_cls.return_value = mock_client
        # GET on commenter_id returns is_user_follow_business = True
        mock_client.get = AsyncMock(return_value={"id": commenter_id, "is_user_follow_business": True})
        # POST for private reply and comment reply succeeds
        mock_client.post = AsyncMock(return_value={"message_id": "mid_dm_101", "id": "rep_101"})

        summary = await process_comment_job({}, f"wh_{uuid.uuid4().hex[:8]}", event_data)

    assert summary["status"] == "COMPLETED"
    assert summary["automations_matched"] == 1
    assert summary["processing_state"] in ("resource_sent", "teaser_reply_sent")
    assert summary["follower_verified"] is True

    # Verify results contain the private DM with resource and the public teaser
    results = summary["results"][0]["result"]["results"]
    actions = [r["action"] for r in results]
    assert "PRIVATE_DM" in actions
    assert "PUBLIC_REPLY" in actions

    # Verify protected resource was sent, NOT the follow gate
    dm_res = next(r for r in results if r["action"] == "PRIVATE_DM")
    assert "exclusive guide" in dm_res["text"]
    assert "Please follow" not in dm_res["text"]

    # Verify teaser reply text is exactly 'Check your DM! 📩'
    teaser_res = next(r for r in results if r["action"] == "PUBLIC_REPLY")
    assert teaser_res["text"] == "Check your DM! 📩"


@pytest.mark.asyncio
async def test_scenario_2_non_follower_receives_follow_request_not_resource():
    """
    Scenario 2: Non-follower receives the follow request but NOT the protected link.
    - Creator's profile link and Follow button are included.
    - Resource is withheld.
    - Pending follow state is saved on contact for recheck.
    - Teaser reply is sent.
    """
    ws_id = uuid.uuid4()
    acc_id = uuid.uuid4()
    biz_ig_id = f"biz_{uuid.uuid4().hex[:8]}"

    async with get_db_session() as session:
        ws = Workspace(id=ws_id, name="Test WS 2", slug=f"ws2-{uuid.uuid4().hex[:6]}")
        session.add(ws)

        acc = InstagramAccount(
            id=acc_id,
            workspace_id=ws_id,
            ig_user_id=biz_ig_id,
            username="cool_creator",
            access_token_encrypted=encrypt_token("EAAB_valid_token_2"),
            is_active=True
        )
        session.add(acc)

        auto = Automation(
            id=uuid.uuid4(),
            workspace_id=ws_id,
            instagram_account_id=acc_id,
            name="Follow Gate Flow",
            trigger_type="COMMENT",
            status="ACTIVE",
            flow_definition={
                "trigger": {
                    "type": "COMMENT",
                    "triggerMode": "any_keyword"
                },
                "automatedDm": {
                    "message": "Here is the super secret template! 🔥",
                    "button": {
                        "label": "Open Template",
                        "url": "https://example.com/template"
                    }
                },
                "advanced": {
                    "askFollow": {
                        "enabled": True,
                        "message": "Thanks for commenting! Please follow @cool_creator first to unlock this link 🚀"
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

    commenter_id = f"commenter_{uuid.uuid4().hex[:6]}"
    event_data = {
        "provider_event_id": f"evt_{uuid.uuid4().hex[:8]}",
        "event_type": "COMMENT",
        "business_ig_id": biz_ig_id,
        "sender_id": commenter_id,
        "sender_username": "new_visitor",
        "text": "Love this, send it over!",
        "post_id": "media_post_200",
        "comment_id": "comm_200"
    }

    # Mock Meta client: commenter does NOT follow (is_user_follow_business = False)
    with patch("app.jobs.process_comment.MetaGraphClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client_cls.return_value = mock_client
        mock_client.get = AsyncMock(return_value={"id": commenter_id, "is_user_follow_business": False})
        mock_client.post = AsyncMock(return_value={"message_id": "mid_gate_201", "id": "rep_201"})

        summary = await process_comment_job({}, f"wh_{uuid.uuid4().hex[:8]}", event_data)

    assert summary["status"] == "COMPLETED"
    assert summary["automations_matched"] == 1
    assert summary["processing_state"] == "verification_pending"
    assert summary["follower_verified"] is False

    results = summary["results"][0]["result"]["results"]
    dm_res = next(r for r in results if r["action"] == "PRIVATE_DM")
    # Follow request message sent
    assert "Please follow @cool_creator" in dm_res["text"]
    # Protected link is withheld!
    assert "secret template" not in dm_res["text"]
    # Buttons include profile link
    button_urls = [b.get("url") for b in dm_res.get("buttons", []) if b.get("url")]
    assert "https://instagram.com/cool_creator" in button_urls

    # Check contact record in DB has pending follow gate
    async with get_db_session() as session:
        c_res = await session.execute(select(Contact).where(Contact.ig_user_id == commenter_id))
        contact = c_res.scalar_one_or_none()
        assert contact is not None
        assert contact.automation_state == "verification_pending"
        assert "follow_gate_pending" in contact.custom_fields
        assert "secret template" in contact.custom_fields["follow_gate_pending"]["resource_message"]


@pytest.mark.asyncio
async def test_scenario_3_user_follows_after_request_and_verified():
    """
    Scenario 3: User follows after the request and eligibility is subsequently verified.
    - User has follow_gate_pending.
    - User sends DM / taps quick reply -> MESSAGING webhook arrives.
    - Meta API recheck returns is_user_follow_business = True.
    - State transitions: follow_verified -> eligible_for_delivery -> resource_sent.
    - Protected resource is delivered and pending gate is removed.
    """
    ws_id = uuid.uuid4()
    acc_id = uuid.uuid4()
    biz_ig_id = f"biz_{uuid.uuid4().hex[:8]}"
    viewer_id = f"user_{uuid.uuid4().hex[:6]}"

    async with get_db_session() as session:
        ws = Workspace(id=ws_id, name="Test WS 3", slug=f"ws3-{uuid.uuid4().hex[:6]}")
        session.add(ws)

        acc = InstagramAccount(
            id=acc_id,
            workspace_id=ws_id,
            ig_user_id=biz_ig_id,
            username="verified_host",
            access_token_encrypted=encrypt_token("EAAB_valid_token_3"),
            is_active=True
        )
        session.add(acc)

        contact = Contact(
            workspace_id=ws_id,
            instagram_account_id=acc_id,
            ig_user_id=viewer_id,
            username="converted_user",
            follower_status="NOT_FOLLOWING",
            automation_state="verification_pending",
            custom_fields={
                "follow_gate_pending": {
                    "resource_message": "Unlocked: Here is the VIP resource link! 🔓",
                    "buttons": [{"label": "Access VIP", "url": "https://example.com/vip"}],
                    "account_username": "verified_host"
                }
            }
        )
        session.add(contact)
        await session.commit()

    event_data = {
        "provider_event_id": f"msg_evt_{uuid.uuid4().hex[:8]}",
        "event_type": "MESSAGING",
        "sender_id": viewer_id,
        "sender_username": "converted_user",
        "recipient_id": biz_ig_id,
        "business_ig_id": biz_ig_id,
        "workspace_id": str(ws_id),
        "instagram_account_id": str(acc_id),
        "text": "I followed! 🚀"
    }

    # Mock Meta client: now recheck returns is_user_follow_business = True!
    with patch("app.jobs.send_dm.MetaGraphClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client_cls.return_value = mock_client
        mock_client.get = AsyncMock(return_value={"id": viewer_id, "is_user_follow_business": True})
        mock_client.post = AsyncMock(return_value={"message_id": "mid_vip_301"})

        result = await send_dm_job({}, f"evt_{uuid.uuid4().hex[:8]}", event_data)

    assert result["processing_state"] == "resource_sent"
    assert result["follower_verified"] is True

    # Verify contact in DB was updated and unlocked
    async with get_db_session() as session:
        c_res = await session.execute(select(Contact).where(Contact.ig_user_id == viewer_id))
        updated_contact = c_res.scalar_one_or_none()
        assert updated_contact is not None
        assert updated_contact.follower_status == "FOLLOWING"
        assert updated_contact.automation_state == "resource_sent"
        assert "follow_gate_pending" not in updated_contact.custom_fields

        # Verify BOT message was saved with unlocked VIP resource
        m_res = await session.execute(select(Message).where(Message.sender_type == "BOT"))
        bot_msgs = list(m_res.scalars().all())
        assert any("VIP resource link" in m.text for m in bot_msgs)


@pytest.mark.asyncio
async def test_scenario_4_follow_verification_unavailable():
    """
    Scenario 4: Follow verification is unavailable (Graph error / missing messaging consent).
    - Status degrades gracefully to CHECK_UNAVAILABLE.
    - State is verification_unavailable / verification_pending.
    - Protected resource is NOT released.
    - Follow gate DM is sent.
    """
    ws_id = uuid.uuid4()
    acc_id = uuid.uuid4()
    biz_ig_id = f"biz_{uuid.uuid4().hex[:8]}"

    async with get_db_session() as session:
        ws = Workspace(id=ws_id, name="Test WS 4", slug=f"ws4-{uuid.uuid4().hex[:6]}")
        session.add(ws)

        acc = InstagramAccount(
            id=acc_id,
            workspace_id=ws_id,
            ig_user_id=biz_ig_id,
            username="pro_creator",
            access_token_encrypted=encrypt_token("EAAB_token_4"),
            is_active=True
        )
        session.add(acc)

        auto = Automation(
            id=uuid.uuid4(),
            workspace_id=ws_id,
            instagram_account_id=acc_id,
            name="Protected Flow",
            trigger_type="COMMENT",
            status="ACTIVE",
            flow_definition={
                "trigger": {"type": "COMMENT", "triggerMode": "any_keyword"},
                "automatedDm": {"message": "Protected resource: https://secret.link"},
                "advanced": {
                    "askFollow": {"enabled": True, "message": "Follow @pro_creator to unlock!"},
                    "commentTeaser": {"enabled": True, "message": "Check your DM! 📩"}
                }
            }
        )
        session.add(auto)
        await session.commit()

    commenter_id = f"commenter_{uuid.uuid4().hex[:6]}"
    event_data = {
        "provider_event_id": f"evt_{uuid.uuid4().hex[:8]}",
        "event_type": "COMMENT",
        "business_ig_id": biz_ig_id,
        "sender_id": commenter_id,
        "sender_username": "new_commenter",
        "text": "Link please",
        "post_id": "media_400",
        "comment_id": "comm_400"
    }

    with patch("app.jobs.process_comment.MetaGraphClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client_cls.return_value = mock_client
        # Meta returns Graph API error (e.g. consent missing on comment-only user)
        mock_client.get = AsyncMock(side_effect=MetaGraphAPIError("Requires user messaging consent"))
        mock_client.post = AsyncMock(return_value={"message_id": "mid_gate_401", "id": "rep_401"})

        summary = await process_comment_job({}, f"wh_{uuid.uuid4().hex[:8]}", event_data)

    assert summary["status"] == "COMPLETED"
    assert summary["follower_verified"] is False
    assert summary["processing_state"] == "verification_pending"

    # Verify protected link was withheld
    results = summary["results"][0]["result"]["results"]
    dm_res = next(r for r in results if r["action"] == "PRIVATE_DM")
    assert "https://secret.link" not in dm_res["text"]
    assert "Follow @pro_creator" in dm_res["text"]


@pytest.mark.asyncio
async def test_scenario_5_dm_delivery_fails_suppresses_teaser():
    """
    Scenario 5: DM delivery fails.
    - Public teaser reply must NOT be sent (do not falsely tell user to check DM!).
    - State is recorded as failed.
    """
    ws_id = uuid.uuid4()
    acc_id = uuid.uuid4()
    biz_ig_id = f"biz_{uuid.uuid4().hex[:8]}"

    async with get_db_session() as session:
        ws = Workspace(id=ws_id, name="Test WS 5", slug=f"ws5-{uuid.uuid4().hex[:6]}")
        session.add(ws)

        acc = InstagramAccount(
            id=acc_id,
            workspace_id=ws_id,
            ig_user_id=biz_ig_id,
            username="failing_dm_creator",
            access_token_encrypted=encrypt_token("EAAB_token_5"),
            is_active=True
        )
        session.add(acc)

        auto = Automation(
            id=uuid.uuid4(),
            workspace_id=ws_id,
            instagram_account_id=acc_id,
            name="DM Fail Test",
            trigger_type="COMMENT",
            status="ACTIVE",
            flow_definition={
                "trigger": {"type": "COMMENT", "triggerMode": "any_keyword"},
                "automatedDm": {"message": "Here is your link!"},
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
        "sender_id": f"commenter_{uuid.uuid4().hex[:6]}",
        "sender_username": "recipient_user",
        "text": "Send it",
        "post_id": "media_500",
        "comment_id": "comm_500"
    }

    with patch("app.jobs.process_comment.MetaGraphClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client_cls.return_value = mock_client
        # DM delivery throws an error (e.g. messaging window closed or user blocked)
        mock_client.post = AsyncMock(side_effect=MetaGraphAPIError("Cannot message recipient"))

        summary = await process_comment_job({}, f"wh_{uuid.uuid4().hex[:8]}", event_data)

    assert summary["processing_state"] == "failed"
    results = summary["results"][0]["result"]["results"]
    actions = [r["action"] for r in results]
    # PUBLIC_REPLY must NOT be present!
    assert "PUBLIC_REPLY" not in actions


@pytest.mark.asyncio
async def test_scenario_6_public_teaser_reply_fails_gracefully():
    """
    Scenario 6: Public teaser reply fails (e.g. comment deleted or rate limited).
    - DM delivery succeeded.
    - System tracks teaser failure separately and does not crash.
    """
    ws_id = uuid.uuid4()
    acc_id = uuid.uuid4()
    biz_ig_id = f"biz_{uuid.uuid4().hex[:8]}"

    async with get_db_session() as session:
        ws = Workspace(id=ws_id, name="Test WS 6", slug=f"ws6-{uuid.uuid4().hex[:6]}")
        session.add(ws)

        acc = InstagramAccount(
            id=acc_id,
            workspace_id=ws_id,
            ig_user_id=biz_ig_id,
            username="teaser_fail_creator",
            access_token_encrypted=encrypt_token("EAAB_token_6"),
            is_active=True
        )
        session.add(acc)

        auto = Automation(
            id=uuid.uuid4(),
            workspace_id=ws_id,
            instagram_account_id=acc_id,
            name="Teaser Fail Test",
            trigger_type="COMMENT",
            status="ACTIVE",
            flow_definition={
                "trigger": {"type": "COMMENT", "triggerMode": "any_keyword"},
                "automatedDm": {"message": "Here is the download link!"},
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
        "sender_id": f"commenter_{uuid.uuid4().hex[:6]}",
        "sender_username": "teaser_user",
        "text": "Link me",
        "post_id": "media_600",
        "comment_id": "comm_600"
    }

    with patch("app.jobs.process_comment.MetaGraphClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client_cls.return_value = mock_client
        # DM succeeds, but comment reply fails with MetaGraphAPIError
        async def mock_post(endpoint, json_data=None):
            if "replies" in endpoint:
                raise MetaGraphAPIError("Comment was deleted")
            return {"message_id": "mid_dm_601"}
        mock_client.post = AsyncMock(side_effect=mock_post)

        summary = await process_comment_job({}, f"wh_{uuid.uuid4().hex[:8]}", event_data)

    assert summary["status"] == "COMPLETED"
    assert summary["processing_state"] == "resource_sent"
    results = summary["results"][0]["result"]["results"]
    dm_res = next(r for r in results if r["action"] == "PRIVATE_DM")
    assert dm_res["status"] == "SUCCESS"
    teaser_res = next(r for r in results if r["action"] == "PUBLIC_REPLY")
    assert teaser_res["status"] == "FAILED"


@pytest.mark.asyncio
async def test_scenario_7_duplicate_webhook_events_idempotency():
    """
    Scenario 7: Duplicate webhook events arrive.
    - Idempotency key provider_event_id prevents second event from running.
    """
    from app.api.webhooks import _insert_webhook_event_idempotent

    ws_id = uuid.uuid4()
    acc_id = uuid.uuid4()
    provider_id = f"dup_event_{uuid.uuid4().hex[:8]}"

    async with get_db_session() as session:
        # First insertion succeeds
        id1 = await _insert_webhook_event_idempotent(
            session, ws_id, acc_id, provider_id, "COMMENT", {"test": 1}
        )
        await session.commit()
        assert id1 is not None

        # Second duplicate insertion with identical provider_id returns None
        id2 = await _insert_webhook_event_idempotent(
            session, ws_id, acc_id, provider_id, "COMMENT", {"test": 1}
        )
        assert id2 is None


@pytest.mark.asyncio
async def test_scenario_8_two_different_commenters_trigger_same_automation():
    """
    Scenario 8: Two different commenters trigger the same automation.
    - Commenter A is an existing follower -> receives resource.
    - Commenter B is a non-follower -> receives follow gate.
    - Separate contacts and states are tracked independently.
    """
    ws_id = uuid.uuid4()
    acc_id = uuid.uuid4()
    biz_ig_id = f"biz_{uuid.uuid4().hex[:8]}"

    async with get_db_session() as session:
        ws = Workspace(id=ws_id, name="Test WS 8", slug=f"ws8-{uuid.uuid4().hex[:6]}")
        session.add(ws)

        acc = InstagramAccount(
            id=acc_id,
            workspace_id=ws_id,
            ig_user_id=biz_ig_id,
            username="multi_creator",
            access_token_encrypted=encrypt_token("EAAB_token_8"),
            is_active=True
        )
        session.add(acc)

        auto = Automation(
            id=uuid.uuid4(),
            workspace_id=ws_id,
            instagram_account_id=acc_id,
            name="Multi User Flow",
            trigger_type="COMMENT",
            status="ACTIVE",
            flow_definition={
                "trigger": {"type": "COMMENT", "triggerMode": "any_keyword"},
                "automatedDm": {"message": "Here is the resource link: https://example.com/res"},
                "advanced": {
                    "askFollow": {"enabled": True, "message": "Follow @multi_creator to unlock!"},
                    "commentTeaser": {"enabled": True, "message": "Check your DM! 📩"}
                }
            }
        )
        session.add(auto)
        await session.commit()

    id_a = f"commenter_A_{uuid.uuid4().hex[:6]}"
    id_b = f"commenter_B_{uuid.uuid4().hex[:6]}"

    with patch("app.jobs.process_comment.MetaGraphClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client_cls.return_value = mock_client

        # User A follows, User B does not follow
        async def mock_get(endpoint, params=None):
            if id_a in endpoint:
                return {"id": id_a, "is_user_follow_business": True}
            return {"id": id_b, "is_user_follow_business": False}

        mock_client.get = AsyncMock(side_effect=mock_get)
        mock_client.post = AsyncMock(return_value={"message_id": "mid_888"})

        # Process Commenter A
        evt_a = {
            "provider_event_id": f"evt_a_{uuid.uuid4().hex[:8]}",
            "event_type": "COMMENT",
            "business_ig_id": biz_ig_id,
            "sender_id": id_a,
            "sender_username": "user_a",
            "text": "Send please!",
            "comment_id": "comm_a"
        }
        res_a = await process_comment_job({}, f"wh_a_{uuid.uuid4().hex[:6]}", evt_a)
        assert res_a["follower_verified"] is True
        assert res_a["processing_state"] in ("resource_sent", "teaser_reply_sent")

        # Process Commenter B
        evt_b = {
            "provider_event_id": f"evt_b_{uuid.uuid4().hex[:8]}",
            "event_type": "COMMENT",
            "business_ig_id": biz_ig_id,
            "sender_id": id_b,
            "sender_username": "user_b",
            "text": "Send please!",
            "comment_id": "comm_b"
        }
        res_b = await process_comment_job({}, f"wh_b_{uuid.uuid4().hex[:6]}", evt_b)
        assert res_b["follower_verified"] is False
        assert res_b["processing_state"] == "verification_pending"

    # Verify both contacts exist in DB with separate statuses
    async with get_db_session() as session:
        c_a = (await session.execute(select(Contact).where(Contact.ig_user_id == id_a))).scalar_one_or_none()
        c_b = (await session.execute(select(Contact).where(Contact.ig_user_id == id_b))).scalar_one_or_none()
        assert c_a.follower_status == "FOLLOWING"
        assert c_b.follower_status in ("NOT_FOLLOWING", "UNKNOWN")
        assert "follow_gate_pending" in c_b.custom_fields
        assert "follow_gate_pending" not in (c_a.custom_fields or {})


@pytest.mark.asyncio
async def test_scenario_9_disconnected_or_revoked_instagram_account():
    """
    Scenario 9: Instagram account has been disconnected (is_active=False) or not found.
    - Automation does NOT execute.
    - Webhook status is marked IGNORED.
    """
    ws_id = uuid.uuid4()
    acc_id = uuid.uuid4()
    biz_ig_id = f"biz_inactive_{uuid.uuid4().hex[:8]}"

    async with get_db_session() as session:
        ws = Workspace(id=ws_id, name="Test WS 9", slug=f"ws9-{uuid.uuid4().hex[:6]}")
        session.add(ws)

        acc = InstagramAccount(
            id=acc_id,
            workspace_id=ws_id,
            ig_user_id=biz_ig_id,
            username="disconnected_account",
            access_token_encrypted=encrypt_token("EAAB_revoked_token"),
            is_active=False  # Disconnected
        )
        session.add(acc)
        await session.commit()

    event_data = {
        "provider_event_id": f"evt_{uuid.uuid4().hex[:8]}",
        "event_type": "COMMENT",
        "business_ig_id": biz_ig_id,
        "sender_id": "commenter_9",
        "text": "Hello"
    }

    summary = await process_comment_job({}, f"wh_9_{uuid.uuid4().hex[:6]}", event_data)
    assert summary["status"] == "IGNORED"
    assert summary["automations_matched"] == 0


@pytest.mark.asyncio
async def test_scenario_10_meta_rate_limits_safely_handled():
    """
    Scenario 10: Meta rate limits during follower check.
    - Raises MetaRateLimitError.
    - InstagramFollowerService returns FollowerStatus.CHECK_UNAVAILABLE.
    - Safe degradation without crashing or invent fake follow status.
    """
    mock_client = AsyncMock()
    mock_client.get = AsyncMock(side_effect=MetaRateLimitError("Meta Rate limit 613: Calls exceeded"))

    service = InstagramFollowerService(mock_client)
    status, reason = await service.check_follower_status("biz_123", "sender_456")

    assert status == FollowerStatus.CHECK_UNAVAILABLE
    assert "Rate Limit" in reason
