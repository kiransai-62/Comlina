# server/app/engine/flow_engine.py
import logging
from typing import Dict, Any, List, Optional
from .trigger_engine import TriggerEngine
from .condition_engine import ConditionEngine
from .action_engine import ActionEngine
from app.integrations.instagram.follower_status import InstagramFollowerService

logger = logging.getLogger("flow_engine")

class FlowEngine:
    """
    Coordinates execution of an automation workflow definition:
    Trigger -> Follow Verification -> Private DM Delivery -> Public Teaser Reply.
    Supports both v1 DAGs and v2 Studio playbooks (Comment-to-DM, Comment Reply, DM Reply).
    """

    @staticmethod
    def _extract_conditions(flow_definition: Dict[str, Any]) -> List[Dict[str, Any]]:
        if "conditions" in flow_definition and isinstance(flow_definition["conditions"], list):
            return flow_definition["conditions"]

        conditions = []
        # Support both flow_definition["askFollow"] and flow_definition["advanced"]["askFollow"]
        advanced = flow_definition.get("advanced") or {}
        ask_follow = flow_definition.get("askFollow") or advanced.get("askFollow")
        if isinstance(ask_follow, dict) and ask_follow.get("enabled"):
            conditions.append({
                "type": "FOLLOWER_STATUS",
                "expected": "FOLLOWING",
                "fallbackAction": "SEND_FOLLOW_GATE",
                "onUnavailableAction": ask_follow.get("onUnavailableAction", "HANDLE_CHECK_UNAVAILABLE"),
                "onUnknownAction": ask_follow.get("onUnknownAction", "HANDLE_UNKNOWN"),
                "message": ask_follow.get("message"),
                "retryMessage": ask_follow.get("retryMessage"),
                "successMessage": ask_follow.get("successMessage"),
                "unavailableMessage": ask_follow.get("unavailableMessage") or ask_follow.get("fallbackMessage"),
                "buttonLabel": ask_follow.get("buttonLabel", "Follow"),
            })
        return conditions

    @staticmethod
    def _extract_dm_action(flow_definition: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        automated_dm = flow_definition.get("automatedDm") or flow_definition.get("responseDm")
        if isinstance(automated_dm, dict) and automated_dm.get("message"):
            buttons = []
            if isinstance(automated_dm.get("buttons"), list):
                buttons = automated_dm.get("buttons")
            elif isinstance(automated_dm.get("button"), dict) and automated_dm["button"].get("url"):
                btn = automated_dm["button"]
                buttons = [{"label": btn.get("label", "Open Link"), "url": btn.get("url")}]
            return {
                "type": "PRIVATE_DM",
                "text": automated_dm.get("message"),
                "buttons": buttons
            }
        elif flow_definition.get("dmMessage"):
            return {
                "type": "PRIVATE_DM",
                "text": flow_definition.get("dmMessage"),
                "buttons": flow_definition.get("buttons") or []
            }
        return None

    @staticmethod
    def _extract_teaser_action(flow_definition: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        advanced = flow_definition.get("advanced") or {}
        teaser = advanced.get("commentTeaser") or flow_definition.get("teaserReply")
        if isinstance(teaser, dict) and teaser.get("enabled"):
            msg = teaser.get("message") or "Check your DM! 📩"
            return {
                "type": "PUBLIC_REPLY",
                "text": msg
            }
        elif flow_definition.get("replyText"):
            return {
                "type": "PUBLIC_REPLY",
                "text": flow_definition.get("replyText")
            }
        return None

    @staticmethod
    def _extract_actions(flow_definition: Dict[str, Any]) -> List[Dict[str, Any]]:
        # If explicitly defined as v1 list of actions:
        if "actions" in flow_definition and isinstance(flow_definition["actions"], list):
            return flow_definition["actions"]

        actions = []
        # In definition order: Public teaser reply definition followed by DM delivery
        teaser_action = FlowEngine._extract_teaser_action(flow_definition)
        if teaser_action:
            actions.append(teaser_action)

        dm_action = FlowEngine._extract_dm_action(flow_definition)
        if dm_action:
            actions.append(dm_action)

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
            return {"status": "TRIGGER_MISMATCH", "processing_state": "processing", "results": []}

        logger.info(f"Trigger matched for event {event_data.get('provider_event_id')}")

        # Extract conditions & actions
        conditions = FlowEngine._extract_conditions(flow_definition)
        has_follower_cond = any(c.get("type") == "FOLLOWER_STATUS" for c in conditions)

        account_username = (
            event_data.get("business_username")
            or event_data.get("account_username")
            or "our account"
        )
        if account_username.startswith("@"):
            account_username = account_username[1:]

        dm_action = FlowEngine._extract_dm_action(flow_definition)
        teaser_action = FlowEngine._extract_teaser_action(flow_definition)

        # 2. Check Follower Status if Follow Gate Condition is enabled
        if has_follower_cond:
            follower_status = event_data.get("follower_status")
            follower_reason = event_data.get("follower_status_reason", "")

            if not follower_status and instagram_client:
                business_ig_id = event_data.get("business_ig_id")
                sender_id = event_data.get("sender_id")
                if business_ig_id and sender_id:
                    follower_service = InstagramFollowerService(instagram_client)
                    status_enum, follower_reason = await follower_service.check_follower_status(business_ig_id, sender_id)
                    follower_status = status_enum.value
                    event_data["follower_status"] = follower_status
                    event_data["follower_status_reason"] = follower_reason
                else:
                    follower_status = "UNKNOWN"
                    event_data["follower_status"] = "UNKNOWN"
                    event_data["follower_status_reason"] = "Missing business or sender ID"
            elif not follower_status:
                follower_status = "UNKNOWN"
                event_data["follower_status"] = "UNKNOWN"
                event_data["follower_status_reason"] = "No follower status provided"

            follower_cond = next(c for c in conditions if c.get("type") == "FOLLOWER_STATUS")
            passed, fallback = ConditionEngine.evaluate_condition(follower_cond, event_data)

            if not passed:
                logger.info(f"Follower condition not met ({follower_status}). Executing fallback: {fallback}")

                if follower_status == "NOT_FOLLOWING":
                    init_state = "follow_required"
                    gate_msg = (
                        follower_cond.get("message")
                        or f"Thanks for your comment! Please follow @{account_username} first so we can send you the direct download link 🚀"
                    )
                elif follower_status == "CHECK_UNAVAILABLE":
                    init_state = "verification_unavailable"
                    gate_msg = (
                        follower_cond.get("unavailableMessage")
                        or f"Thanks for your comment! We couldn't verify your follow status automatically. Follow @{account_username} and tap below so we can verify and send your link 🚀"
                    )
                else:  # UNKNOWN
                    init_state = "unknown_status"
                    gate_msg = (
                        follower_cond.get("unknownMessage")
                        or f"Thanks for your comment! To receive your link, Follow @{account_username} and tap below 🚀"
                    )

                # Send creator's customized Ask to Follow DM with profile link button & recheck button
                follow_gate_action = {
                    "type": "PRIVATE_DM",
                    "text": gate_msg,
                    "buttons": [
                        {
                            "label": f"Follow @{account_username}"[:20],
                            "url": f"https://instagram.com/{account_username}"
                        },
                        {
                            "label": "I followed! 🚀"[:20],
                            "payload": "VERIFY_FOLLOW"
                        }
                    ]
                }
                dm_res = await ActionEngine.execute_action(follow_gate_action, event_data, instagram_client, db_session)

                if dm_res.get("status") == "SUCCESS":
                    current_state = "follow_request_sent"
                    # Only send public teaser reply AFTER private DM has been successfully initiated!
                    if teaser_action and event_data.get("comment_id"):
                        teaser_res = await ActionEngine.execute_action(teaser_action, event_data, instagram_client, db_session)
                        results.append(teaser_res)
                        if teaser_res.get("status") == "SUCCESS":
                            current_state = "teaser_reply_sent"
                    results.append(dm_res)

                    pending_delivery = {
                        "automation_id": str(flow_definition.get("id") or ""),
                        "resource_message": dm_action.get("text") if dm_action else "",
                        "buttons": dm_action.get("buttons") if dm_action else [],
                        "retry_message": follower_cond.get("retryMessage"),
                        "account_username": account_username,
                        "business_ig_id": event_data.get("business_ig_id"),
                        "verification_status": follower_status
                    }
                    return {
                        "status": "FALLBACK_EXECUTED",
                        "processing_state": "verification_pending",
                        "prior_state": current_state,
                        "initial_state": init_state,
                        "follower_verified": False,
                        "follower_status": follower_status,
                        "pending_delivery": pending_delivery,
                        "results": results
                    }
                else:
                    # DM delivery failed -> do NOT falsely post public teaser!
                    results.append(dm_res)
                    return {
                        "status": "COMPLETED",
                        "processing_state": "failed",
                        "follower_verified": False,
                        "follower_status": follower_status,
                        "error": dm_res.get("error", "Follow gate DM delivery failed"),
                        "results": results
                    }

        # 3. User Already Follows (or askFollow is disabled) -> Eligible for Delivery
        if dm_action:
            # Deliver private DM first to verify initiation
            dm_res = await ActionEngine.execute_action(dm_action, event_data, instagram_client, db_session)

            if dm_res.get("status") == "SUCCESS":
                current_state = "resource_sent"
                # Deliver public comment teaser reply ONLY after DM succeeds!
                if teaser_action and event_data.get("comment_id"):
                    teaser_res = await ActionEngine.execute_action(teaser_action, event_data, instagram_client, db_session)
                    results.append(teaser_res)
                    if teaser_res.get("status") == "SUCCESS":
                        current_state = "teaser_reply_sent"
                results.append(dm_res)

                return {
                    "status": "COMPLETED",
                    "processing_state": current_state,
                    "follower_verified": True,
                    "follower_status": "FOLLOWING" if has_follower_cond else event_data.get("follower_status", "UNKNOWN"),
                    "results": results
                }
            else:
                # Private DM failed -> Do NOT send public teaser reply
                results.append(dm_res)
                return {
                    "status": "COMPLETED",
                    "processing_state": "failed",
                    "follower_verified": True,
                    "follower_status": "FOLLOWING" if has_follower_cond else event_data.get("follower_status", "UNKNOWN"),
                    "error": dm_res.get("error", "Protected resource DM delivery failed"),
                    "results": results
                }

        # Fallback for custom DAG actions (e.g. comment reply only or non-standard actions)
        actions = FlowEngine._extract_actions(flow_definition)
        for action in actions:
            action_res = await ActionEngine.execute_action(action, event_data, instagram_client, db_session)
            results.append(action_res)

        return {"status": "COMPLETED", "processing_state": "completed", "results": results}
