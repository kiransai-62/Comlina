# server/app/engine/flow_engine.py
import logging
from typing import Dict, Any, List, Optional
from app.engine.trigger_engine import TriggerEngine
from app.engine.condition_engine import ConditionEngine
from app.engine.action_engine import ActionEngine
from app.integrations.instagram.follower_status import InstagramFollowerService

logger = logging.getLogger("flow_engine")

class FlowEngine:
    """
    Coordinates execution of an automation workflow definition (DAG):
    Trigger -> Conditions -> Actions.
    Supports both v1 DAGs and v2 Studio playbooks (Comment-to-DM, Comment Reply, DM Reply).
    """

    @staticmethod
    def _extract_conditions(flow_definition: Dict[str, Any]) -> List[Dict[str, Any]]:
        # If explicitly defined as v1 list of conditions:
        if "conditions" in flow_definition and isinstance(flow_definition["conditions"], list):
            return flow_definition["conditions"]

        conditions = []
        # v2 Studio playbook: askFollow
        ask_follow = flow_definition.get("askFollow")
        if isinstance(ask_follow, dict) and ask_follow.get("enabled"):
            conditions.append({
                "type": "FOLLOWER_STATUS",
                "expected": "FOLLOWING",
                "fallbackAction": "SEND_FOLLOW_GATE",
                "message": ask_follow.get("message"),
                "retryMessage": ask_follow.get("retryMessage"),
                "successMessage": ask_follow.get("successMessage"),
                "buttonLabel": ask_follow.get("buttonLabel", "Follow"),
            })
        return conditions

    @staticmethod
    def _extract_actions(flow_definition: Dict[str, Any]) -> List[Dict[str, Any]]:
        # If explicitly defined as v1 list of actions:
        if "actions" in flow_definition and isinstance(flow_definition["actions"], list):
            return flow_definition["actions"]

        actions = []
        # 1. PUBLIC_REPLY (from teaserReply.message or replyText)
        teaser = flow_definition.get("teaserReply")
        if isinstance(teaser, dict) and teaser.get("enabled") and teaser.get("message"):
            actions.append({
                "type": "PUBLIC_REPLY",
                "text": teaser.get("message")
            })
        elif flow_definition.get("replyText"):
            actions.append({
                "type": "PUBLIC_REPLY",
                "text": flow_definition.get("replyText")
            })

        # 2. PRIVATE_DM (from responseDm.message + responseDm.buttons)
        response_dm = flow_definition.get("responseDm")
        if isinstance(response_dm, dict) and response_dm.get("message"):
            actions.append({
                "type": "PRIVATE_DM",
                "text": response_dm.get("message"),
                "buttons": response_dm.get("buttons") or []
            })
        elif flow_definition.get("dmMessage"):
            actions.append({
                "type": "PRIVATE_DM",
                "text": flow_definition.get("dmMessage"),
                "buttons": flow_definition.get("buttons") or []
            })

        return actions

    @staticmethod
    async def run_flow(
        flow_definition: Dict[str, Any],
        event_data: Dict[str, Any],
        instagram_client: Any = None,
        db_session: Any = None
    ) -> Dict[str, Any]:
        results: List[Dict[str, Any]] = []

        # 1. Trigger Check: support v1 (flow_definition["trigger"]) and v2 top-level playbook
        trigger_config = flow_definition.get("trigger") or flow_definition
        if not TriggerEngine.evaluate_trigger(trigger_config, event_data):
            return {"status": "TRIGGER_MISMATCH", "results": []}

        logger.info(f"Trigger matched for event {event_data.get('provider_event_id')}")

        # 2. Extract conditions (v1 or v2)
        conditions = FlowEngine._extract_conditions(flow_definition)

        # Pre-condition check: resolve follower status if needed
        has_follower_cond = any(c.get("type") == "FOLLOWER_STATUS" for c in conditions)
        if has_follower_cond and instagram_client and "follower_status" not in event_data:
            business_ig_id = event_data.get("business_ig_id")
            sender_id = event_data.get("sender_id")
            if business_ig_id and sender_id:
                follower_service = InstagramFollowerService(instagram_client)
                status, _ = await follower_service.check_follower_status(business_ig_id, sender_id)
                event_data["follower_status"] = status.value

        # 3. Condition Checks
        for cond in conditions:
            passed, fallback = ConditionEngine.evaluate_condition(cond, event_data)
            if not passed:
                logger.info(f"Condition not passed. Executing fallback: {fallback}")
                if fallback == "SEND_FOLLOW_GATE":
                    follow_gate_msg = (
                        cond.get("message")
                        or "Thanks for your comment! Please follow our account first so we can send you the direct download link 🚀"
                    )
                    follow_gate_action = {
                        "type": "PRIVATE_DM",
                        "text": follow_gate_msg
                    }
                    res = await ActionEngine.execute_action(follow_gate_action, event_data, instagram_client, db_session)
                    results.append(res)
                return {"status": "FALLBACK_EXECUTED", "results": results}

        # 4. Actions Execution Pipeline
        actions = FlowEngine._extract_actions(flow_definition)
        for action in actions:
            action_res = await ActionEngine.execute_action(action, event_data, instagram_client, db_session)
            results.append(action_res)

        return {"status": "COMPLETED", "results": results}
