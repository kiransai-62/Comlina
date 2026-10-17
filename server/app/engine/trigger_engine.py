# server/app/engine/trigger_engine.py
import re
from typing import Dict, Any, List

COMMENT_TRIGGER_TYPES = {"COMMENT", "COMMENT_TO_DM", "COMMENT_REPLY", "COMMENT_TO_LEAD"}
MESSAGING_TRIGGER_TYPES = {"MESSAGING", "DM", "DM_REPLY", "DM_TO_LEAD"}

class TriggerEngine:
    """
    Evaluates whether an incoming event satisfies an automation trigger.
    Supports both v1 (trigger dict) and v2 Studio playbooks
    (COMMENT_TO_DM, COMMENT_REPLY, COMMENT_TO_LEAD, DM_REPLY).
    """
    @staticmethod
    def evaluate_trigger(trigger_config: Dict[str, Any], event_data: Dict[str, Any]) -> bool:
        if not trigger_config:
            return False

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
        # v2 Studio: selectedPostId
        selected_post_id = trigger_config.get("selectedPostId")
        if selected_post_id and str(selected_post_id).strip().lower() not in ("all", "", "none"):
            current_post = str(event_data.get("post_id") or "")
            if current_post and current_post != str(selected_post_id).strip():
                return False

        # v1: postsScope + postIds
        posts_scope = str(trigger_config.get("postsScope", "ALL")).upper()
        if posts_scope == "SPECIFIC":
            allowed_posts = [str(p) for p in trigger_config.get("postIds", [])]
            current_post = str(event_data.get("post_id") or "")
            if current_post and allowed_posts and current_post not in allowed_posts:
                return False

        # 3. Reply to all check (v2 Studio)
        reply_to_all = trigger_config.get("replyToAll")
        if reply_to_all is True:
            return True

        # 4. Keyword matching
        keywords = trigger_config.get("keywords")
        if not keywords:
            # If replyToAll is explicitly False and keywords is empty, do not trigger
            if "replyToAll" in trigger_config and not trigger_config.get("replyToAll"):
                return False
            # In legacy v1 without keywords, trigger on all comments
            return True

        text = (event_data.get("text") or "").strip().lower()
        if not text:
            return False

        for kw in keywords:
            kw_str = str(kw).strip().lower()
            if not kw_str:
                continue

            # Support single keywords (e.g. 'ai', 'link') and multi-word phrases (e.g. 'send me')
            try:
                pattern = rf"\b{re.escape(kw_str)}\b"
                if re.search(pattern, text, re.IGNORECASE):
                    return True
            except Exception:
                if kw_str in text:
                    return True

        return False
