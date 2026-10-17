import unittest
from fastapi import HTTPException
from app.core.security import decode_supabase_jwt

class TestSecurity(unittest.TestCase):
    def test_dev_mock_token_rejected(self):
        with self.assertRaises(HTTPException) as ctx:
            decode_supabase_jwt("dev_mock_token")
        self.assertEqual(ctx.exception.status_code, 401)

    def test_empty_token_rejected(self):
        with self.assertRaises(HTTPException) as ctx:
            decode_supabase_jwt("")
        self.assertEqual(ctx.exception.status_code, 401)

    def test_garbage_token_rejected(self):
        with self.assertRaises(HTTPException) as ctx:
            decode_supabase_jwt("not.a.valid.jwt.token")
        self.assertEqual(ctx.exception.status_code, 401)

    def test_dev_bypass_token_rejected_unconditionally(self):
        with self.assertRaises(HTTPException) as ctx:
            decode_supabase_jwt("dev-bypass-token")
        self.assertEqual(ctx.exception.status_code, 401)

    def test_webhook_empty_secret_rejected(self):
        from app.core.security import verify_meta_webhook_signature
        from app.core.config import settings
        orig = settings.META_APP_SECRET
        settings.META_APP_SECRET = ""
        try:
            # When secret is empty, must return False unconditionally
            self.assertFalse(verify_meta_webhook_signature(b'test', "sha256=abcdef"))
        finally:
            settings.META_APP_SECRET = orig

if __name__ == "__main__":
    unittest.main()
