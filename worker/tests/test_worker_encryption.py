# worker/tests/test_worker_encryption.py
import pytest
from app.core.encryption import decrypt_token

def test_worker_invalid_ciphertext_raises():
    with pytest.raises(Exception):
        decrypt_token("invalid_token_string")
