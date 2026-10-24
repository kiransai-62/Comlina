# server/app/jobs/process_comment.py
import uuid
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from sqlalchemy import select, update, or_, case, func, text

from app.core.database import get_db_session
from app.core.encryption import decrypt_token
from app.core.plans import get_plan_config
from app.core.logging import log_diagnostic_event, redact_string
from app.engine.flow_engine import FlowEngine
from app.integrations.instagram.client import MetaGraphClient
from app.models import (
    InstagramAccount,
    Automation,
    AutomationVersion,
    Contact,
    Conversation,
    Message,
    WebhookEvent,
    AnalyticsEvent,
    Workspace,
    PostUsage,
    AutomationRun
)

logger = logging.getLogger("process_comment")


async def reserve_quota(
    db_session,
    account_id: Any,
    event_id: str,
    automation_id: Optional[Any] = None,
    media_id: Optional[str] = None,
    max_dms: Optional[int] = None,
    workspace_id: Optional[Any] = None
) -> bool:
    """
    Idempotent atomic quota reservation keyed by event_id to prevent double-counting on ARQ retries.
    Replaces row-locking (with_for_update) to avoid serializing comment bursts.
    """
    acc_str = str(account_id)
    evt_str = str(event_id)

    # 1. Idempotent reservation check
    check_stmt = select(AutomationRun.id).where(
        AutomationRun.event_id == evt_str,
        AutomationRun.action == "QUOTA_RESERVED"
    )
    check_res = await db_session.execute(check_stmt)
    if check_res.scalar_one_or_none():
        return True

    # 2. Build account filter supporting both UUID and string forms
    acc_uuid = None
    if isinstance(account_id, uuid.UUID):
        acc_uuid = account_id
    else:
        try:
            acc_uuid = uuid.UUID(acc_str)
        except (ValueError, TypeError):
            pass

    auto_uuid = None
    if automation_id:
        if isinstance(automation_id, uuid.UUID):
            auto_uuid = automation_id
        else:
            try:
                auto_uuid = uuid.UUID(str(automation_id))
            except (ValueError, TypeError):
                pass

    ws_uuid = None
    if workspace_id:
        if isinstance(workspace_id, uuid.UUID):
            ws_uuid = workspace_id
        else:
            try:
                ws_uuid = uuid.UUID(str(workspace_id))
            except (ValueError, TypeError):
                pass

    acc_filters = [PostUsage.ig_account_id == acc_str]
    if acc_uuid:
        acc_filters.append(PostUsage.instagram_account_id == acc_uuid)
    account_cond = or_(*acc_filters)

    conditions = [account_cond]
    if media_id and str(media_id).lower() not in ("all", "none", ""):
        conditions.append(PostUsage.media_id == str(media_id))

    if max_dms is not None and max_dms != -1:
        conditions.append(PostUsage.dms_delivered_count < max_dms)
    conditions.append(or_(PostUsage.max_dms.is_(None), PostUsage.dms_delivered_count < PostUsage.max_dms))

    # 3. Atomic update using returning
    update_stmt = (
        update(PostUsage)
        .where(*conditions)
        .values(
            dms_delivered_count=PostUsage.dms_delivered_count + 1,
            last_delivered_at=func.now(),
            updated_at=func.now()
        )
        .returning(PostUsage.id)
    )
    result = await db_session.execute(update_stmt)
    reservation = result.scalar()

    # 4. If no row was updated, check if row exists (quota exhausted vs new row needed)
    if not reservation:
        find_conds = [account_cond]
        if media_id and str(media_id).lower() not in ("all", "none", ""):
            find_conds.append(PostUsage.media_id == str(media_id))

        chk_stmt = select(PostUsage.id, PostUsage.dms_delivered_count, PostUsage.max_dms).where(*find_conds)
        chk_res = await db_session.execute(chk_stmt)
        existing = chk_res.first()
        if existing:
            # Row exists but failed quota cap check
            return False

        # Row doesn't exist yet, insert with initial count 1 if within limit
        if max_dms is not None and max_dms <= 0:
            return False

        m_id = str(media_id) if (media_id and str(media_id).lower() not in ("all", "none", "")) else "default"
        new_usage = PostUsage(
            id=uuid.uuid4(),
            workspace_id=ws_uuid,
            instagram_account_id=acc_uuid,
            ig_account_id=acc_str,
            media_id=m_id,
            dms_delivered_count=1,
            max_dms=max_dms,
            last_delivered_at=datetime.now(timezone.utc)
        )
        db_session.add(new_usage)
        try:
            await db_session.flush()
            reservation = new_usage.id
        except Exception:
            retry_res = await db_session.execute(update_stmt)
            reservation = retry_res.scalar()

    if reservation:
        auto_run = AutomationRun(
            id=uuid.uuid4(),
            workspace_id=ws_uuid,
            instagram_account_id=acc_uuid,
            ig_account_id=acc_str,
            event_id=evt_str,
            automation_id=auto_uuid,
            action="QUOTA_RESERVED",
            status="SUCCESS",
            attempt=1,
            created_at=datetime.now(timezone.utc)
        )
        db_session.add(auto_run)
        await db_session.commit()
        return True

    return False


