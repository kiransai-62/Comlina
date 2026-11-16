# server/app/engine/trigger_engine.py
import logging
import re
import unicodedata
from typing import Any, Dict, List, Optional
from app.core.logging import log_event

logger = logging.getLogger(__name__)

PUNCTUATION_RE = re.compile(r"[^\w\s]", flags=re.UNICODE)
COMMENT_TRIGGER_TYPES = {"COMMENT", "COMMENT_TO_DM", "COMMENT_REPLY", "COMMENT_TO_LEAD", "COMMENT_KEYWORD", "COMMENT_ANY", "SPECIFIC_WORDS", "ANY_WORD"}
MESSAGING_TRIGGER_TYPES = {"MESSAGING", "DM", "DM_REPLY", "DM_TO_LEAD", "STORY_REPLY", "STORY_MENTION"}


def normalize_text(text: str, strip_punctuation: bool = False) -> str:
    if not text:
        return ""
    norm = unicodedata.normalize("NFKC", str(text)).casefold()
    if strip_punctuation:
        norm = PUNCTUATION_RE.sub(" ", norm)
    return " ".join(norm.split())


def matches_specific_words(
    comment_text: str,
    keywords: List[str],
    match_mode: str = "CONTAINS",
) -> Optional[str]:
    """
    Returns the matched keyword string if comment_text satisfies the configured keywords,
    or None if no keyword matches.
    """
    raw_norm = normalize_text(comment_text, strip_punctuation=False)
    clean_norm = normalize_text(comment_text, strip_punctuation=True)
    if not raw_norm and not clean_norm:
        return None

    clean_words = set(clean_norm.split())
    valid_keywords = [str(k).strip() for k in (keywords or []) if str(k).strip()]
    if not valid_keywords:
        return None

    mode = (match_mode or "CONTAINS").upper()

    for kw in valid_keywords:
        kw_raw = normalize_text(kw, strip_punctuation=False)
        kw_clean = normalize_text(kw, strip_punctuation=True)
        if not kw_raw and not kw_clean:
            continue

        if mode == "EXACT":
            if raw_norm == kw_raw or (kw_clean and clean_norm == kw_clean):
                return kw
        else:
            # 1. Single word keyword: match whole word token or boundary (e.g. "price!" matches "price", but "priceless" does not)
            if kw_clean and " " not in kw_clean:
                if kw_clean in clean_words:
                    return kw
                pattern = rf"(?:\b|^){re.escape(kw_clean)}(?:\b|$)"
                if re.search(pattern, clean_norm):
                    return kw
            # 2. Multi-word phrase (contains spaces)
            elif kw_clean and " " in kw_clean:
                pattern = rf"(?:\b|^){re.escape(kw_clean)}(?:\b|$)"
                if re.search(pattern, clean_norm):
                    return kw
            # 3. Pure emoji / non-alphanumeric keywords (e.g. "🔥")
            elif not kw_clean and kw_raw:
                if kw_raw in raw_norm:
                    return kw

    return None


