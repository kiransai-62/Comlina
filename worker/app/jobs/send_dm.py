# worker/app/jobs/send_dm.py
import uuid
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Union
from sqlalchemy import select

from app.core.database import get_db_session
from app.core.encryption import decrypt_token
from app.core.logging import log_diagnostic_event
from app.engine.flow_engine import FlowEngine
from app.integrations.instagram.client import MetaGraphClient
from app.integrations.instagram.messaging import InstagramMessaging
from app.models import (
    InstagramAccount,
    Automation,
    Contact,
    Conversation,
    Message,
    WebhookEvent,
    AnalyticsEvent
)

logger = logging.getLogger("send_dm")

async def _update_webhook_event(session, event_id: str, provider_id: Optional[str], status: str, error: Optional[str] = None):
    webhook_event = None
    try:
        stmt_wh = select(WebhookEvent).where(WebhookEvent.id == uuid.UUID(event_id))
        res_wh = await session.execute(stmt_wh)
        webhook_event = res_wh.scalar_one_or_none()
    except (ValueError, Exception):
        pass

    if not webhook_event and provider_id:
        stmt_wh = select(WebhookEvent).where(WebhookEvent.provider_event_id == provider_id)
        res_wh = await session.execute(stmt_wh)
        webhook_event = res_wh.scalar_one_or_none()

    if webhook_event:
        webhook_event.status = status
        if error is not None:
            webhook_event.error = error
        webhook_event.processed_at = datetime.now(timezone.utc)


