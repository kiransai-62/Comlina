# worker/app/engine/condition_engine.py
from typing import Dict, Any, Tuple

class ConditionEngine:
    """
    Evaluates workflow conditions.
    Safely handles 4 explicit follower states:
    - FOLLOWING
    - NOT_FOLLOWING
    - UNKNOWN
    - CHECK_UNAVAILABLE
    """
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
            # Direct non-follower -> Trigger Follow Gate
            return False, "SEND_FOLLOW_GATE"

        elif actual_follower_status in ("UNKNOWN", "CHECK_UNAVAILABLE"):
            # Safe degradation fallback
            return False, fallback_action

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
