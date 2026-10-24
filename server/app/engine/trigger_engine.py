# server/app/engine/trigger_engine.py
import re
from typing import Dict, Any, List

COMMENT_TRIGGER_TYPES = {"COMMENT", "COMMENT_TO_DM", "COMMENT_REPLY", "COMMENT_TO_LEAD"}
MESSAGING_TRIGGER_TYPES = {"MESSAGING", "DM", "DM_REPLY", "DM_TO_LEAD", "STORY_REPLY", "STORY_MENTION"}

class TriggerEngine:
    """
    Evaluates whether an incoming event satisfies an automation trigger.
    Supports both v1 (trigger dict) and v2 Studio playbooks
    (COMMENT_TO_DM, COMMENT_REPLY, COMMENT_TO_LEAD, DM_REPLY, STORY_REPLY, STORY_MENTION).
    """
    @staticmethod
    def evaluate_trigger(flow_or_trigger: Dict[str, Any], event_data: Dict[str, Any]) -> bool:
        if not flow_or_trigger:
            return False

        # If full flow_definition is passed, extract trigger configuration
        if isinstance(flow_or_trigger, dict) and "trigger" in flow_or_trigger and isinstance(flow_or_trigger["trigger"], dict):
            trigger_config = flow_or_trigger["trigger"]
        else:
            trigger_config = flow_or_trigger

        trigger_type = str(trigger_config.get("type", "")).upper()
        event_type = str(event_data.get("event_type", "COMMENT")).upper()

        # 1. Event type compatibility check
        is_comment_event = event_type in ("COMMENT", "FEED", "COMMENTS")
        is_messaging_event = event_type in ("MESSAGING", "MESSAGES", "DM")

        if is_comment_event:
            if trigger_type and trigger_type not in COMMENT_TRIGGER_TYPES and trigger_type != event_type:
                return False
        elif is_messaging_event:
            if trigger_type and trigger_type not in MESSAGING_TRIGGER_TYPES and trigger_type != event_type:
                return False
        else:
            if trigger_type != event_type:
                return False

        # 2. Scope check (specific post vs all posts)
        # v2 Studio: selectedPostId / postId
        selected_post_id = trigger_config.get("selectedPostId") or trigger_config.get("postId")
        if selected_post_id and str(selected_post_id).strip().lower() not in ("all", "", "none"):
            current_post = str(event_data.get("post_id") or "").strip()
            # F7: If locked to a specific post, event MUST carry that post_id
            if not current_post or current_post != str(selected_post_id).strip():
                return False

        # v1: postsScope + postIds
        posts_scope = str(trigger_config.get("postsScope", "ALL")).upper()
        if posts_scope == "SPECIFIC":
            allowed_posts = [str(p).strip() for p in trigger_config.get("postIds", []) if str(p).strip()]
            current_post = str(event_data.get("post_id") or "").strip()
            # F7: If postsScope is SPECIFIC, event MUST carry a matching post_id in allowed_posts
            if not current_post or (allowed_posts and current_post not in allowed_posts):
                return False

        # 3. Explicit triggerMode check: "specific_keywords" vs "any_keyword"
        trigger_mode = (
            trigger_config.get("triggerMode")
            or (isinstance(flow_or_trigger, dict) and flow_or_trigger.get("triggerMode"))
            or ""
        )
        if isinstance(trigger_mode, str):
            trigger_mode = trigger_mode.strip().lower()

        if trigger_mode == "any_keyword":
            # Enable automation for any eligible comment on the selected post or Reel,
            # regardless of its text.
            return True
        elif trigger_mode == "specific_keywords":
            keywords = trigger_config.get("keywords") or []
            if not keywords:
                return False
            # Fall through to keyword matching below
        else:
            # 4. Backward compatibility: Fail closed if no keywords and replyToAll is not True
            reply_to_all = trigger_config.get("replyToAll")
            if reply_to_all is True:
                return True

            keywords = trigger_config.get("keywords")
            if not keywords:
                # F7: Fail closed. If no keywords and not explicitly replyToAll=True, do not trigger.
                return False

        # 5. Keyword matching (for specific_keywords mode or legacy keyword configs)
        keywords = trigger_config.get("keywords") or []
        if not keywords:
            return False

        text = (event_data.get("text") or "").strip().lower()
        if not text:
            return False

        match_whole_words = trigger_config.get("matchWholeWords", True)

        for kw in keywords:
            kw_str = str(kw).strip().lower()
            if not kw_str:
                continue

            # Support single keywords (e.g. 'ai', 'link') and multi-word phrases (e.g. 'send me')
            try:
                if match_whole_words:
                    pattern = rf"(?:\b|^|\s){re.escape(kw_str)}(?:\b|$|\s)"
                    if re.search(pattern, text, re.IGNORECASE):
                        return True
                else:
                    if kw_str in text:
                        return True
            except Exception:
                if kw_str in text:
                    return True

        return False
