# server/app/engine/condition_engine.py
from typing import Dict, Any, List, Tuple

class ConditionEngine:
    """
    Evaluates workflow conditions.
    Safely handles 4 explicit follower states:
    - FOLLOWING
    - NOT_FOLLOWING
    - UNKNOWN
    - CHECK_UNAVAILABLE
    """
    @classmethod
    def evaluate(cls, conditions: List[Dict[str, Any]], event_context: Dict[str, Any]) -> Dict[str, Any]:
        if not conditions:
            return {"passed": True, "follow_gate_required": False, "reason": "NO_CONDITIONS"}

        for cond in conditions:
            if not cond.get("enabled", True):
                continue

            cond_type = str(cond.get("type") or "").upper()
            if cond_type in ("IS_FOLLOWER", "FOLLOW_CHECK", "FOLLOW_THE_PAGE"):
                follower_status = str(event_context.get("follower_status") or "UNKNOWN").upper()
                if follower_status == "FOLLOWING":
                    continue

                if follower_status == "NOT_FOLLOWING":
                    return {
                        "passed": False,
                        "follow_gate_required": True,
                        "follower_status": "NOT_FOLLOWING",
                        "prompt_message": cond.get("prompt_message")
                        or "Please follow our page first, then tap the button below to receive your link!",
                        "button_title": cond.get("button_title") or "I'm Following ✅",
                        "reason": "USER_NOT_FOLLOWING",
                    }

                # follower_status is CHECK_UNAVAILABLE or UNKNOWN:
                # Never falsely mark as FOLLOWING! Report the limitation explicitly.
                strict_policy = str(cond.get("unavailable_policy") or "SEND_FOLLOW_GATE").upper()
                return {
                    "passed": False,
                    "follow_gate_required": strict_policy == "SEND_FOLLOW_GATE",
                    "follower_status": follower_status,
                    "limitation": event_context.get("follower_limitation")
                    or "Meta API does not expose follower status for this comment event.",
                    "prompt_message": cond.get("prompt_message")
                    or "Please make sure you follow our page, then tap the button below to unlock your DM!",
                    "button_title": cond.get("button_title") or "I'm Following ✅",
                    "reason": f"FOLLOWER_{follower_status}",
                }

        return {"passed": True, "follow_gate_required": False, "reason": "ALL_CONDITIONS_PASSED"}

    @staticmethod
    def evaluate_follower_condition(
        condition_config: Dict[str, Any],
        actual_follower_status: str
    ) -> Tuple[bool, str]:
        """
        Returns (passed: bool, next_action_override: str).
        """
        expected = condition_config.get("expected", "FOLLOWING")
        fallback_action = condition_config.get("fallbackAction", "SEND_FOLLOW_GATE")

        if actual_follower_status == "FOLLOWING":
            if expected == "FOLLOWING":
                return True, "CONTINUE"
            return False, fallback_action

        elif actual_follower_status == "NOT_FOLLOWING":
            # Verified non-follower -> Trigger Follow Gate
            return False, "SEND_FOLLOW_GATE"

        elif actual_follower_status == "CHECK_UNAVAILABLE":
            # Verification unavailable -> Distinct action override (never treat as NOT_FOLLOWING or FOLLOWING)
            return False, condition_config.get("onUnavailableAction") or fallback_action

        elif actual_follower_status == "UNKNOWN":
            # Unknown status (e.g. missing IDs)
            return False, condition_config.get("onUnknownAction") or fallback_action

        return False, fallback_action

    @staticmethod
    def evaluate_condition(
        condition: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Tuple[bool, str]:
        cond_type = condition.get("type")

        if cond_type == "FOLLOWER_STATUS":
            follower_status = context.get("follower_status", "UNKNOWN")
            return ConditionEngine.evaluate_follower_condition(condition, follower_status)

        elif cond_type == "KEYWORD_MATCH":
            text = (context.get("text") or "").lower()
            keyword = condition.get("keyword", "").lower()
            if keyword in text:
                return True, "CONTINUE"
            return False, condition.get("fallbackAction", "STOP")

        return True, "CONTINUE"
