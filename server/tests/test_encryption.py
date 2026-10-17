import unittest
from app.core.encryption import encrypt_token, decrypt_token

class TestEncryption(unittest.TestCase):
    def test_token_encryption_roundtrip(self):
        test_tokens = [
            "EAABsbCS1iHgBAO...",
            "mock_long_lived_token_2026",
            "short_key_12345",
            "special_chars_!@#$%^&*()_+{}[]:;<>,.?",
        ]
        for token in test_tokens:
            encrypted = encrypt_token(token)
            self.assertNotEqual(encrypted, token)
            self.assertIsInstance(encrypted, str)
            decrypted = decrypt_token(encrypted)
            self.assertEqual(decrypted, token)

    def test_legacy_unencrypted_token_fallback(self):
        # Legacy tokens that aren't encrypted should be gracefully returned when allow_fallback=True
        legacy = "raw_unencrypted_token_abc123"
        self.assertEqual(decrypt_token(legacy, allow_fallback=True), legacy)

if __name__ == "__main__":
    unittest.main()
