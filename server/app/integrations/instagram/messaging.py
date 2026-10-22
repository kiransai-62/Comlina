# server/app/integrations/instagram/messaging.py
from typing import Dict, Any, Optional
from app.integrations.instagram.client import MetaGraphClient

class InstagramMessaging:
    def __init__(self, client: MetaGraphClient):
        self.client = client

    @staticmethod
    def _format_private_reply_text(message_text: str, buttons: Optional[list] = None) -> str:
        """
        Meta Graph API restricts comment_id private replies to plain text messages.
        If CTA buttons/links are configured, convert them into readable text with URLs
        so Instagram natively generates link previews without sending unsupported button templates.
        """
        if not buttons:
            return message_text

        link_lines = []
        for b in buttons:
            label = (b.get("label") or b.get("title") or "").strip()
            url = (b.get("url") or "").strip()
            if url:
                if label:
                    link_lines.append(f"{label}: {url}")
                else:
                    link_lines.append(url)
            elif b.get("payload"):
                if label:
                    link_lines.append(f"[{label}]")

        if link_lines:
            return f"{message_text}\n\n" + "\n".join(link_lines)
        return message_text

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

        Meta Graph API strictly requires recipient={'comment_id': ...} messages to be plain text.
        Configured CTA links are formatted into the text body to leverage Instagram's native link previews.
        Unsupported attachment templates are never sent to comment_id.

        Does NOT automatically fall back to direct messaging using fallback_sender_id when comment_id
        fails, because direct messaging outside the 24-hour conversational window violates Meta messaging policy
        and masks the root error.
        If comment_id is omitted but fallback_sender_id is provided, delegates to send_direct_message.
        """
        endpoint = "me/messages"

        if comment_id:
            formatted_text = self._format_private_reply_text(message_text, buttons)
            payload = {
                "recipient": {"comment_id": comment_id},
                "message": {"text": formatted_text}
            }
            return await self.client.post(endpoint, json_data=payload)

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
