# worker/app/jobs/process_comment.py
import uuid
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from sqlalchemy import select, func

from app.core.database import get_db_session
from app.core.encryption import decrypt_token
from app.core.plans import get_plan_config
from app.engine.flow_engine import FlowEngine
from app.integrations.instagram.client import MetaGraphClient
from app.models import (
    InstagramAccount,
    Automation,
    Contact,
    Conversation,
    Message,
    WebhookEvent,
    AnalyticsEvent,
    Workspace,
    PostUsage
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
    ARQ job processing an incoming Instagram comment webhook event:
    1. Resolves InstagramAccount and active Automations from PostgreSQL.
    2. Decrypts access token and initializes MetaGraphClient.
    3. Runs FlowEngine (Trigger -> Conditions -> Actions).
    4. Auto-creates or updates Contact and Conversation records.
    5. Records Messages, AnalyticsEvent, and updates Automation stats.
    6. Updates WebhookEvent status to PROCESSED.
    """
    logger.info(f"Worker processing comment job: event_id={event_id}")
    execution_summary: Dict[str, Any] = {
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

            # Strictly reject if account is not found - never fallback to arbitrary accounts
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

            # Defense-in-depth: Skip self-comment if commenter is the account itself
            commenter_id = event_data.get("sender_id")
            if commenter_id and account and str(commenter_id) == account.ig_user_id:
                logger.info(f"Skipping self-comment for account {account.id} (commenter_id == ig_user_id == {commenter_id})")
                execution_summary["status"] = "SKIPPED_SELF_EVENT"
                execution_summary["reason"] = "SELF_EVENT_SKIPPED"
                await _update_webhook_event(
                    session, event_id, event_data.get("provider_event_id"), "PROCESSED", "Self-comment skipped"
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

            # If no DB automations found, safely ignore event - never run hardcoded sample flows
            if not automations:
                logger.info(f"No active automations found for account {account.id}. Ignoring event {event_id}.")
                execution_summary["status"] = "IGNORED"
                execution_summary["reason"] = "NO_ACTIVE_AUTOMATIONS"
                await _update_webhook_event(
                    session, event_id, event_data.get("provider_event_id"), "IGNORED", "No active automations found"
                )
                return execution_summary

            # 2.5 Enforce Workspace Plan Quota & Limits with row-level locks
            stmt_ws = select(Workspace).where(Workspace.id == account.workspace_id).with_for_update()
            res_ws = await session.execute(stmt_ws)
            workspace = res_ws.scalar_one_or_none()
            tier = (workspace.plan_tier or "FREE").upper() if workspace else "FREE"
            plan_cfg = get_plan_config(tier)

            media_id = str(event_data.get("post_id") or event_data.get("media_id") or "").strip()
            post_usage: Optional[PostUsage] = None

            if media_id and media_id.lower() not in ("all", "none", ""):
                stmt_post = select(PostUsage).where(
                    PostUsage.workspace_id == account.workspace_id,
                    PostUsage.media_id == media_id
                ).with_for_update()
                res_post = await session.execute(stmt_post)
                post_usage = res_post.scalars().first()

                max_posts = plan_cfg.get("max_posts_quota", 10)
                if not post_usage and max_posts != -1:
                    cnt_stmt = select(func.count(PostUsage.id)).where(PostUsage.workspace_id == account.workspace_id)
                    cnt_res = await session.execute(cnt_stmt)
                    current_post_count = cnt_res.scalar() or 0
                    if current_post_count >= max_posts:
                        logger.warning(
                            f"Post quota limit reached ({current_post_count}/{max_posts}) for workspace {account.workspace_id}. "
                            f"Ignoring comment for media {media_id}."
                        )
                        execution_summary["status"] = "QUOTA_EXCEEDED"
                        execution_summary["reason"] = f"POST_QUOTA_EXCEEDED: max {max_posts} posts allowed on {plan_cfg.get('name', 'Free')} plan"
                        await _update_webhook_event(
                            session, event_id, event_data.get("provider_event_id"), "IGNORED", execution_summary["reason"]
                        )
                        return execution_summary

                # Check max DMs per post
                max_dms = plan_cfg.get("max_dms_per_post", 99)
                current_dms = post_usage.dms_delivered_count if post_usage else 0
                if current_dms >= max_dms:
                    logger.warning(
                        f"DM quota per post reached ({current_dms}/{max_dms}) for post {media_id}. Ignoring comment."
                    )
                    execution_summary["status"] = "QUOTA_EXCEEDED"
                    execution_summary["reason"] = f"DM_QUOTA_EXCEEDED: max {max_dms} DMs per post allowed on {plan_cfg.get('name', 'Free')} plan"
                    await _update_webhook_event(
                        session, event_id, event_data.get("provider_event_id"), "IGNORED", execution_summary["reason"]
                    )
                    return execution_summary

            # 2.6 Resolve Contact & Pre-cache follower status if already verified
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
                if contact and contact.follower_status == "FOLLOWING":
                    event_data["follower_status"] = "FOLLOWING"

            event_data["business_username"] = account.username
            event_data["account_username"] = account.username

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
                if res.get("processing_state"):
                    execution_summary["processing_state"] = res.get("processing_state")
                if res.get("follower_verified") is not None:
                    execution_summary["follower_verified"] = res.get("follower_verified")

                if is_matched:
                    action_results = res.get("results", [])
                    execution_summary["actions_executed"] += len(action_results)
                    for act_res in action_results:
                        if act_res.get("status") == "SUCCESS":
                            if act_res.get("action") == "PUBLIC_REPLY":
                                auto.stats_comments = (auto.stats_comments or 0) + 1
                            elif act_res.get("action") == "PRIVATE_DM":
                                auto.stats_dms_sent = (auto.stats_dms_sent or 0) + 1
                                # Atomically track verified DM delivery on PostUsage
                                if media_id and media_id.lower() not in ("all", "none", ""):
                                    if not post_usage:
                                        post_usage = PostUsage(
                                            id=uuid.uuid4(),
                                            workspace_id=account.workspace_id,
                                            instagram_account_id=account.id,
                                            media_id=media_id,
                                            dms_delivered_count=1,
                                            last_delivered_at=datetime.now(timezone.utc)
                                        )
                                        session.add(post_usage)
                                    else:
                                        post_usage.dms_delivered_count = (post_usage.dms_delivered_count or 0) + 1
                                        post_usage.last_delivered_at = datetime.now(timezone.utc)

            # 3. Contact Auto-Creation / Upsert with Follower & Automation States
            if account and commenter_id:
                if not contact:
                    contact = Contact(
                        workspace_id=account.workspace_id,
                        instagram_account_id=account.id,
                        ig_user_id=str(commenter_id),
                        username=commenter_username,
                        follower_status=str(event_data.get("follower_status") or "UNKNOWN"),
                        automation_state=str(execution_summary.get("processing_state") or "received"),
                        interaction_count=1,
                        tags=["lead", "commenter"],
                        custom_fields={},
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
                        contact.follower_status = str(event_data.get("follower_status"))
                    if execution_summary.get("processing_state"):
                        contact.automation_state = str(execution_summary["processing_state"])

                # Persist pending delivery for follow-to-unlock recheck if follow gate was sent
                for auto_run in execution_summary["results"]:
                    r_obj = auto_run.get("result", {})
                    if r_obj.get("pending_delivery"):
                        current_cf = dict(contact.custom_fields) if isinstance(contact.custom_fields, dict) else {}
                        current_cf["follow_gate_pending"] = r_obj["pending_delivery"]
                        contact.custom_fields = current_cf
                        contact.automation_state = "verification_pending"
                await session.flush()

            # 4. P1.6: Conversation and Message Auto-Creation
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

                            # Deduplicate bot message by meta_message_id if provided
                            is_dup_bot_msg = False
                            if meta_msg_id:
                                stmt_dup_bot = select(Message.id).where(
                                    Message.conversation_id == conversation.id,
                                    Message.meta_message_id == meta_msg_id
                                )
                                res_dup_bot = await session.execute(stmt_dup_bot)
                                if res_dup_bot.scalar_one_or_none():
                                    is_dup_bot_msg = True

                            if not is_dup_bot_msg:
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

            # 5. P1.7: Analytics Event Recording
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
                        "sender_username": commenter_username,
                        "processing_state": execution_summary.get("processing_state", "completed"),
                        "follower_status": contact.follower_status if contact else "UNKNOWN"
                    },
                    created_at=datetime.now(timezone.utc)
                )
                session.add(analytics_event)

            # 6. P2.2: Update WebhookEvent status = PROCESSED
            await _update_webhook_event(session, event_id, event_data.get("provider_event_id"), "PROCESSED")

    except Exception as ex:
        logger.error(f"Error processing comment event {event_id}: {ex}", exc_info=True)
        execution_summary["status"] = "FAILED"
        execution_summary["error"] = str(ex)

        # Attempt to mark WebhookEvent as FAILED
        try:
            async with get_db_session() as fail_session:
                await _update_webhook_event(fail_session, event_id, event_data.get("provider_event_id"), "FAILED", str(ex))
        except Exception:
            pass

    logger.info(f"Job completed for event {event_id}: {execution_summary['status']}")
    return execution_summary
