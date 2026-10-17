import unittest
import hmac
import hashlib
from app.core.config import settings
from app.integrations.instagram.webhooks import InstagramWebhookParser

class TestWebhooks(unittest.TestCase):
    def test_webhook_signature_valid(self):
        payload = b'{"object": "instagram", "entry": []}'
        secret = settings.META_APP_SECRET
        valid_sig = "sha256=" + hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
        self.assertTrue(InstagramWebhookParser.verify_signature(payload, valid_sig))

    def test_webhook_signature_invalid(self):
        payload = b'{"object": "instagram", "entry": []}'
        invalid_sig = "sha256=invalidhash00000000000000000000000000000000000000000000000000000000"
        self.assertFalse(InstagramWebhookParser.verify_signature(payload, invalid_sig))

    def test_webhook_extract_comment_event(self):
        payload = {
            "entry": [
                {
                    "id": "ig_biz_12345",
                    "changes": [
                        {
                            "field": "comments",
                            "value": {
                                "id": "comment_999",
                                "from": {"id": "user_777", "username": "jane_doe"},
                                "text": "Send me the link please!"
                            }
                        }
                    ]
                }
            ]
        }
        events = InstagramWebhookParser.extract_events(payload)
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["event_type"], "COMMENT")
        self.assertEqual(events[0]["business_ig_id"], "ig_biz_12345")
        self.assertEqual(events[0]["sender_username"], "jane_doe")
        self.assertEqual(events[0]["text"], "Send me the link please!")

    def test_signed_request_validation(self):
        import json
        import base64
        from app.api.webhooks import parse_signed_request
        secret = settings.META_APP_SECRET
        payload = {"algorithm": "HMAC-SHA256", "user_id": "test_user_12345"}
        payload_b64 = base64.urlsafe_b64encode(json.dumps(payload).encode()).decode().rstrip("=")
        sig = hmac.new(secret.encode(), payload_b64.encode(), hashlib.sha256).digest()
        sig_b64 = base64.urlsafe_b64encode(sig).decode().rstrip("=")
        signed_request = f"{sig_b64}.{payload_b64}"

        parsed = parse_signed_request(signed_request, secret)
        self.assertEqual(parsed["user_id"], "test_user_12345")

    def test_signed_request_tampered_rejected(self):
        import json
        import base64
        from fastapi import HTTPException
        from app.api.webhooks import parse_signed_request
        secret = settings.META_APP_SECRET
        payload = {"algorithm": "HMAC-SHA256", "user_id": "test_user_12345"}
        payload_b64 = base64.urlsafe_b64encode(json.dumps(payload).encode()).decode().rstrip("=")
        fake_sig_b64 = base64.urlsafe_b64encode(b"0" * 32).decode().rstrip("=")
        signed_request = f"{fake_sig_b64}.{payload_b64}"

        with self.assertRaises(HTTPException) as ctx:
            parse_signed_request(signed_request, secret)
        self.assertEqual(ctx.exception.status_code, 400)


if __name__ == "__main__":
    unittest.main()
