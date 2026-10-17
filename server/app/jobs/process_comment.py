# server/app/jobs/process_comment.py
import uuid
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from sqlalchemy import select

from app.core.database import get_db_session
from app.core.encryption import decrypt_token
from app.engine.flow_engine import FlowEngine
from app.integrations.instagram.client import MetaGraphClient
from app.models import (
    InstagramAccount,
    Automation,
    Contact,
    Conversation,
    Message,
    WebhookEvent,
    AnalyticsEvent
)

logger = logging.getLogger("process_comment")

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

async def process_comment_job(ctx: Dict[str, Any], event_id: str, event_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Job processing an incoming Instagram comment webhook event:
    1. Resolves InstagramAccount and active Automations.
    2. Decrypts access token and initializes MetaGraphClient.
    3. Runs FlowEngine (Trigger -> Conditions -> Actions).
    4. Auto-creates or updates Contact and Conversation records.
    5. Records Messages, AnalyticsEvent, and updates Automation stats.
    6. Updates WebhookEvent status to PROCESSED.
    """
    logger.info(f"Processing comment job: event_id={event_id}")
    execution_summary = {
        "event_id": event_id,
        "automations_matched": 0,
        "actions_executed": 0,
        "status": "COMPLETED",
        "results": []
    }

    try:
        async with get_db_session() as session:
            # 1. Resolve Instagram Account
            account = None
            account_id_str = event_data.get("instagram_account_id")
            business_ig_id = event_data.get("business_ig_id")

            if account_id_str:
                try:
                    stmt_acc = select(InstagramAccount).where(InstagramAccount.id == uuid.UUID(account_id_str))
                    res_acc = await session.execute(stmt_acc)
                    account = res_acc.scalar_one_or_none()
                except ValueError:
                    pass

            if not account and business_ig_id:
                stmt_acc = select(InstagramAccount).where(InstagramAccount.ig_user_id == str(business_ig_id))
                res_acc = await session.execute(stmt_acc)
                account = res_acc.scalar_one_or_none()

            # Strictly reject if account is not found
            if not account:
                logger.warning(
                    f"No matching InstagramAccount found for business_ig_id={business_ig_id}, "
                    f"account_id={account_id_str}. Ignoring event {event_id}."
                )
                execution_summary["status"] = "IGNORED"
                execution_summary["reason"] = "ACCOUNT_NOT_FOUND"
                await _update_webhook_event(
                    session, event_id, event_data.get("provider_event_id"), "IGNORED", "No matching Instagram account found"
                )
                return execution_summary

            meta_client = None
            if account.access_token_encrypted:
                try:
                    decrypted_token = decrypt_token(account.access_token_encrypted)
                    if decrypted_token:
                        meta_client = MetaGraphClient(access_token=decrypted_token)
                except Exception as ex:
                    logger.error(f"Failed to decrypt Instagram access token for account {account.id}: {ex}")

            # 2. Query Active Automations for this account & workspace
            stmt_auto = (
                select(Automation)
                .where(
                    Automation.workspace_id == account.workspace_id,
                    Automation.instagram_account_id == account.id,
                    Automation.status == "ACTIVE"
                )
            )
            res_auto = await session.execute(stmt_auto)
            automations: List[Automation] = list(res_auto.scalars().all())

            if not automations:
                logger.info(f"No active automations found for account {account.id}. Ignoring event {event_id}.")
                execution_summary["status"] = "IGNORED"
                execution_summary["reason"] = "NO_ACTIVE_AUTOMATIONS"
                await _update_webhook_event(
                    session, event_id, event_data.get("provider_event_id"), "IGNORED", "No active automations found"
                )
                return execution_summary

            for auto in automations:
                res = await FlowEngine.run_flow(
                    auto.flow_definition,
                    event_data,
                    instagram_client=meta_client,
                    db_session=session
                )
                execution_summary["automations_matched"] += 1
                execution_summary["results"].append({"automation_id": str(auto.id), "result": res})

                if res.get("status") in ("COMPLETED", "FALLBACK_EXECUTED"):
                    action_results = res.get("results", [])
                    execution_summary["actions_executed"] += len(action_results)
                    for act_res in action_results:
                        if act_res.get("status") == "SUCCESS":
                            if act_res.get("action") == "PUBLIC_REPLY":
                                auto.stats_comments = (auto.stats_comments or 0) + 1
                            elif act_res.get("action") == "PRIVATE_DM":
                                auto.stats_dms_sent = (auto.stats_dms_sent or 0) + 1

            # 3. Contact Auto-Creation / Upsert
            contact = None
            commenter_id = event_data.get("sender_id")
            commenter_username = event_data.get("sender_username", "unknown")

            if account and commenter_id:
                stmt_contact = (
                    select(Contact)
                    .where(
                        Contact.workspace_id == account.workspace_id,
                        Contact.instagram_account_id == account.id,
                        Contact.ig_user_id == str(commenter_id)
                    )
                )
                res_contact = await session.execute(stmt_contact)
                contact = res_contact.scalar_one_or_none()

                if not contact:
                    contact = Contact(
                        workspace_id=account.workspace_id,
                        instagram_account_id=account.id,
                        ig_user_id=str(commenter_id),
                        username=commenter_username,
                        follower_status=event_data.get("follower_status", "UNKNOWN"),
                        interaction_count=1,
                        tags=["lead", "commenter"],
                        last_interaction_at=datetime.now(timezone.utc)
                    )
                    session.add(contact)
                    await session.flush()
                else:
                    contact.interaction_count = (contact.interaction_count or 0) + 1
                    contact.last_interaction_at = datetime.now(timezone.utc)
                    if commenter_username and commenter_username != "unknown":
                        contact.username = commenter_username
                    if event_data.get("follower_status"):
                        contact.follower_status = event_data.get("follower_status")
                    await session.flush()

            # 4. Conversation and Message Auto-Creation
            if account and contact:
                stmt_conv = (
                    select(Conversation)
                    .where(
                        Conversation.workspace_id == account.workspace_id,
                        Conversation.instagram_account_id == account.id,
                        Conversation.contact_id == contact.id
                    )
                )
                res_conv = await session.execute(stmt_conv)
                conversation = res_conv.scalar_one_or_none()

                comment_text = event_data.get("text", "")
                if not conversation:
                    conversation = Conversation(
                        workspace_id=account.workspace_id,
                        instagram_account_id=account.id,
                        contact_id=contact.id,
                        status="OPEN",
                        last_message_text=comment_text,
                        last_message_at=datetime.now(timezone.utc),
                        unread_count=0
                    )
                    session.add(conversation)
                    await session.flush()
                else:
                    conversation.last_message_at = datetime.now(timezone.utc)
                    if comment_text:
                        conversation.last_message_text = comment_text

                # Record messages for any DMs sent
                for auto_run in execution_summary["results"]:
                    res_obj = auto_run.get("result", {})
                    for act_res in res_obj.get("results", []):
                        if act_res.get("status") == "SUCCESS" and act_res.get("action") == "PRIVATE_DM":
                            msg_text = act_res.get("text", "")
                            meta_resp = act_res.get("meta_response", {})
                            meta_msg_id = meta_resp.get("message_id") if isinstance(meta_resp, dict) else None
                            auto_id_val = None
                            try:
                                auto_id_val = uuid.UUID(str(auto_run.get("automation_id")))
                            except (ValueError, TypeError):
                                pass

                            dm_msg = Message(
                                workspace_id=account.workspace_id,
                                conversation_id=conversation.id,
                                sender_type="BOT",
                                text=msg_text,
                                meta_message_id=meta_msg_id,
                                automation_id=auto_id_val,
                                created_at=datetime.now(timezone.utc)
                            )
                            session.add(dm_msg)

            # 5. Analytics Event Recording
            if account and execution_summary["actions_executed"] > 0:
                first_auto_id = None
                try:
                    if automations:
                        first_auto_id = automations[0].id
                except Exception:
                    pass

                analytics_event = AnalyticsEvent(
                    workspace_id=account.workspace_id,
                    instagram_account_id=account.id,
                    automation_id=first_auto_id,
                    contact_id=contact.id if contact else None,
                    event_type="COMMENT_AUTOMATION_EXECUTED",
                    metadata_={
                        "comment_id": event_data.get("comment_id"),
                        "actions_count": execution_summary["actions_executed"],
                        "sender_username": commenter_username
                    },
                    created_at=datetime.now(timezone.utc)
                )
                session.add(analytics_event)

            # 6. Update WebhookEvent status = PROCESSED
            await _update_webhook_event(session, event_id, event_data.get("provider_event_id"), "PROCESSED")

    except Exception as ex:
        logger.error(f"Error processing comment event {event_id}: {ex}", exc_info=True)
        execution_summary["status"] = "FAILED"
        execution_summary["error"] = str(ex)

        try:
            async with get_db_session() as fail_session:
                await _update_webhook_event(fail_session, event_id, event_data.get("provider_event_id"), "FAILED", str(ex))
        except Exception:
            pass

    logger.info(f"Job completed for event {event_id}: {execution_summary['status']}")
    return execution_summary
