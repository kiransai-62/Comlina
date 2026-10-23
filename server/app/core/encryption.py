# server/app/core/encryption.py
import base64
import hashlib
from typing import List
from cryptography.fernet import Fernet, MultiFernet, InvalidToken
from app.core.config import settings


def _normalize_key(key: str) -> bytes:
    key_bytes = key.encode("utf-8") if isinstance(key, str) else key
    try:
        decoded = base64.urlsafe_b64decode(key_bytes)
        if len(decoded) != 32:
            key_bytes = base64.urlsafe_b64encode(decoded.ljust(32, b"0")[:32])
    except Exception:
        key_bytes = base64.urlsafe_b64encode(hashlib.sha256(key_bytes).digest())
    return key_bytes


def _get_multi_fernet() -> MultiFernet:
    keys = settings.get_encryption_keys()
    if not keys:
        if settings.TOKEN_ENCRYPTION_KEY:
            keys = [settings.TOKEN_ENCRYPTION_KEY]
        else:
            raise ValueError("TOKEN_ENCRYPTION_KEY environment variable is not configured")
    fernets = [Fernet(_normalize_key(k)) for k in keys]
    return MultiFernet(fernets)


def _get_fernet() -> Fernet:
    """Backwards compatibility helper returning Fernet for primary key."""
    keys = settings.get_encryption_keys()
    key = keys[0] if keys else settings.TOKEN_ENCRYPTION_KEY
    if not key:
        raise ValueError("TOKEN_ENCRYPTION_KEY environment variable is not configured")
    return Fernet(_normalize_key(key))


def encrypt_token(plaintext: str) -> str:
    """
    Encrypts a plaintext token using MultiFernet authenticated symmetric encryption.
    Always encrypts with the primary (first) key.
    Returns URL-safe base64 encoded ciphertext string.
    """
    if not plaintext:
        return ""
    mf = _get_multi_fernet()
    encrypted_bytes = mf.encrypt(plaintext.encode("utf-8"))
    return encrypted_bytes.decode("utf-8")


def decrypt_token(ciphertext: str, allow_fallback: bool = False) -> str:
    """
    Decrypts a MultiFernet ciphertext back to plaintext.
    Supports key rotation: tries all configured keys in order (primary first, then fallback keys).
    If ciphertext cannot be decrypted and allow_fallback is True, returns original string.
    Otherwise raises InvalidToken.
    """
    if not ciphertext:
        return ""
    mf = _get_multi_fernet()
    try:
        decrypted_bytes = mf.decrypt(ciphertext.encode("utf-8"))
        return decrypted_bytes.decode("utf-8")
    except (InvalidToken, Exception):
        if allow_fallback:
            return ciphertext
        raise


def rotate_token(ciphertext: str) -> str:
    """
    Re-encrypts a ciphertext with the primary encryption key using MultiFernet.rotate.
    If the ciphertext was encrypted under a secondary/fallback key, re-encrypts it under the primary key.
    If already encrypted under the primary key, refreshes the timestamp/IV.
    """
    if not ciphertext:
        return ""
    mf = _get_multi_fernet()
    rotated_bytes = mf.rotate(ciphertext.encode("utf-8"))
    return rotated_bytes.decode("utf-8")
