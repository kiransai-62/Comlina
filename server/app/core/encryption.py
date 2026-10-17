# server/app/core/encryption.py
import base64
from cryptography.fernet import Fernet, InvalidToken
from app.core.config import settings

def _get_fernet() -> Fernet:
    key = settings.TOKEN_ENCRYPTION_KEY
    if not key:
        raise ValueError("TOKEN_ENCRYPTION_KEY environment variable is not configured")
    # Ensure key is bytes
    key_bytes = key.encode("utf-8") if isinstance(key, str) else key
    # If key is 32 raw bytes (not base64), base64 encode it
    try:
        # Check if valid base64 32-byte key
        decoded = base64.urlsafe_b64decode(key_bytes)
        if len(decoded) != 32:
            # Re-pad or hash to 32 bytes
            key_bytes = base64.urlsafe_b64encode(decoded.ljust(32, b"0")[:32])
    except Exception:
        # If not valid base64, derive 32 bytes from key_bytes
        import hashlib
        key_bytes = base64.urlsafe_b64encode(hashlib.sha256(key_bytes).digest())
    
    return Fernet(key_bytes)

def encrypt_token(plaintext: str) -> str:
    """
    Encrypts a plaintext token using Fernet authenticated symmetric encryption.
    Returns URL-safe base64 encoded ciphertext string.
    """
    if not plaintext:
        return ""
    f = _get_fernet()
    encrypted_bytes = f.encrypt(plaintext.encode("utf-8"))
    return encrypted_bytes.decode("utf-8")

def decrypt_token(ciphertext: str, allow_fallback: bool = False) -> str:
    """
    Decrypts a Fernet ciphertext back to plaintext.
    If ciphertext cannot be decrypted and allow_fallback is True, returns original string.
    Otherwise raises InvalidToken.
    """
    if not ciphertext:
        return ""
    f = _get_fernet()
    try:
        decrypted_bytes = f.decrypt(ciphertext.encode("utf-8"))
        return decrypted_bytes.decode("utf-8")
    except (InvalidToken, Exception):
        if allow_fallback:
            return ciphertext
        raise
