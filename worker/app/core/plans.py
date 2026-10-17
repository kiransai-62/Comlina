# worker/app/core/plans.py
"""
Comlina Centralized Plan Configuration for Worker Service
"""

from enum import Enum
from typing import Dict, Any, Optional


class PlanTier(str, Enum):
    FREE = "FREE"
    PREMIUM = "PREMIUM"
    PRO = "PRO"


FEATURE_COMMENT_TO_DM_BASIC = "comment_to_dm_basic"
FEATURE_TRIGGER_RESPONSE_DM = "trigger_response_dm"
FEATURE_BASIC_KEYWORDS = "basic_keywords"
FEATURE_REPLY_TO_ALL = "reply_to_all"
FEATURE_ASK_TO_FOLLOW = "ask_to_follow"
FEATURE_COMMENT_TEASER_REPLY = "comment_teaser_reply"
FEATURE_DM_BUTTONS = "dm_buttons"
FEATURE_FOLLOW_UP_DMS = "follow_up_dms"
FEATURE_EXPANDED_KEYWORDS = "expanded_keywords"
FEATURE_LIVE_COMMENT = "live_comment"
FEATURE_AI_SMART_ASSISTANT = "ai_smart_assistant"
FEATURE_APPOINTMENT_BOOKING = "appointment_booking"
FEATURE_ADVANCED_WORKFLOWS = "advanced_workflows"


PLAN_CONFIG: Dict[PlanTier, Dict[str, Any]] = {
    PlanTier.FREE: {
        "id": "FREE",
        "name": "Free",
        "price_inr": 0,
        "max_posts_quota": 10,
        "max_dms_per_post": 99,
    },
    PlanTier.PREMIUM: {
        "id": "PREMIUM",
        "name": "Premium",
        "price_inr": 199,
        "max_posts_quota": 100,
        "max_dms_per_post": 2500,
    },
    PlanTier.PRO: {
        "id": "PRO",
        "name": "Pro",
        "price_inr": 399,
        "max_posts_quota": -1,
        "max_dms_per_post": 10000,
    },
}


def get_plan_config(plan_tier: Optional[str]) -> Dict[str, Any]:
    if not plan_tier:
        return PLAN_CONFIG[PlanTier.FREE]
    try:
        tier_enum = PlanTier(plan_tier.upper())
        return PLAN_CONFIG[tier_enum]
    except (ValueError, KeyError):
        return PLAN_CONFIG[PlanTier.FREE]
