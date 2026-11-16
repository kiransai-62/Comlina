# server/app/engine/action_engine.py
import asyncio
import logging
from typing import Dict, Any, List, Optional
import httpx
from sqlalchemy import select
from app.core.config import settings
from app.core.logging import log_event
from app.integrations.instagram import InstagramComments, InstagramMessaging
from app.integrations.instagram.client import MetaGraphClient

logger = logging.getLogger("action_engine")

def format_template(template: str, user_profile: dict) -> str:
    # Fallback to username if first_name is empty/missing
    first_name = user_profile.get("first_name") or user_profile.get("username") or "there"
    return template.replace("{first_name}", first_name).replace("{username}", user_profile.get("username", "") or "")


class ActionEngine:
    """
    Executes automation actions:
    - PRIVATE_DM (Private reply to comment or Direct Message)
    - PUBLIC_REPLY (Direct comment thread reply)
    - TAG_CONTACT (Database contact tag update)
    - DELAY (Smart asynchronous wait)
    """
    format_template = staticmethod(format_template)

    @staticmethod
    async def execute_action(
        action_config: Dict[str, Any],
        context: Dict[str, Any],
        instagram_client: Optional[MetaGraphClient] = None,
        db_session: Any = None
    ) -> Dict[str, Any]:
        action_type = action_config.get("type")
        username = context.get("sender_username", "friend")
        comment_id = context.get("comment_id")
        recipient_id = context.get("sender_id")

        user_profile = context.get("user_profile")
        if not isinstance(user_profile, dict):
            user_profile = {}
            if context.get("sender_username"):
                user_profile["username"] = context.get("sender_username")
            if context.get("first_name"):
                user_profile["first_name"] = context.get("first_name")

        if action_type == "PUBLIC_REPLY":
            text = action_config.get("text", "Thanks @{username}! Sent the details to your DMs 📩")
            profile_for_reply = user_profile if user_profile.get("username") else {**user_profile, "username": "friend"}
            formatted_text = format_template(text, profile_for_reply)
            logger.info(f"Executing PUBLIC_REPLY for comment {comment_id} (text_len={len(formatted_text)})")

            # Guard: no client means the account token is missing or undecryptable — fail explicitly.
            if not instagram_client:
                logger.error(
                    f"PUBLIC_REPLY skipped for comment {comment_id}: instagram_client is unavailable (NO_CLIENT). "
                    "Account token is missing or could not be decrypted."
                )
                return {
                    "status": "FAILED",
                    "action": "PUBLIC_REPLY",
                    "error": "Instagram client is unavailable. Account token is missing or could not be decrypted.",
                    "error_code": "NO_CLIENT",
                }

            if not comment_id:
                logger.error("PUBLIC_REPLY skipped: comment_id is missing in context.")
                return {
                    "status": "FAILED",
                    "action": "PUBLIC_REPLY",
                    "error": "Missing comment_id in event context.",
                    "error_code": "MISSING_COMMENT_ID",
                }

            res: Dict[str, Any] = {"status": "SUCCESS", "action": "PUBLIC_REPLY", "text": formatted_text}
            try:
                comments_client = InstagramComments(instagram_client)
                api_res = await comments_client.reply_to_comment(comment_id, formatted_text)
                res["meta_response"] = api_res
            except Exception as e:
                logger.error(f"Failed to post public reply to comment {comment_id}: {e}")
                res["status"] = "FAILED"
                res["error"] = str(e)
                if hasattr(e, "code"):
                    res["error_code"] = getattr(e, "code", 500)
                    res["meta_error"] = {
                        "code": getattr(e, "code", 500),
                        "subcode": getattr(e, "error_subcode", 0),
                        "message": str(e)
                    }
                if hasattr(e, "to_diagnostic_dict"):
                    res["meta_diagnostic"] = e.to_diagnostic_dict()
            return res

        elif action_type == "PRIVATE_DM":
            text = action_config.get("text", "Hey {first_name}! Here is the resource you requested.")
            buttons = action_config.get("buttons") or []
            formatted_text = format_template(text, user_profile)
            logger.info(
                f"Executing PRIVATE_DM for comment {comment_id} / recipient {recipient_id} "
                f"(text_len={len(formatted_text)}, buttons_count={len(buttons)})"
            )

            # Guard: no client means the account token is missing or undecryptable — fail explicitly.
            if not instagram_client:
                logger.error(
                    f"PRIVATE_DM skipped for comment {comment_id} / recipient {recipient_id}: "
                    "instagram_client is unavailable (NO_CLIENT). Account token is missing or could not be decrypted."
                )
                return {
                    "status": "FAILED",
                    "action": "PRIVATE_DM",
                    "error": "Instagram client is unavailable. Account token is missing or could not be decrypted.",
                    "error_code": "NO_CLIENT",
                }

            res: Dict[str, Any] = {"status": "SUCCESS", "action": "PRIVATE_DM", "text": formatted_text, "buttons": buttons}
            try:
                messaging_client = InstagramMessaging(instagram_client)
                api_res = await messaging_client.send_private_reply(
                    comment_id=comment_id,
                    message_text=formatted_text,
                    fallback_sender_id=recipient_id,
                    buttons=buttons
                )
                res["meta_response"] = api_res
                # Only record a verified message_id returned by Meta as delivery confirmation
                verified_msg_id = (api_res or {}).get("message_id") or (api_res or {}).get("id")
                if verified_msg_id:
                    res["verified_message_id"] = verified_msg_id
                else:
                    # Meta responded but did not return a message_id — treat as unverified
                    logger.warning(
                        f"PRIVATE_DM to {recipient_id or comment_id}: Meta API responded without a message_id. "
                        "Delivery cannot be confirmed — marking UNVERIFIED."
                    )
                    res["status"] = "UNVERIFIED"
                    res["delivery_note"] = "Meta response missing message_id; delivery unconfirmed."
            except Exception as e:
                logger.error(f"Failed to send private DM to {recipient_id or comment_id}: {e}")
                res["status"] = "FAILED"
                res["error"] = str(e)
                if hasattr(e, "code"):
                    res["error_code"] = getattr(e, "code", 500)
                    res["meta_error"] = {
                        "code": getattr(e, "code", 500),
                        "subcode": getattr(e, "error_subcode", 0),
                        "message": str(e)
                    }
                if hasattr(e, "to_diagnostic_dict"):
                    res["meta_diagnostic"] = e.to_diagnostic_dict()
            return res

        elif action_type == "TAG_CONTACT":
            tag = action_config.get("tag", "lead")
            contact_id = context.get("contact_id")
            logger.info(f"Executing TAG_CONTACT for contact {contact_id}: tag={tag}")
            res: Dict[str, Any] = {"status": "SUCCESS", "action": "TAG_CONTACT", "tag": tag}

            contact_id = context.get("contact_id")
            if db_session and contact_id:
                try:
                    from app.models import Contact
                    stmt = select(Contact).where(Contact.id == contact_id)
                    contact_res = await db_session.execute(stmt)
                    contact = contact_res.scalar_one_or_none()
                    if contact:
                        current_tags = list(contact.tags) if isinstance(contact.tags, list) else []
                        if tag not in current_tags:
                            current_tags.append(tag)
                            contact.tags = current_tags
                            await db_session.flush()
                except Exception as e:
                    logger.error(f"Failed to update tag for contact {contact_id}: {e}")
                    res["error"] = str(e)
            return res

        elif action_type == "DELAY":
            seconds = min(action_config.get("delaySeconds", 1), 60)
            logger.info(f"Executing DELAY for {seconds} seconds...")
            await asyncio.sleep(seconds)
            return {"status": "SUCCESS", "action": "DELAY", "seconds": seconds}

        return {"status": "SKIPPED", "action": action_type}

    @classmethod
    async def send_comment_reply(
        cls,
        comment_id: str,
        message_text: str,
        access_token: str,
        correlation_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        version = getattr(settings, "META_GRAPH_API_VERSION", None) or getattr(settings, "META_API_VERSION", "v21.0")
        url = f"https://graph.instagram.com/{version}/{comment_id}/replies"
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(
                url,
                params={"access_token": access_token},
                json={"message": message_text},
            )
            body = resp.json() if resp.content else {}
            if resp.status_code in (200, 201) and body.get("id"):
                log_event(
                    logger,
                    "ACTION_EXECUTION",
                    status="SUCCESS",
                    correlation_id=correlation_id,
                    action_type="REPLY_COMMENT",
                    comment_id=comment_id,
                    reply_id=body.get("id"),
                )
                return {"success": True, "reply_id": body["id"]}

            err_msg = body.get("error", {}).get("message") or f"HTTP {resp.status_code}"
            log_event(
                logger,
                "ACTION_EXECUTION",
                status="FAILED",
                correlation_id=correlation_id,
                level=logging.ERROR,
                action_type="REPLY_COMMENT",
                comment_id=comment_id,
                error=err_msg,
            )
            return {"success": False, "error": err_msg}

    @classmethod
    async def send_private_reply_dm(
        cls,
        ig_business_id: str,
        comment_id: Optional[str],
        commenter_id: Optional[str],
        message_text: str,
        buttons: Optional[List[Dict[str, Any]]],
        access_token: str,
        correlation_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        version = getattr(settings, "META_GRAPH_API_VERSION", None) or getattr(settings, "META_API_VERSION", "v21.0")
        url = f"https://graph.instagram.com/{version}/me/messages"
        recipient = {"comment_id": comment_id} if comment_id else {"id": commenter_id}

        if buttons:
            url_buttons = []
            quick_replies = []
            for btn in buttons[:3]:
                if btn.get("type") == "postback" or btn.get("payload"):
                    quick_replies.append({
                        "content_type": "text",
                        "title": str(btn.get("title") or "Continue")[:20],
                        "payload": str(btn.get("payload") or "FOLLOW_VERIFIED"),
                    })
                elif btn.get("url"):
                    url_buttons.append({
                        "type": "web_url",
                        "url": btn["url"],
                        "title": str(btn.get("title") or "Open Link")[:20],
                    })

            if url_buttons:
                message_payload: Dict[str, Any] = {
                    "attachment": {
                        "type": "template",
                        "payload": {
                            "template_type": "button",
                            "text": message_text,
                            "buttons": url_buttons,
                        },
                    }
                }
            elif quick_replies:
                message_payload = {
                    "text": message_text,
                    "quick_replies": quick_replies,
                }
            else:
                message_payload = {"text": message_text}
        else:
            message_payload = {"text": message_text}

        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(
                url,
                params={"access_token": access_token},
                json={
                    "recipient": recipient,
                    "message": message_payload,
                },
            )
            body = resp.json() if resp.content else {}
            if resp.status_code in (200, 201) and body.get("message_id"):
                log_event(
                    logger,
                    "ACTION_EXECUTION",
                    status="SUCCESS",
                    correlation_id=correlation_id,
                    action_type="SEND_DM",
                    comment_id=comment_id,
                    message_id=body.get("message_id"),
                )
                return {"success": True, "message_id": body["message_id"]}

            err_msg = body.get("error", {}).get("message") or f"HTTP {resp.status_code}"
            log_event(
                logger,
                "ACTION_EXECUTION",
                status="FAILED",
                correlation_id=correlation_id,
                level=logging.ERROR,
                action_type="SEND_DM",
                comment_id=comment_id,
                error=err_msg,
            )
            return {"success": False, "error": err_msg}

    @classmethod
    async def execute_actions(
        cls,
        actions: List[Dict[str, Any]],
        event_context: Dict[str, Any],
        correlation_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        access_token = event_context.get("access_token")
        ig_business_id = event_context.get("ig_business_id")
        comment_id = event_context.get("comment_id")
        commenter_id = event_context.get("commenter_id")

        dm_sent = False
        comment_replied = False
        errors: List[str] = []

        for act in actions:
            act_type = str(act.get("type") or "").upper()
            text = str(act.get("text") or act.get("message") or "").strip()
            if not text:
                continue

            if act_type in ("REPLY_COMMENT", "COMMENT_REPLY") and comment_id:
                res = await cls.send_comment_reply(
                    comment_id=comment_id,
                    message_text=text,
                    access_token=access_token,
                    correlation_id=correlation_id,
                )
                if res["success"]:
                    comment_replied = True
                else:
                    errors.append(res["error"])

            elif act_type in ("SEND_DM", "PRIVATE_REPLY", "DM"):
                res = await cls.send_private_reply_dm(
                    ig_business_id=ig_business_id,
                    comment_id=comment_id,
                    commenter_id=commenter_id,
                    message_text=text,
                    buttons=act.get("buttons"),
                    access_token=access_token,
                    correlation_id=correlation_id,
                )
                if res["success"]:
                    dm_sent = True
                else:
                    errors.append(res["error"])

        return {
            "success": (dm_sent or comment_replied) and len(errors) == 0,
            "dm_sent": dm_sent,
            "comment_replied": comment_replied,
            "errors": errors,
        }
