# worker/app/core/encryption.py
import base64
import hashlib
from typing import List
from cryptography.fernet import Fernet, MultiFernet, InvalidToken
from app.core.config import worker_settings


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
    keys = worker_settings.get_encryption_keys()
    if not keys:
        if worker_settings.TOKEN_ENCRYPTION_KEY:
            keys = [worker_settings.TOKEN_ENCRYPTION_KEY]
        else:
            raise ValueError("TOKEN_ENCRYPTION_KEY is not configured")
    fernets = [Fernet(_normalize_key(k)) for k in keys]
    return MultiFernet(fernets)


def _get_fernet() -> Fernet:
    keys = worker_settings.get_encryption_keys()
    key = keys[0] if keys else worker_settings.TOKEN_ENCRYPTION_KEY
    if not key:
        raise ValueError("TOKEN_ENCRYPTION_KEY is not configured")
    return Fernet(_normalize_key(key))


def decrypt_token(ciphertext: str, allow_fallback: bool = False) -> str:
    """
    Decrypts a MultiFernet ciphertext back to plaintext.
    Supports key rotation: tries all configured keys in order.
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


def encrypt_token(plaintext: str) -> str:
    """
    Encrypts a plaintext token using MultiFernet authenticated symmetric encryption.
    Always encrypts with the primary (first) key.
    """
    if not plaintext:
        return ""
    return _get_multi_fernet().encrypt(plaintext.encode("utf-8")).decode("utf-8")


def rotate_token(ciphertext: str) -> str:
    """
    Re-encrypts a ciphertext with the primary encryption key using MultiFernet.rotate.
    """
    if not ciphertext:
        return ""
    return _get_multi_fernet().rotate(ciphertext.encode("utf-8")).decode("utf-8")
