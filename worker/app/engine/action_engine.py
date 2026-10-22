# worker/app/engine/action_engine.py
import asyncio
import logging
from typing import Dict, Any, Optional
from sqlalchemy import select
from app.integrations.instagram import InstagramComments, InstagramMessaging
from app.integrations.instagram.client import MetaGraphClient

logger = logging.getLogger("action_engine")

class ActionEngine:
    """
    Executes automation actions:
    - PRIVATE_DM (Private reply to comment or Direct Message)
    - PUBLIC_REPLY (Direct comment thread reply)
    - TAG_CONTACT (Database contact tag update)
    - DELAY (Smart asynchronous wait)
    """
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

        if action_type == "PUBLIC_REPLY":
            text = action_config.get("text", "Thanks @{username}! Sent the details to your DMs 📩")
            formatted_text = text.replace("{username}", username)
            logger.info(f"Executing PUBLIC_REPLY for comment {comment_id} (text_len={len(formatted_text)})")
            
            res = {"status": "SUCCESS", "action": "PUBLIC_REPLY", "text": formatted_text}
            if instagram_client and comment_id:
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
            formatted_text = text.replace("{first_name}", username).replace("{username}", username)
            logger.info(
                f"Executing PRIVATE_DM for comment {comment_id} / recipient {recipient_id} "
                f"(text_len={len(formatted_text)}, buttons_count={len(buttons)})"
            )

            res = {"status": "SUCCESS", "action": "PRIVATE_DM", "text": formatted_text, "buttons": buttons}
            if instagram_client:
                try:
                    messaging_client = InstagramMessaging(instagram_client)
                    api_res = await messaging_client.send_private_reply(
                        comment_id=comment_id,
                        message_text=formatted_text,
                        fallback_sender_id=recipient_id,
                        buttons=buttons
                    )
                    res["meta_response"] = api_res
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
            res = {"status": "SUCCESS", "action": "TAG_CONTACT", "tag": tag}

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