async def send_dm_job(
    ctx: Dict[str, Any],
    event_id_or_recipient: str,
    event_data_or_text: Union[Dict[str, Any], str]
) -> Dict[str, Any]:
    """
    Job handler supporting:
    1. Direct message dispatch: send_dm_job(ctx, recipient_id, message_text)
    2. MESSAGING webhook event pipeline: send_dm_job(ctx, event_id, event_data)
       - Upserts Contact (sets is_converted=True, refreshes last_interaction_at to open 24h window)
       - Upserts Conversation (status="OPEN", unread_count incremented)
       - Stores incoming message (sender_type="CONTACT")
       - Runs active DM automations (e.g. DM_REPLY)
       - Records BOT response message and updates stats
       - Updates WebhookEvent status to PROCESSED
    """
    if isinstance(event_data_or_text, str):
        recipient_id = event_id_or_recipient
        text = event_data_or_text
        logger.info(f"Dispatched direct DM to recipient {recipient_id}: {text[:40]}...")
        return {"status": "DELIVERED", "recipient_id": recipient_id}

    event_id = event_id_or_recipient
    event_data = event_data_or_text
    logger.info(f"Worker processing messaging webhook job: event_id={event_id}")

    execution_summary: Dict[str, Any] = {
        "event_id": event_id,
        "automations_matched": 0,
        "actions_executed": 0,
        "status": "COMPLETED",
        "results": []
    }

    async with get_db_session() as session:
        try:
            sender_id: Optional[str] = str(event_data["sender_id"]) if event_data.get("sender_id") is not None else None
            recipient_id = event_data.get("recipient_id") or event_data.get("business_ig_id")
            incoming_text = event_data.get("text", "")
            sender_username = event_data.get("sender_username", "unknown")
            provider_event_id = event_data.get("provider_event_id")

            # 1. Resolve InstagramAccount
            account = None
            if recipient_id:
                stmt_acc = select(InstagramAccount).where(
                    InstagramAccount.ig_user_id == str(recipient_id),
                    InstagramAccount.is_active == True
                )
                if event_data.get("workspace_id"):
                    try:
                        stmt_acc = stmt_acc.where(InstagramAccount.workspace_id == uuid.UUID(str(event_data.get("workspace_id"))))
                    except Exception:
                        pass
                res_acc = await session.execute(stmt_acc)
                account = res_acc.scalars().first()

            if not account and event_data.get("instagram_account_id"):
                try:
                    stmt_acc = select(InstagramAccount).where(
                        InstagramAccount.id == uuid.UUID(str(event_data.get("instagram_account_id"))),
                        InstagramAccount.is_active == True
                    )
                    res_acc = await session.execute(stmt_acc)
                    account = res_acc.scalars().first()
                except Exception:
                    pass

            if not account:
                logger.warning(f"No active InstagramAccount found for recipient_id={recipient_id}")
                execution_summary["status"] = "IGNORED"
                execution_summary["reason"] = "ACCOUNT_NOT_FOUND"
                log_diagnostic_event(
                    stage="job_processed",
                    correlation_id=provider_event_id or event_id,
                    event_type="MESSAGING",
                    error_code="ACCOUNT_NOT_FOUND",
                    details={"status": "IGNORED", "reason": "ACCOUNT_NOT_FOUND"}
                )
                await _update_webhook_event(session, event_id, provider_event_id, "IGNORED", "Instagram account not found")
                return execution_summary

            # Defense-in-depth: Skip self-event if sender is the business account itself
            if sender_id and account and sender_id == account.ig_user_id:
                logger.info(f"Skipping self-event for account {account.id} (sender_id == ig_user_id == {sender_id})")
                execution_summary["status"] = "SKIPPED_SELF_EVENT"
                execution_summary["reason"] = "SELF_EVENT_SKIPPED"
                log_diagnostic_event(
                    stage="job_processed",
                    correlation_id=provider_event_id or event_id,
                    event_type="MESSAGING",
                    workspace_id=str(account.workspace_id),
                    account_id=str(account.id),
                    details={"status": "SKIPPED_SELF_EVENT"}
                )
                await _update_webhook_event(session, event_id, provider_event_id, "PROCESSED", "Self-event skipped")
                return execution_summary

            meta_client = None
            try:
                decrypted_token = decrypt_token(account.access_token_encrypted)
                meta_client = MetaGraphClient(decrypted_token)
            except Exception as e:
                logger.warning(f"Failed to decrypt token for account {account.id}: {e}")

            # 2. Upsert Contact: mark is_converted = True and refresh last_interaction_at (opens 24h reply window)
            contact = None
            if sender_id:
                stmt_contact = select(Contact).where(
                    Contact.workspace_id == account.workspace_id,
                    Contact.instagram_account_id == account.id,
                    Contact.ig_user_id == sender_id
                )
                res_contact = await session.execute(stmt_contact)
                contact = res_contact.scalar_one_or_none()

                if not contact:
                    contact = Contact(
                        workspace_id=account.workspace_id,
                        instagram_account_id=account.id,
                        ig_user_id=sender_id,
                        username=sender_username,
                        is_converted=True,
                        interaction_count=1,
                        tags=["lead", "dm"],
                        last_interaction_at=datetime.now(timezone.utc)
                    )
                    session.add(contact)
                    await session.flush()
                else:
                    contact.is_converted = True
                    contact.interaction_count = (contact.interaction_count or 0) + 1
                    contact.last_interaction_at = datetime.now(timezone.utc)
                    if sender_username and sender_username != "unknown":
                        contact.username = sender_username
                    current_tags = list(contact.tags) if isinstance(contact.tags, list) else []
                    if "dm" not in current_tags:
                        current_tags.append("dm")
                        contact.tags = current_tags
                    await session.flush()

            # 3. Upsert Conversation (status = "OPEN")
            conversation = None
            if contact:
                stmt_conv = select(Conversation).where(
                    Conversation.workspace_id == account.workspace_id,
                    Conversation.instagram_account_id == account.id,
                    Conversation.contact_id == contact.id
                )
                res_conv = await session.execute(stmt_conv)
                conversation = res_conv.scalar_one_or_none()

                if not conversation:
                    conversation = Conversation(
                        workspace_id=account.workspace_id,
                        instagram_account_id=account.id,
                        contact_id=contact.id,
                        status="OPEN",
                        last_message_text=incoming_text,
                        last_message_at=datetime.now(timezone.utc),
                        unread_count=1
                    )
                    session.add(conversation)
                    await session.flush()
                else:
                    conversation.status = "OPEN"
                    conversation.last_message_text = incoming_text
                    conversation.last_message_at = datetime.now(timezone.utc)
                    conversation.unread_count = (conversation.unread_count or 0) + 1
                    await session.flush()

                # 4. Store incoming message from viewer (sender_type="CONTACT") with deduplication
                is_duplicate = False
                if provider_event_id:
                    stmt_dup = select(Message.id).where(
                        Message.conversation_id == conversation.id,
                        Message.meta_message_id == provider_event_id
                    )
                    res_dup = await session.execute(stmt_dup)
                    if res_dup.scalar_one_or_none():
                        is_duplicate = True

                if not is_duplicate:
                    contact_msg = Message(
                        workspace_id=account.workspace_id,
                        conversation_id=conversation.id,
                        sender_type="CONTACT",
                        text=incoming_text,
                        meta_message_id=provider_event_id,
                        created_at=datetime.now(timezone.utc)
                    )
                    session.add(contact_msg)
                    await session.flush()

                # 4.5 Follow-to-Unlock Recheck Pipeline
                custom_fields = dict(contact.custom_fields) if isinstance(contact.custom_fields, dict) else {}
                pending_follow = custom_fields.get("follow_gate_pending")

                if pending_follow and meta_client:
                    sender_ig_id: str = sender_id or contact.ig_user_id
                    logger.info(f"Rechecking follow status for contact {contact.id} (sender_id={sender_ig_id})...")
                    from app.integrations.instagram.follower_status import InstagramFollowerService, FollowerStatus
                    follower_service = InstagramFollowerService(meta_client)
                    status_enum, reason = await follower_service.check_follower_status(account.ig_user_id, sender_ig_id)
                    logger.info(f"Follow recheck result for {sender_ig_id}: {status_enum.value} ({reason})")

                    if status_enum == FollowerStatus.FOLLOWING:
                        # Confirmed! Advance states: follow_verified -> eligible_for_delivery -> resource_sent
                        contact.follower_status = "FOLLOWING"
                        contact.automation_state = "eligible_for_delivery"

                        resource_text = pending_follow.get("resource_message") or ""
                        buttons = pending_follow.get("buttons") or []
                        auto_id_val = None
                        if pending_follow.get("automation_id"):
                            try:
                                auto_id_val = uuid.UUID(str(pending_follow.get("automation_id")))
                            except (ValueError, TypeError):
                                pass

                        messaging_client = InstagramMessaging(meta_client)
                        delivery_res = await messaging_client.send_direct_message(
                            ig_recipient_id=sender_ig_id,
                            message_text=resource_text,
                            buttons=buttons
                        )

                        contact.automation_state = "resource_sent"
                        del custom_fields["follow_gate_pending"]
                        contact.custom_fields = custom_fields

                        tags = list(contact.tags) if isinstance(contact.tags, list) else []
                        if "follow_verified" not in tags:
                            tags.append("follow_verified")
                        contact.tags = tags

                        meta_msg_id = delivery_res.get("message_id") if isinstance(delivery_res, dict) else None
                        bot_msg = Message(
                            workspace_id=account.workspace_id,
                            conversation_id=conversation.id,
                            sender_type="BOT",
                            text=resource_text,
                            meta_message_id=meta_msg_id,
                            automation_id=auto_id_val,
                            created_at=datetime.now(timezone.utc)
                        )
                        session.add(bot_msg)

                        recheck_analytics = AnalyticsEvent(
                            workspace_id=account.workspace_id,
                            instagram_account_id=account.id,
                            contact_id=contact.id,
                            automation_id=auto_id_val,
                            event_type="FOLLOW_VERIFIED_RESOURCE_SENT",
                            metadata_={
                                "processing_state": "resource_sent",
                                "verified": True,
                                "sender_id": sender_ig_id,
                                "reason": reason
                            },
                            created_at=datetime.now(timezone.utc)
                        )
                        session.add(recheck_analytics)
                        execution_summary["actions_executed"] += 1
                        execution_summary["processing_state"] = "resource_sent"
                        execution_summary["follower_verified"] = True

                        await _update_webhook_event(session, event_id, provider_event_id, "PROCESSED")
                        await session.commit()
                        return execution_summary

                    elif status_enum == FollowerStatus.NOT_FOLLOWING:
                        # User still does NOT follow! Send reminder, do not release resource
                        contact.follower_status = "NOT_FOLLOWING"
                        contact.automation_state = "verification_pending"

                        account_username = pending_follow.get("account_username") or account.username
                        retry_text = (
                            pending_follow.get("retry_message")
                            or f"We couldn't confirm your follow yet! Please make sure to follow @{account_username} and tap below 🚀"
                        )
                        retry_buttons = [
                            {"label": f"Follow @{account_username}"[:20], "url": f"https://instagram.com/{account_username}"},
                            {"label": "I followed! 🚀"[:20], "payload": "VERIFY_FOLLOW"}
                        ]
                        messaging_client = InstagramMessaging(meta_client)
                        await messaging_client.send_direct_message(
                            ig_recipient_id=sender_ig_id,
                            message_text=retry_text,
                            buttons=retry_buttons
                        )
                        execution_summary["processing_state"] = "verification_pending"
                        execution_summary["follower_verified"] = False
                        execution_summary["actions_executed"] += 1

                        await _update_webhook_event(session, event_id, provider_event_id, "PROCESSED")
                        await session.commit()
                        return execution_summary

                    else:  # CHECK_UNAVAILABLE
                        contact.automation_state = "verification_unavailable"
                        unavail_text = "Instagram follow verification is temporarily unavailable. Please tap 'I followed! 🚀' again in a moment."
                        messaging_client = InstagramMessaging(meta_client)
                        await messaging_client.send_direct_message(
                            ig_recipient_id=sender_ig_id,
                            message_text=unavail_text,
                            buttons=[{"label": "I followed! 🚀"[:20], "payload": "VERIFY_FOLLOW"}]
                        )
                        execution_summary["processing_state"] = "verification_unavailable"
                        execution_summary["follower_verified"] = False

                        await _update_webhook_event(session, event_id, provider_event_id, "PROCESSED")
                        await session.commit()
                        return execution_summary

            # 5. Run active DM Automations
            stmt_auto = select(Automation).where(
                Automation.instagram_account_id == account.id,
                Automation.status == "ACTIVE"
            )
            res_auto = await session.execute(stmt_auto)
            automations = list(res_auto.scalars().all())

            for auto in automations:
                res = await FlowEngine.run_flow(
                    auto.flow_definition,
                    event_data,
                    instagram_client=meta_client,
                    db_session=session
                )
                is_matched = res.get("status") in ("COMPLETED", "FALLBACK_EXECUTED")
                if is_matched:
                    execution_summary["automations_matched"] += 1
                    execution_summary["results"].append({"automation_id": str(auto.id), "result": res})
                    action_results = res.get("results", [])
                    execution_summary["actions_executed"] += len(action_results)

                log_diagnostic_event(
                    stage="automation_matched",
                    correlation_id=provider_event_id or event_id,
                    event_type="MESSAGING",
                    workspace_id=str(account.workspace_id),
                    account_id=str(account.id),
                    error_code=None if is_matched else "TRIGGER_MISMATCH",
                    details={
                        "automation_id": str(auto.id),
                        "matched": is_matched,
                        "trigger_type": auto.trigger_type,
                        "flow_status": res.get("status")
                    }
                )

                if is_matched:
                    for act_res in action_results:
                        log_diagnostic_event(
                            stage="instagram_api_result",
                            correlation_id=provider_event_id or event_id,
                            event_type="MESSAGING",
                            workspace_id=str(account.workspace_id),
                            account_id=str(account.id),
                            http_status=200 if act_res.get("status") == "SUCCESS" else 400,
                            error_code=None if act_res.get("status") == "SUCCESS" else str(act_res.get("error", "API_ERROR")),
                            details={
                                "action": act_res.get("action"),
                                "status": act_res.get("status"),
                            }
                        )
                        if act_res.get("status") == "SUCCESS":
                            if act_res.get("action") == "PRIVATE_DM":
                                auto.stats_dms_sent = (auto.stats_dms_sent or 0) + 1
                                if conversation:
                                    bot_msg = Message(
                                        workspace_id=account.workspace_id,
                                        conversation_id=conversation.id,
                                        sender_type="BOT",
                                        text=act_res.get("text", ""),
                                        automation_id=auto.id,
                                        created_at=datetime.now(timezone.utc)
                                    )
                                    session.add(bot_msg)

            # 6. Analytics Event
            analytics_evt = AnalyticsEvent(
                workspace_id=account.workspace_id,
                instagram_account_id=account.id,
                automation_id=automations[0].id if automations else None,
                contact_id=contact.id if contact else None,
                event_type="DM_RECEIVED",
                metadata_={
                    "event_id": event_id,
                    "sender_id": sender_id,
                    "actions_count": execution_summary["actions_executed"]
                },
                created_at=datetime.now(timezone.utc)
            )
            session.add(analytics_evt)

            # 7. Update WebhookEvent to PROCESSED
            await _update_webhook_event(session, event_id, provider_event_id, "PROCESSED")
            log_diagnostic_event(
                stage="job_processed",
                correlation_id=provider_event_id or event_id,
                event_type="MESSAGING",
                workspace_id=str(account.workspace_id),
                account_id=str(account.id),
                http_status=200,
                details={
                    "status": execution_summary["status"],
                    "automations_matched": execution_summary["automations_matched"],
                    "actions_executed": execution_summary["actions_executed"]
                }
            )
            await session.commit()
            return execution_summary

        except Exception as e:
            logger.error(f"Error in send_dm_job: {e}", exc_info=True)
            execution_summary["status"] = "FAILED"
            execution_summary["error"] = str(e)
            log_diagnostic_event(
                stage="job_processed",
                correlation_id=event_data.get("provider_event_id") or event_id,
                event_type="MESSAGING",
                http_status=500,
                error_code="JOB_FAILED",
                details={
                    "status": "FAILED",
                    "error": str(e)[:200]
                }
            )
            await _update_webhook_event(session, event_id, event_data.get("provider_event_id"), "FAILED", str(e))
            return execution_summary
