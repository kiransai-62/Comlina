# server/app/core/plans.py
"""
Comlina Centralized Plan Configuration & Entitlements

Defines Free, Premium (₹199/month), and Pro (₹399/month) tiers,
feature entitlements, and usage quotas.
"""

from enum import Enum
from typing import Dict, Any, Optional


class PlanTier(str, Enum):
    FREE = "FREE"
    PREMIUM = "PREMIUM"
    PRO = "PRO"


# Feature Keys
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


# Centralized Quotas & Pricing
PLAN_CONFIG: Dict[PlanTier, Dict[str, Any]] = {
    PlanTier.FREE: {
        "id": "FREE",
        "name": "Free",
        "price_inr": 0,
        "price_paise": 0,
        "billing_period": "month",
        "max_posts_quota": 10,       # Maximum 10 posts total per user (lifetime / configurable)
        "max_dms_per_post": 99,      # Maximum 99 DMs per post
        "max_automations": 10,
        "max_accounts": 1,
        "features": {
            "comment_to_dm_basic": True,
            "trigger_response_dm": True,
            "basic_keywords": True,           # Up to 3 trigger keywords
            "reply_to_all": False,            # Locked: PREMIUM
            "ask_to_follow": False,           # Locked: PREMIUM
            "comment_teaser_reply": False,    # Locked: PREMIUM
            "dm_buttons": False,              # Locked: PREMIUM
            "follow_up_dms": False,           # Locked: PREMIUM
            "expanded_keywords": False,       # Locked: PREMIUM (>3 keywords, phrase match)
            "live_comment": False,            # Locked: PRO
            "ai_smart_assistant": False,      # Locked: PRO
            "appointment_booking": False,     # Locked: PRO
            "advanced_workflows": False,      # Locked: PRO
        },
        "description": "Essential Comment-to-DM automation for creators getting started.",
    },
    PlanTier.PREMIUM: {
        "id": "PREMIUM",
        "name": "Premium",
        "price_inr": 199,
        "price_paise": 19900,
        "billing_period": "month",
        "max_posts_quota": 100,      # Configurable post limit
        "max_dms_per_post": 2500,    # Configurable DM limit per post
        "max_automations": 50,
        "max_accounts": 3,
        "features": {
            "comment_to_dm_basic": True,
            "trigger_response_dm": True,
            "basic_keywords": True,
            "reply_to_all": True,
            "ask_to_follow": True,
            "comment_teaser_reply": True,
            "dm_buttons": True,
            "follow_up_dms": True,
            "expanded_keywords": True,
            "live_comment": False,            # Locked: PRO
            "ai_smart_assistant": False,      # Locked: PRO
            "appointment_booking": False,     # Locked: PRO
            "advanced_workflows": False,      # Locked: PRO
        },
        "description": "Advanced conversion tools: Ask to Follow, Teaser replies, and multi-step follow-ups.",
    },
    PlanTier.PRO: {
        "id": "PRO",
        "name": "Pro",
        "price_inr": 399,
        "price_paise": 39900,
        "billing_period": "month",
        "max_posts_quota": -1,       # -1 indicates highest / unlimited posts
        "max_dms_per_post": 10000,   # Configurable high-volume limit
        "max_automations": 200,
        "max_accounts": 10,
        "features": {
            "comment_to_dm_basic": True,
            "trigger_response_dm": True,
            "basic_keywords": True,
            "reply_to_all": True,
            "ask_to_follow": True,
            "comment_teaser_reply": True,
            "dm_buttons": True,
            "follow_up_dms": True,
            "expanded_keywords": True,
            "live_comment": True,
            "ai_smart_assistant": True,
            "appointment_booking": True,
            "advanced_workflows": True,
        },
        "description": "Power workflows: Live Comment automation, AI Smart Assistant, and Appointment Booking.",
    },
}


def get_plan_config(plan_tier: Optional[str]) -> Dict[str, Any]:
    """Retrieve plan configuration by tier string, defaulting to FREE."""
    if not plan_tier:
        return PLAN_CONFIG[PlanTier.FREE]
    try:
        tier_enum = PlanTier(plan_tier.upper())
        return PLAN_CONFIG[tier_enum]
    except (ValueError, KeyError):
        return PLAN_CONFIG[PlanTier.FREE]


def has_feature(plan_tier: Optional[str], feature_key: str) -> bool:
    """Return True if the specified plan tier has access to the feature."""
    cfg = get_plan_config(plan_tier)
    return bool(cfg.get("features", {}).get(feature_key, False))


def get_required_plan_for_feature(feature_key: str) -> str:
    """Return the minimum plan tier string required to unlock a feature."""
    # Check if Free has it
    if PLAN_CONFIG[PlanTier.FREE]["features"].get(feature_key, False):
        return "FREE"
    # Check if Premium has it
    if PLAN_CONFIG[PlanTier.PREMIUM]["features"].get(feature_key, False):
        return "PREMIUM"
    # Otherwise Pro
    return "PRO"
