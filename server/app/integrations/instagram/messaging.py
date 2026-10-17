# server/app/integrations/instagram/messaging.py
from typing import Dict, Any, Optional
from app.integrations.instagram.client import MetaGraphClient

class InstagramMessaging:
    def __init__(self, client: MetaGraphClient):
        self.client = client

    async def send_private_reply(
        self,
        comment_id: Optional[str],
        message_text: str,
        fallback_sender_id: Optional[str] = None,
        buttons: Optional[list] = None
    ) -> Dict[str, Any]:
        """
        Sends a private DM reply in response to an Instagram comment using the 7-day window.
        Uses POST me/messages with recipient={'comment_id': comment_id}.
        Automatically falls back to recipient={'id': fallback_sender_id} if comment_id fails or is missing.
        Supports button templates when buttons are provided (e.g. responseDm.buttons).
        """
        endpoint = "me/messages"

        # Format message payload (template if buttons provided, else plain text)
        msg_obj: Dict[str, Any]
        if buttons:
            meta_buttons = []
            for b in buttons[:3]:  # Meta allows max 3 buttons per button template
                label = b.get("label") or b.get("title") or "Open Link"
                url = b.get("url")
                if url:
                    meta_buttons.append({
                        "type": "web_url",
                        "url": url,
                        "title": label[:20]
                    })
                elif b.get("payload"):
                    meta_buttons.append({
                        "type": "postback",
                        "title": label[:20],
                        "payload": b.get("payload")
                    })
            if meta_buttons:
                msg_obj = {
                    "attachment": {
                        "type": "template",
                        "payload": {
                            "template_type": "button",
                            "text": message_text,
                            "buttons": meta_buttons
                        }
                    }
                }
            else:
                msg_obj = {"text": message_text}
        else:
            msg_obj = {"text": message_text}

        if comment_id:
            try:
                payload = {
                    "recipient": {"comment_id": comment_id},
                    "message": msg_obj
                }
                return await self.client.post(endpoint, json_data=payload)
            except Exception as e:
                if not fallback_sender_id:
                    raise
                import logging
                logging.getLogger("messaging").warning(
                    f"Failed to send private reply by comment_id={comment_id}, falling back to recipient_id={fallback_sender_id}: {e}"
                )

        if fallback_sender_id:
            return await self.send_direct_message(
                ig_recipient_id=fallback_sender_id,
                message_text=message_text,
                buttons=buttons
            )

        raise ValueError("Neither comment_id nor fallback_sender_id provided for private reply.")

    async def send_direct_message(
        self,
        ig_recipient_id: str,
        message_text: str,
        quick_replies: Optional[list] = None,
        buttons: Optional[list] = None
    ) -> Dict[str, Any]:
        """
        Sends a standard Instagram Direct Message using standard 24h messaging window.
        Supports button templates when buttons are provided.
        """
        endpoint = "me/messages"
        msg_obj: Dict[str, Any]

        if buttons:
            meta_buttons = []
            for b in buttons[:3]:
                label = b.get("label") or b.get("title") or "Open Link"
                url = b.get("url")
                if url:
                    meta_buttons.append({
                        "type": "web_url",
                        "url": url,
                        "title": label[:20]
                    })
                elif b.get("payload"):
                    meta_buttons.append({
                        "type": "postback",
                        "title": label[:20],
                        "payload": b.get("payload")
                    })
            if meta_buttons:
                msg_obj = {
                    "attachment": {
                        "type": "template",
                        "payload": {
                            "template_type": "button",
                            "text": message_text,
                            "buttons": meta_buttons
                        }
                    }
                }
            else:
                msg_obj = {"text": message_text}
        else:
            msg_obj = {"text": message_text}

        if quick_replies:
            msg_obj["quick_replies"] = quick_replies

        payload = {
            "recipient": {"id": ig_recipient_id},
            "message": msg_obj
        }
        return await self.client.post(endpoint, json_data=payload)
