# server/app/services/plan_service.py
"""
Plan Service: Enforces Plan Entitlements, Post Quotas (10 posts for Free),
and Post DM Limits (99 DMs per post for Free).
"""

import uuid
import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any, Tuple, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.models import Workspace, PostUsage, Automation
from app.core.plans import PlanTier, PLAN_CONFIG, get_plan_config, has_feature, get_required_plan_for_feature

logger = logging.getLogger(__name__)


class PlanService:
    @staticmethod
    def check_feature_access(workspace: Workspace, feature_key: str) -> bool:
        """Check if workspace's current plan tier includes the feature."""
        tier = workspace.plan_tier or "FREE"
        return has_feature(tier, feature_key)

    @staticmethod
    def validate_automation_features(
        workspace: Workspace,
        flow_definition: Dict[str, Any]
    ) -> Tuple[bool, Optional[str]]:
        """
        Validates all features in an automation flow against workspace plan tier.
        Returns (True, None) if valid, or (False, "Error message...") if locked.
        """
        tier = (workspace.plan_tier or "FREE").upper()
        plan_cfg = get_plan_config(tier)

        # 1. Ask to Follow (Follower Gate check) -> PREMIUM or PRO
        ask_follow = flow_definition.get("askFollowEnabled") or flow_definition.get("ask_to_follow")
        if ask_follow and not has_feature(tier, "ask_to_follow"):
            return False, "Ask to Follow requires a Premium (₹199/mo) or Pro plan. Please upgrade to unlock."

        # 2. Comment Teaser Reply (Public Reply) -> PREMIUM or PRO
        teaser = flow_definition.get("teaserEnabled") or flow_definition.get("public_reply")
        if teaser and not has_feature(tier, "comment_teaser_reply"):
            return False, "Comment Teaser Reply requires a Premium (₹199/mo) or Pro plan. Please upgrade to unlock."

        # 3. Follow-up DMs -> PREMIUM or PRO
        follow_ups = flow_definition.get("followUpEnabled") or flow_definition.get("follow_ups")
        if follow_ups and not has_feature(tier, "follow_up_dms"):
            return False, "Follow-up DMs require a Premium (₹199/mo) or Pro plan. Please upgrade to unlock."

        # 4. DM Buttons -> PREMIUM or PRO
        buttons = flow_definition.get("buttons") or flow_definition.get("dm_buttons") or []
        if buttons and len(buttons) > 0 and not has_feature(tier, "dm_buttons"):
            return False, "Interactive DM Buttons require a Premium (₹199/mo) or Pro plan. Please upgrade to unlock."

        # 5. Reply to All -> PREMIUM or PRO
        reply_to_all = flow_definition.get("replyToAll") or flow_definition.get("reply_to_all")
        if reply_to_all and not has_feature(tier, "reply_to_all"):
            return False, "Reply to All Comments requires a Premium (₹199/mo) or Pro plan. Please upgrade to unlock."

        # 6. Trigger Keywords (>3 keywords requires expanded_keywords)
        raw_trigger = flow_definition.get("trigger")
        trigger_config: Dict[str, Any] = raw_trigger if isinstance(raw_trigger, dict) else {}
        trigger_mode = str(
            flow_definition.get("triggerMode")
            or trigger_config.get("triggerMode")
            or ""
        ).strip().lower()

        if trigger_mode != "any_keyword":
            keywords = (
                flow_definition.get("keywords")
                or trigger_config.get("keywords")
                or flow_definition.get("trigger_keywords")
                or []
            )
            if len(keywords) > 3 and not has_feature(tier, "expanded_keywords"):
                return False, f"The Free plan supports up to 3 trigger keywords (you specified {len(keywords)}). Upgrade to Premium for unlimited keywords."

        # 7. Live Comment -> PRO
        live_comment = flow_definition.get("liveCommentEnabled") or flow_definition.get("trigger_type") == "LIVE_COMMENT"
        if live_comment and not has_feature(tier, "live_comment"):
            return False, "Live Comment Automation is exclusive to the Pro plan (₹399/mo). Please upgrade to unlock."

        # 8. AI Smart Assistant -> PRO
        ai_enabled = flow_definition.get("aiSmartAssistantEnabled") or flow_definition.get("use_ai_assistant")
        if ai_enabled and not has_feature(tier, "ai_smart_assistant"):
            return False, "AI Smart Assistant is exclusive to the Pro plan (₹399/mo). Please upgrade to unlock."

        # 9. Appointment Booking -> PRO
        booking = flow_definition.get("appointmentBookingEnabled") or flow_definition.get("booking_flow")
        if booking and not has_feature(tier, "appointment_booking"):
            return False, "Appointment Booking is exclusive to the Pro plan (₹399/mo). Please upgrade to unlock."

        # 10. Create Lead Flow (Comment to Lead) -> PRO
        flow_type = str(flow_definition.get("type", "")).upper()
        if flow_type in ("COMMENT_TO_LEAD", "LEAD_FLOW") and not has_feature(tier, "create_lead_flow"):
            return False, "Create Lead Flow requires a Pro plan (₹399/mo). Please upgrade to unlock."

        # 11. DM Reply -> PRO
        if flow_type == "DM_REPLY" and not has_feature(tier, "dm_reply"):
            return False, "DM Reply Flow requires a Pro plan (₹399/mo). Please upgrade to unlock."

        # 12. DM to Lead Collection -> PRO
        if flow_type == "DM_TO_LEAD" and not has_feature(tier, "dm_to_lead"):
            return False, "DM to Lead Collection requires a Pro plan (₹399/mo). Please upgrade to unlock."

        return True, None

    @staticmethod
    async def check_and_register_post_quota(
        workspace: Workspace,
        media_id: str,
        db: AsyncSession,
        instagram_account_id: Optional[uuid.UUID] = None
    ) -> Tuple[bool, Optional[str]]:
        """
        Checks if workspace is allowed to automate this media_id.
        Free plan allows max 10 posts total.
        If allowed, ensures a post_usage record exists for this media_id.
        """
        tier = (workspace.plan_tier or "FREE").upper()
        cfg = get_plan_config(tier)
        max_posts = cfg.get("max_posts_quota", 10)

        # Pro / Unlimited (-1)
        if max_posts == -1 or max_posts is None:
            await PlanService._ensure_post_usage_exists(workspace.id, media_id, db, instagram_account_id)
            return True, None

        # Check if media_id is already registered
        stmt = select(PostUsage).where(
            PostUsage.workspace_id == workspace.id,
            PostUsage.media_id == str(media_id)
        )
        res = await db.execute(stmt)
        existing = res.scalars().first()

        if existing:
            return True, None

        # Check current distinct post count
        count_stmt = select(func.count(PostUsage.id)).where(PostUsage.workspace_id == workspace.id)
        count_res = await db.execute(count_stmt)
        current_count = count_res.scalar() or 0

        if current_count >= max_posts:
            return (
                False,
                f"You have reached your {cfg['name']} plan limit of {max_posts} automated posts. "
                "Upgrade to Premium or Pro to automate more posts."
            )

        # Register post usage
        await PlanService._ensure_post_usage_exists(workspace.id, media_id, db, instagram_account_id)
        return True, None

    @staticmethod
    async def _ensure_post_usage_exists(
        workspace_id: uuid.UUID,
        media_id: str,
        db: AsyncSession,
        instagram_account_id: Optional[uuid.UUID] = None
    ) -> PostUsage:
        """Idempotently ensure a PostUsage record exists."""
        stmt = select(PostUsage).where(
            PostUsage.workspace_id == workspace_id,
            PostUsage.media_id == str(media_id)
        )
        res = await db.execute(stmt)
        record = res.scalars().first()
        if not record:
            record = PostUsage(
                id=uuid.uuid4(),
                workspace_id=workspace_id,
                instagram_account_id=instagram_account_id,
                media_id=str(media_id),
                dms_delivered_count=0
            )
            db.add(record)
            await db.flush()
        return record

    @staticmethod
    async def check_dm_quota_for_post(
        workspace: Workspace,
        media_id: str,
        db: AsyncSession
    ) -> Tuple[bool, Optional[str]]:
        """
        Enforce max DMs per post (99 DMs per post for Free tier).
        """
        tier = (workspace.plan_tier or "FREE").upper()
        cfg = get_plan_config(tier)
        max_dms = cfg.get("max_dms_per_post", 99)

        if not media_id or media_id in ("all", "all_posts", "global"):
            return True, None

        stmt = select(PostUsage).where(
            PostUsage.workspace_id == workspace.id,
            PostUsage.media_id == str(media_id)
        )
        res = await db.execute(stmt)
        record = res.scalars().first()

        current_dms = record.dms_delivered_count if record else 0
        if current_dms >= max_dms:
            return (
                False,
                f"Post limit reached: {cfg['name']} plan allows {max_dms} DMs per post ({current_dms} delivered). "
                "Upgrade to Premium (2,500 DMs/post) or Pro (10,000 DMs/post) to continue."
            )

        return True, None

    @staticmethod
    async def record_dm_delivered(
        workspace_id: uuid.UUID,
        media_id: str,
        db: AsyncSession,
        instagram_account_id: Optional[uuid.UUID] = None
    ) -> None:
        """
        Increment the DM delivered count for this post atomically.
        Only called on SUCCESSFUL message delivery to prevent burning quota on failed attempts.
        """
        if not media_id or media_id in ("all", "all_posts", "global"):
            return

        record = await PlanService._ensure_post_usage_exists(workspace_id, media_id, db, instagram_account_id)
        record.dms_delivered_count += 1
        record.last_delivered_at = datetime.now(timezone.utc)
        record.updated_at = datetime.now(timezone.utc)
        await db.commit()

    @staticmethod
    async def get_workspace_usage_summary(
        workspace: Workspace,
        db: AsyncSession
    ) -> Dict[str, Any]:
        """
        Returns full usage summary: plan name, posts used/limit, DMs per post limit,
        and active automations.
        """
        tier = (workspace.plan_tier or "FREE").upper()
        cfg = get_plan_config(tier)

        # Count distinct posts automated
        post_count_stmt = select(func.count(PostUsage.id)).where(PostUsage.workspace_id == workspace.id)
        post_count_res = await db.execute(post_count_stmt)
        posts_used = post_count_res.scalar() or 0

        # Sum total DMs across all posts
        total_dms_stmt = select(func.sum(PostUsage.dms_delivered_count)).where(PostUsage.workspace_id == workspace.id)
        total_dms_res = await db.execute(total_dms_stmt)
        total_dms_delivered = total_dms_res.scalar() or 0

        # Count active automations
        auto_count_stmt = select(func.count(Automation.id)).where(
            Automation.workspace_id == workspace.id,
            Automation.status == "ACTIVE"
        )
        auto_count_res = await db.execute(auto_count_stmt)
        active_automations = auto_count_res.scalar() or 0

        posts_limit = cfg.get("max_posts_quota", 10)
        posts_remaining = (posts_limit - posts_used) if posts_limit != -1 else 999999

        return {
            "plan_tier": tier,
            "plan_name": cfg.get("name", "Free"),
            "plan_status": workspace.plan_status or "ACTIVE",
            "price_inr": cfg.get("price_inr", 0),
            "billing_period": cfg.get("billing_period", "month"),
            "posts_used": posts_used,
            "posts_limit": posts_limit,
            "posts_remaining": max(0, posts_remaining),
            "max_dms_per_post": cfg.get("max_dms_per_post", 99),
            "total_dms_delivered": total_dms_delivered,
            "active_automations": active_automations,
            "max_automations": cfg.get("max_automations", 10),
            "features": cfg.get("features", {}),
            "is_post_quota_reached": posts_limit != -1 and posts_used >= posts_limit,
        }