async def rollback_quota(db_session, account_id: Any, media_id: Optional[str] = None):
    acc_str = str(account_id)
    acc_uuid = None
    if isinstance(account_id, uuid.UUID):
        acc_uuid = account_id
    else:
        try:
            acc_uuid = uuid.UUID(acc_str)
        except (ValueError, TypeError):
            pass

    acc_filters = [PostUsage.ig_account_id == acc_str]
    if acc_uuid:
        acc_filters.append(PostUsage.instagram_account_id == acc_uuid)
    account_cond = or_(*acc_filters)

    conditions = [account_cond]
    if media_id and str(media_id).lower() not in ("all", "none", ""):
        conditions.append(PostUsage.media_id == str(media_id))

    stmt = (
        update(PostUsage)
        .where(*conditions)
        .values(
            dms_delivered_count=case(
                (PostUsage.dms_delivered_count > 0, PostUsage.dms_delivered_count - 1),
                else_=0
            ),
            updated_at=func.now()
        )
    )
    await db_session.execute(stmt)
    await db_session.commit()


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
            webhook_event.error = redact_string(error)[:1000]
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

            # Strictly reject if account is not found
            if not account:
                logger.warning(
                    f"No matching InstagramAccount found for business_ig_id={business_ig_id}, "
                    f"account_id={account_id_str}. Ignoring event {event_id}."
                )
                execution_summary["status"] = "IGNORED"
                execution_summary["reason"] = "ACCOUNT_NOT_FOUND"
                log_diagnostic_event(
                    stage="job_processed",
                    correlation_id=event_data.get("provider_event_id") or event_id,
                    event_type="COMMENT",
                    error_code="ACCOUNT_NOT_FOUND",
                    details={"status": "IGNORED", "reason": "ACCOUNT_NOT_FOUND"}
                )
                await _update_webhook_event(
                    session, event_id, event_data.get("provider_event_id"), "IGNORED", "No matching Instagram account found"
                )
                return execution_summary

            # Guard: reject inactive or disconnected accounts before doing any work.
            if not account.is_active or account.connection_status not in ("CONNECTED", "UNKNOWN"):
                logger.warning(
                    f"Skipping event {event_id}: account {account.id} is inactive or disconnected "
                    f"(is_active={account.is_active}, connection_status={account.connection_status})."
                )
                execution_summary["status"] = "IGNORED"
                execution_summary["reason"] = "ACCOUNT_INACTIVE"
                log_diagnostic_event(
                    stage="job_processed",
                    correlation_id=event_data.get("provider_event_id") or event_id,
                    event_type="COMMENT",
                    workspace_id=str(account.workspace_id),
                    account_id=str(account.id),
                    error_code="ACCOUNT_INACTIVE",
                    details={
                        "is_active": account.is_active,
                        "connection_status": account.connection_status,
                    }
                )
                await _update_webhook_event(
                    session, event_id, event_data.get("provider_event_id"), "IGNORED", "Account inactive or disconnected"
                )
                return execution_summary

            # Defense-in-depth: Skip self-comment if commenter is the account itself
            commenter_id = event_data.get("sender_id")
            if commenter_id and account and str(commenter_id) == account.ig_user_id:
                logger.info(f"Skipping self-comment for account {account.id} (commenter_id == ig_user_id == {commenter_id})")
                execution_summary["status"] = "SKIPPED_SELF_EVENT"
                execution_summary["reason"] = "SELF_EVENT_SKIPPED"
                log_diagnostic_event(
                    stage="job_processed",
                    correlation_id=event_data.get("provider_event_id") or event_id,
                    event_type="COMMENT",
                    workspace_id=str(account.workspace_id),
                    account_id=str(account.id),
                    details={"status": "SKIPPED_SELF_EVENT"}
                )
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

            if not automations:
                logger.info(f"No active automations found for account {account.id}. Ignoring event {event_id}.")
                log_diagnostic_event(
                    stage="automation_matched",
                    correlation_id=event_data.get("provider_event_id") or event_id,
                    event_type="COMMENT",
                    workspace_id=str(account.workspace_id),
                    account_id=str(account.id),
                    error_code="NO_ACTIVE_AUTOMATIONS",
                    details={"automations_found": 0}
                )
                execution_summary["status"] = "IGNORED"
                execution_summary["reason"] = "NO_ACTIVE_AUTOMATIONS"
                log_diagnostic_event(
                    stage="job_processed",
                    correlation_id=event_data.get("provider_event_id") or event_id,
                    event_type="COMMENT",
                    workspace_id=str(account.workspace_id),
                    account_id=str(account.id),
                    details={"status": "IGNORED", "reason": "NO_ACTIVE_AUTOMATIONS"}
                )
                await _update_webhook_event(
                    session, event_id, event_data.get("provider_event_id"), "IGNORED", "No active automations found"
                )
                return execution_summary

            # 2.5 Enforce Workspace Plan Quota & Limits atomically without row-level locks
            stmt_ws = select(Workspace).where(Workspace.id == account.workspace_id)
            res_ws = await session.execute(stmt_ws)
            workspace = res_ws.scalar_one_or_none()
            tier = (workspace.plan_tier or "FREE").upper() if workspace else "FREE"
            plan_cfg = get_plan_config(tier)

            media_id = str(event_data.get("post_id") or event_data.get("media_id") or "").strip()
            max_dms = plan_cfg.get("max_dms_per_post", 99)
            max_posts = plan_cfg.get("max_posts_quota", 10)
            quota_reserved = False

            if media_id and media_id.lower() not in ("all", "none", ""):
                if max_posts != -1:
                    cnt_stmt = select(func.count(PostUsage.id)).where(PostUsage.workspace_id == account.workspace_id)
                    cnt_res = await session.execute(cnt_stmt)
                    current_post_count = cnt_res.scalar() or 0
                    if current_post_count >= max_posts:
                        chk_post = await session.execute(
                            select(PostUsage.id).where(
                                PostUsage.workspace_id == account.workspace_id,
                                PostUsage.media_id == media_id
                            )
                        )
                        if not chk_post.scalar_one_or_none():
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

                # Atomically reserve quota upfront without locking
                reserved = await reserve_quota(
                    session,
                    account_id=account.id,
                    event_id=event_id,
                    automation_id=automations[0].id if automations else None,
                    media_id=media_id,
                    max_dms=max_dms,
                    workspace_id=account.workspace_id
                )
                if not reserved:
                    logger.warning(
                        f"DM quota per post reached for post {media_id}. Ignoring comment."
                    )
                    execution_summary["status"] = "QUOTA_EXCEEDED"
                    execution_summary["reason"] = f"DM_QUOTA_EXCEEDED: max {max_dms} DMs per post allowed on {plan_cfg.get('name', 'Free')} plan"
                    await _update_webhook_event(
                        session, event_id, event_data.get("provider_event_id"), "IGNORED", execution_summary["reason"]
                    )
                    return execution_summary
                quota_reserved = True

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

            any_action_failed = False
            first_failure_error = None
            transient_error = None
            dm_delivered_count = 0

            for auto in automations:
                # F6: Execute the latest published snapshot from automation_versions if available
                flow_def = auto.flow_definition
                stmt_ver = (
                    select(AutomationVersion.flow_definition)
                    .where(
                        AutomationVersion.automation_id == auto.id,
                        AutomationVersion.workspace_id == account.workspace_id
                    )
                    .order_by(AutomationVersion.version.desc())
                    .limit(1)
                )
                res_ver = await session.execute(stmt_ver)
                latest_snapshot = res_ver.scalar_one_or_none()
                if latest_snapshot and isinstance(latest_snapshot, dict):
                    flow_def = latest_snapshot

                res = await FlowEngine.run_flow(
                    flow_def,
                    event_data,
                    instagram_client=meta_client,
                    db_session=session
                )
                is_matched = res.get("status") in ("COMPLETED", "FALLBACK_EXECUTED")
                if is_matched:
                    execution_summary["automations_matched"] += 1
                log_diagnostic_event(
                    stage="automation_matched",
                    correlation_id=event_data.get("provider_event_id") or event_id,
                    event_type="COMMENT",
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
                execution_summary["results"].append({"automation_id": str(auto.id), "result": res})
                if res.get("processing_state"):
                    execution_summary["processing_state"] = res.get("processing_state")
                if res.get("follower_verified") is not None:
                    execution_summary["follower_verified"] = res.get("follower_verified")
                if res.get("follower_status"):
                    execution_summary["follower_status"] = res.get("follower_status")
                    event_data["follower_status"] = res.get("follower_status")

                if is_matched:
                    action_results = res.get("results", [])
                    execution_summary["actions_executed"] += len(action_results)
                    for act_res in action_results:
                        log_diagnostic_event(
                            stage="instagram_api_result",
                            correlation_id=event_data.get("provider_event_id") or event_id,
                            event_type="COMMENT",
                            workspace_id=str(account.workspace_id),
                            account_id=str(account.id),
                            http_status=200 if act_res.get("status") == "SUCCESS" else 400,
                            error_code=None if act_res.get("status") == "SUCCESS" else str(act_res.get("error", "API_ERROR")),
                            details={
                                "action": act_res.get("action"),
                                "status": act_res.get("status"),
                            }
                        )
                        act_status = act_res.get("status")
                        job_try = ctx.get("job_try", 1) if isinstance(ctx, dict) else 1
                        run_entry = AutomationRun(
                            workspace_id=account.workspace_id,
                            instagram_account_id=account.id,
                            ig_account_id=str(account.id),
                            event_id=str(event_id),
                            automation_id=auto.id,
                            action=str(act_res.get("action") or "UNKNOWN"),
                            status=str(act_status or "UNKNOWN"),
                            attempt=job_try,
                            meta_error_code=str(act_res.get("error_code")) if act_res.get("error_code") else None,
                            meta_error_subcode=str(act_res.get("error_subcode")) if act_res.get("error_subcode") else None,
                            error_message=redact_string(str(act_res.get("error")))[:1000] if act_res.get("error") else None,
                            created_at=datetime.now(timezone.utc)
                        )
                        session.add(run_entry)

                        if act_status == "FAILED":
                            any_action_failed = True
                            err_msg = act_res.get("error", "Action execution failed")
                            if not first_failure_error:
                                first_failure_error = err_msg
                            err_code = act_res.get("error_code")
                            if err_code == 190 or "expired" in str(err_msg).lower():
                                account.connection_status = "REAUTHORIZATION_REQUIRED"
                                account.last_error_code = "TOKEN_EXPIRED"
                            elif err_code in (4, 17, 32, 613) or act_res.get("http_status") in (429, 500, 502, 503, 504) or "network" in str(err_msg).lower():
                                transient_error = err_msg
                            
                            # Rollback reserved quota on permanent DM failure
                            if act_res.get("action") == "PRIVATE_DM" and quota_reserved and not transient_error:
                                await rollback_quota(session, account_id=account.id, media_id=media_id)
                                quota_reserved = False
                        elif act_status == "SUCCESS":
                            if act_res.get("action") == "PUBLIC_REPLY":
                                auto.stats_comments = (auto.stats_comments or 0) + 1
                            elif act_res.get("action") == "PRIVATE_DM":
                                verified_msg_id = act_res.get("verified_message_id")
                                if verified_msg_id:
                                    auto.stats_dms_sent = (auto.stats_dms_sent or 0) + 1
                                    dm_delivered_count += 1
                                else:
                                    logger.warning(
                                        f"PRIVATE_DM stat NOT incremented for automation {auto.id}: "
                                        f"no verified_message_id in action result (status={act_status}). "
                                        "Delivery unconfirmed."
                                    )
                                    if quota_reserved:
                                        await rollback_quota(session, account_id=account.id, media_id=media_id)
                                        quota_reserved = False

            if quota_reserved and dm_delivered_count == 0 and not transient_error:
                await rollback_quota(session, account_id=account.id, media_id=media_id)
                quota_reserved = False

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
                        "sender_username": commenter_username,
                        "processing_state": execution_summary.get("processing_state", "completed"),
                        "follower_status": contact.follower_status if contact else "UNKNOWN"
                    },
                    created_at=datetime.now(timezone.utc)
                )
                session.add(analytics_event)

            # F4: If any transient error occurred and ARQ attempts remain, raise for worker backoff retry
            job_try = ctx.get("job_try", 1) if isinstance(ctx, dict) else 1
            if transient_error and job_try < 3:
                logger.warning(
                    f"Transient Meta error in comment job for event {event_id} (attempt {job_try}/3). "
                    f"Re-raising to trigger ARQ backoff retry: {transient_error}"
                )
                from app.integrations.instagram.exceptions import MetaGraphAPIError
                raise MetaGraphAPIError(transient_error, is_transient=True)

            # 6. Update WebhookEvent status based on action results
            if any_action_failed:
                execution_summary["status"] = "FAILED"
                execution_summary["error"] = first_failure_error
                await _update_webhook_event(session, event_id, event_data.get("provider_event_id"), "FAILED", first_failure_error)
            else:
                await _update_webhook_event(session, event_id, event_data.get("provider_event_id"), "PROCESSED")

            log_diagnostic_event(
                stage="job_processed",
                correlation_id=event_data.get("provider_event_id") or event_id,
                event_type="COMMENT",
                workspace_id=str(account.workspace_id),
                account_id=str(account.id),
                http_status=200,
                details={
                    "status": execution_summary["status"],
                    "automations_matched": execution_summary["automations_matched"],
                    "actions_executed": execution_summary["actions_executed"]
                }
            )

    except Exception as ex:
        # F4: Re-raise transient exceptions if ARQ retries remain
        is_transient = getattr(ex, "is_transient", False)
        job_try = ctx.get("job_try", 1) if isinstance(ctx, dict) else 1
        if is_transient and job_try < 3:
            logger.warning(
                f"Transient exception in comment job for event {event_id} (attempt {job_try}/3). "
                f"Re-raising for ARQ retry: {ex}"
            )
            raise
        logger.error(f"Error processing comment event {event_id}: {ex}", exc_info=True)
        execution_summary["status"] = "FAILED"
        execution_summary["error"] = redact_string(str(ex))
        meta_err = ex.to_diagnostic_dict() if hasattr(ex, "to_diagnostic_dict") else None
        diag_details: Dict[str, Any] = {
            "status": "FAILED",
            "error": redact_string(str(ex))[:200]
        }
        if meta_err:
            diag_details["meta_error"] = meta_err

        log_diagnostic_event(
            stage="job_processed",
            correlation_id=event_data.get("provider_event_id") or event_id,
            event_type="COMMENT",
            http_status=getattr(ex, "http_status", 500) or 500,
            error_code=str(getattr(ex, "code", "JOB_FAILED")),
            details=diag_details
        )

        try:
            async with get_db_session() as fail_session:
                await _update_webhook_event(fail_session, event_id, event_data.get("provider_event_id"), "FAILED", str(ex))
        except Exception:
            pass

    logger.info(f"Job completed for event {event_id}: {execution_summary['status']}")
    return execution_summary