class TriggerEngine:
    @classmethod
    def evaluate(
        cls,
        trigger_config: Dict[str, Any],
        event_context: Dict[str, Any],
        correlation_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        comment_text = str(event_context.get("comment_text") or event_context.get("text") or "").strip()
        incoming_media_id = str(event_context.get("media_id") or event_context.get("post_id") or "").strip()
        configured_media_id = str(
            trigger_config.get("media_id")
            or trigger_config.get("post_id")
            or trigger_config.get("selectedPostId")
            or "ALL"
        ).strip()

        # 1. Validate non-empty comment
        if not comment_text:
            log_event(
                logger,
                "TRIGGER_MATCH",
                status="REJECTED_EMPTY_COMMENT",
                correlation_id=correlation_id,
            )
            return {"matched": False, "reason": "EMPTY_COMMENT"}

        # 2. Match Selected Post / Reel Media ID
        media_matched = (
            not configured_media_id
            or configured_media_id.upper() == "ALL"
            or incoming_media_id == configured_media_id
        )
        log_event(
            logger,
            "MEDIA_ID_MATCH",
            status="MATCHED" if media_matched else "MISMATCH",
            correlation_id=correlation_id,
            configured_media_id=configured_media_id,
            incoming_media_id=incoming_media_id,
        )
        if not media_matched:
            return {
                "matched": False,
                "reason": "MEDIA_ID_MISMATCH",
                "configured_media_id": configured_media_id,
                "incoming_media_id": incoming_media_id,
            }

        # 3. Evaluate Trigger Type: ANY_WORD vs SPECIFIC_WORDS
        raw_type = str(
            trigger_config.get("trigger_type")
            or trigger_config.get("type")
            or "SPECIFIC_WORDS"
        ).upper()

        if raw_type in ("ANY_WORD", "ANY", "COMMENT_ANY", "ALL_COMMENTS"):
            log_event(
                logger,
                "TRIGGER_MATCH",
                status="MATCHED",
                correlation_id=correlation_id,
                trigger_type="ANY_WORD",
                matched_keyword="*",
            )
            return {
                "matched": True,
                "trigger_type": "ANY_WORD",
                "matched_keyword": "*",
            }

        keywords = trigger_config.get("keywords") or []
        match_mode = str(trigger_config.get("match_mode") or "CONTAINS").upper()
        matched_kw = matches_specific_words(comment_text, keywords, match_mode=match_mode)

        if matched_kw is not None:
            log_event(
                logger,
                "TRIGGER_MATCH",
                status="MATCHED",
                correlation_id=correlation_id,
                trigger_type="SPECIFIC_WORDS",
                matched_keyword=matched_kw,
            )
            return {
                "matched": True,
                "trigger_type": "SPECIFIC_WORDS",
                "matched_keyword": matched_kw,
            }

        log_event(
            logger,
            "TRIGGER_MATCH",
            status="NO_MATCH",
            correlation_id=correlation_id,
            trigger_type="SPECIFIC_WORDS",
        )
        return {"matched": False, "reason": "NO_KEYWORD_MATCH"}

    @classmethod
    def evaluate_trigger(cls, flow_or_trigger: Dict[str, Any], event_data: Dict[str, Any]) -> bool:
        if not flow_or_trigger:
            return False

        if isinstance(flow_or_trigger, dict) and "trigger" in flow_or_trigger and isinstance(flow_or_trigger["trigger"], dict):
            trigger_config = flow_or_trigger["trigger"]
        else:
            trigger_config = flow_or_trigger

        trigger_type = str(trigger_config.get("type", "")).upper()
        event_type = str(event_data.get("event_type", "COMMENT")).upper()

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

        selected_post_id = trigger_config.get("selectedPostId") or trigger_config.get("postId") or trigger_config.get("media_id")
        if selected_post_id and str(selected_post_id).strip().lower() not in ("all", "", "none"):
            current_post = str(event_data.get("post_id") or event_data.get("media_id") or "").strip()
            if not current_post or current_post != str(selected_post_id).strip():
                return False

        posts_scope = str(trigger_config.get("postsScope", "ALL")).upper()
        if posts_scope == "SPECIFIC":
            allowed_posts = [str(p).strip() for p in trigger_config.get("postIds", []) if str(p).strip()]
            current_post = str(event_data.get("post_id") or event_data.get("media_id") or "").strip()
            if not current_post or (allowed_posts and current_post not in allowed_posts):
                return False

        trigger_mode = (
            trigger_config.get("triggerMode")
            or (isinstance(flow_or_trigger, dict) and flow_or_trigger.get("triggerMode"))
            or ""
        )
        if isinstance(trigger_mode, str):
            trigger_mode = trigger_mode.strip().lower()

        if trigger_mode in ("any_keyword", "any_word") or trigger_type in ("ANY_WORD", "COMMENT_ANY"):
            return True

        if trigger_config.get("replyToAll") is True:
            return True

        keywords = trigger_config.get("keywords") or []
        if not keywords:
            return False

        text = (event_data.get("text") or event_data.get("comment_text") or "").strip()
        if not text:
            return False

        match_whole_words = trigger_config.get("matchWholeWords", True)
        mode = "EXACT" if (trigger_config.get("match_mode") == "EXACT") else "CONTAINS"
        kw_match = matches_specific_words(text, keywords, match_mode=mode)
        if kw_match is not None:
            return True

        for kw in keywords:
            kw_str = str(kw).strip().lower()
            if not kw_str:
                continue
            try:
                if match_whole_words:
                    pattern = rf"(?:\b|^|\s){re.escape(kw_str)}(?:\b|$|\s)"
                    if re.search(pattern, text, re.IGNORECASE):
                        return True
                else:
                    if kw_str in text.lower():
                        return True
            except Exception:
                if kw_str in text.lower():
                    return True

        return False
