# worker/tests/test_worker_encryption.py
import pytest
from cryptography.fernet import Fernet, InvalidToken
from app.core.config import worker_settings
from app.core.encryption import (
    encrypt_token,
    decrypt_token,
    rotate_token,
    _normalize_key,
)


def _generate_valid_fernet_key() -> str:
    return Fernet.generate_key().decode("utf-8")


def test_worker_invalid_ciphertext_raises():
    with pytest.raises(Exception):
        decrypt_token("invalid_token_string")


def test_worker_multi_fernet_rotation_parity(monkeypatch):
    primary_key = _generate_valid_fernet_key()
    secondary_key = _generate_valid_fernet_key()

    monkeypatch.setattr(worker_settings, "TOKEN_ENCRYPTION_KEY", primary_key)
    monkeypatch.setattr(worker_settings, "TOKEN_ENCRYPTION_KEYS", secondary_key)

    token = "worker_token_shared_rotation_key"

    # Encrypt under secondary key
    sec_fernet = Fernet(_normalize_key(secondary_key))
    old_ciphertext = sec_fernet.encrypt(token.encode("utf-8")).decode("utf-8")

    # Worker decrypts successfully
    assert decrypt_token(old_ciphertext) == token

    # Worker rotates successfully to primary key
    new_ciphertext = rotate_token(old_ciphertext)
    assert new_ciphertext != old_ciphertext

    # Primary key alone can decrypt the rotated token
    prim_fernet = Fernet(_normalize_key(primary_key))
    assert prim_fernet.decrypt(new_ciphertext.encode("utf-8")).decode("utf-8") == token
