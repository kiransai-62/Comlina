# server/app/integrations/instagram/webhooks.py
from typing import Dict, Any, List, Optional
from app.core.security import verify_meta_webhook_signature

class InstagramWebhookParser:
    @staticmethod
    def verify_signature(payload_bytes: bytes, signature_header: Optional[str]) -> bool:
        return verify_meta_webhook_signature(payload_bytes, signature_header)

    @staticmethod
    def extract_events(payload: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Normalizes Meta webhook payload into standardized Comlina event items.
        Extracts provider_event_id for durable deduplication.
        """
        events = []
        entries = payload.get("entry", [])
        for entry in entries:
            business_id = str(entry.get("id", ""))
            # 1. Direct Messages
            for msg in entry.get("messaging", []):
                # Ignore echo messages (sent by the page/account itself) to prevent reply loops
                if msg.get("message", {}).get("is_echo"):
                    continue

                provider_id = msg.get("message", {}).get("mid") or f"msg_{msg.get('timestamp')}_{msg.get('sender', {}).get('id')}"
                events.append({
                    "provider_event_id": provider_id,
                    "event_type": "MESSAGING",
                    "business_ig_id": business_id or msg.get("recipient", {}).get("id"),
                    "sender_id": msg.get("sender", {}).get("id"),
                    "recipient_id": msg.get("recipient", {}).get("id"),
                    "text": msg.get("message", {}).get("text", ""),
                    "timestamp": msg.get("timestamp"),
                    "raw": msg
                })

            # 2. Feed / Comments
            for change in entry.get("changes", []):
                val = change.get("value", {})
                provider_id = val.get("id") or f"chg_{entry.get('time')}_{val.get('item')}"
                events.append({
                    "provider_event_id": provider_id,
                    "event_type": "COMMENT" if change.get("field") == "comments" else change.get("field", "FEED").upper(),
                    "business_ig_id": business_id,
                    "sender_id": val.get("from", {}).get("id"),
                    "sender_username": val.get("from", {}).get("username"),
                    "text": val.get("text", "") or val.get("message", ""),
                    "post_id": val.get("media", {}).get("id"),
                    "comment_id": val.get("id"),
                    "raw": val
                })

        return events
