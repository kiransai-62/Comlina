# server/app/core/encryption.py
import base64
import hashlib
import logging
from typing import List, Any
from cryptography.fernet import Fernet, InvalidToken, MultiFernet

logger = logging.getLogger(__name__)


def _derive_fernet_key(secret_material: str) -> bytes:
    digest = hashlib.sha256(secret_material.encode("utf-8")).digest()
    return base64.urlsafe_b64encode(digest)


def _normalize_key(key: Any) -> bytes:
    key_bytes = key.encode("utf-8") if isinstance(key, str) else key
    try:
        decoded = base64.urlsafe_b64decode(key_bytes)
        if len(decoded) == 32:
            return key_bytes
        return base64.urlsafe_b64encode(decoded.ljust(32, b"0")[:32])
    except Exception:
        return _derive_fernet_key(key if isinstance(key, str) else key.decode("utf-8", "ignore"))


def _get_config():
    try:
        from app.core.config import worker_settings
        return worker_settings
    except (ImportError, AttributeError):
        pass
    try:
        from app.core.config import settings
        return settings
    except Exception:
        return None


def build_fernet_cipher() -> MultiFernet:
    cfg = _get_config()
    keys: List[Fernet] = []

    raw_primary = (
        getattr(cfg, "ENCRYPTION_KEY", None)
        or getattr(cfg, "TOKEN_ENCRYPTION_KEY", None)
        or ""
    ).strip() if cfg else ""

    if raw_primary:
        try:
            keys.append(Fernet(_normalize_key(raw_primary)))
        except Exception:
            keys.append(Fernet(_derive_fernet_key(raw_primary)))
    else:
        # Derive deterministically from JWT_SECRET or META_APP_SECRET so restarts never wipe tokens
        fallback_seed = (
            getattr(cfg, "SUPABASE_JWT_SECRET", None)
            or getattr(cfg, "JWT_SECRET", None)
            or getattr(cfg, "META_APP_SECRET", None)
            or "comlina-deterministic-dev-key-seed"
        ) if cfg else "comlina-deterministic-dev-key-seed"
        keys.append(Fernet(_derive_fernet_key(fallback_seed)))

    raw_old = (
        getattr(cfg, "OLD_ENCRYPTION_KEYS", None)
        or getattr(cfg, "TOKEN_ENCRYPTION_KEYS", None)
        or ""
    ).strip() if cfg else ""

    if raw_old:
        for item in raw_old.split(","):
            cleaned = item.strip()
            if not cleaned:
                continue
            try:
                keys.append(Fernet(_normalize_key(cleaned)))
            except Exception:
                keys.append(Fernet(_derive_fernet_key(cleaned)))

    return MultiFernet(keys)


def _get_multi_fernet() -> MultiFernet:
    return build_fernet_cipher()


def _get_fernet() -> Fernet:
    mf = build_fernet_cipher()
    return mf._fernets[0]


def encrypt_token(plain_token: str) -> str:
    if not plain_token or not plain_token.strip():
        raise ValueError("Cannot encrypt an empty token.")
    cipher = build_fernet_cipher()
    return cipher.encrypt(plain_token.strip().encode("utf-8")).decode("utf-8")


def decrypt_token(encrypted_token: str, allow_fallback: bool = False) -> str:
    if not encrypted_token or not encrypted_token.strip():
        raise ValueError("Cannot decrypt an empty token.")
    cipher = build_fernet_cipher()
    try:
        return cipher.decrypt(encrypted_token.strip().encode("utf-8")).decode("utf-8")
    except InvalidToken as exc:
        if allow_fallback:
            return encrypted_token
        raise ValueError("Stored Instagram access token failed decryption (key mismatch or corrupted token).") from exc


def rotate_token(encrypted_token: str) -> str:
    if not encrypted_token or not encrypted_token.strip():
        raise ValueError("Cannot rotate an empty token.")
    cipher = build_fernet_cipher()
    try:
        return cipher.rotate(encrypted_token.strip().encode("utf-8")).decode("utf-8")
    except InvalidToken as exc:
        raise ValueError("Stored token failed rotation (key mismatch or corrupted token).") from exc
