# server/app/core/security.py
import hmac
import hashlib
import json
import base64
import logging
import urllib.request
import urllib.error
from typing import Optional, Dict, Any
import jwt
from fastapi import HTTPException, Security, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.core.config import settings

logger = logging.getLogger(__name__)

security_bearer = HTTPBearer(auto_error=False)

def verify_meta_webhook_signature(payload_bytes: bytes, signature_header: Optional[str]) -> bool:
    """
    Verifies Meta's X-Hub-Signature-256 header using SHA-256 HMAC against META_APP_SECRET.
    Signature header format: 'sha256=<hex_digest>'
    """
    if not settings.META_APP_SECRET or not signature_header or not signature_header.startswith("sha256="):
        return False
    
    try:
        expected_hash = signature_header.split("sha256=")[1]
        computed_hash = hmac.new(
            key=settings.META_APP_SECRET.encode("utf-8"),
            msg=payload_bytes,
            digestmod=hashlib.sha256
        ).hexdigest()
        return hmac.compare_digest(expected_hash, computed_hash)
    except Exception:
        return False

def _verify_with_supabase_cloud(token: str) -> Optional[Dict[str, Any]]:
    """
    Validates the access token directly against Supabase Auth /auth/v1/user endpoint.
    Serves as authoritative fallback when local HMAC secret differs or is rotated.
    """
    supabase_url = settings.SUPABASE_URL
    anon_key = settings.SUPABASE_ANON_KEY
    if not supabase_url or not anon_key or "placeholder" in supabase_url:
        return None

    user_endpoint = f"{supabase_url.rstrip('/')}/auth/v1/user"
    req = urllib.request.Request(user_endpoint)
    req.add_header("apikey", anon_key)
    req.add_header("Authorization", f"Bearer {token}")

    try:
        with urllib.request.urlopen(req, timeout=5) as response:
            if response.status == 200:
                user_record = json.loads(response.read().decode("utf-8"))
                logger.info(f"[AUTH] Successfully verified token with Supabase Cloud: user={user_record.get('email')}")
                return {
                    "sub": user_record.get("id"),
                    "email": user_record.get("email"),
                    "user_metadata": user_record.get("user_metadata", {}),
                    "role": user_record.get("role", "authenticated"),
                    "aud": user_record.get("aud", "authenticated"),
                }
    except Exception as e:
        logger.warning(f"[AUTH] Supabase Cloud verification check failed: {e}")
        return None

    return None

_jwks_client: Optional[jwt.PyJWKClient] = None

def get_jwks_client() -> Optional[jwt.PyJWKClient]:
    global _jwks_client
    if _jwks_client is None and settings.SUPABASE_JWKS_URL:
        try:
            _jwks_client = jwt.PyJWKClient(settings.SUPABASE_JWKS_URL, cache_keys=True)
        except Exception as e:
            logger.warning(f"[AUTH] Failed to initialize JWKS client: {e}")
    return _jwks_client


GENERIC_UNAUTHORIZED_EXCEPTION = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"},
)

ALLOWED_JWT_ALGORITHMS = ["HS256", "RS256", "ES256"]


def decode_supabase_jwt(token: str) -> Dict[str, Any]:
    """
    Decodes and verifies an access token JWT with hardened security checks:
    - Algorithm explicitly allowed (never 'none')
    - Signature cryptographically verified
    - exp required and verified
    - aud ('authenticated') required and verified
    - iss required and verified (<SUPABASE_URL>/auth/v1 or comlina-backend)
    - sub required, non-empty, and verified
    - Generic 401 response on any failure
    """
    if not token or not isinstance(token, str):
        raise GENERIC_UNAUTHORIZED_EXCEPTION

    # Basic structural check (header.payload.signature)
    parts = token.split(".")
    if len(parts) != 3:
        raise GENERIC_UNAUTHORIZED_EXCEPTION

    # Inspect header without signature to verify algorithm
    try:
        header = jwt.get_unverified_header(token)
    except Exception:
        raise GENERIC_UNAUTHORIZED_EXCEPTION

    alg = header.get("alg")
    if not alg or alg.lower() == "none" or alg not in ALLOWED_JWT_ALGORITHMS:
        logger.warning("[AUTH] Rejecting JWT with disallowed algorithm: %s", alg)
        raise GENERIC_UNAUTHORIZED_EXCEPTION

    supabase_iss = f"{settings.SUPABASE_URL.rstrip('/')}/auth/v1"
    allowed_issuers = {supabase_iss, "comlina-backend", "supabase"}

    payload: Optional[Dict[str, Any]] = None

    # Strategy 1: Asymmetric JWKS verification (RS256, ES256)
    if alg in ("RS256", "ES256"):
        jwks = get_jwks_client()
        if not jwks:
            logger.warning("[AUTH] Received asymmetric token %s but SUPABASE_JWKS_URL is not configured", alg)
            raise GENERIC_UNAUTHORIZED_EXCEPTION
        try:
            signing_key = jwks.get_signing_key_from_jwt(token)
            payload = jwt.decode(
                token,
                signing_key.key,
                algorithms=[alg],
                audience="authenticated",
                options={
                    "require": ["exp", "sub", "aud", "iss"],
                    "verify_exp": True,
                    "verify_aud": True,
                    "verify_iss": False,
                },
            )
        except Exception as e:
            logger.warning("[AUTH] JWKS JWT validation failed: %s", type(e).__name__)
            raise GENERIC_UNAUTHORIZED_EXCEPTION

    # Strategy 2: Symmetric HMAC verification (HS256)
    elif alg == "HS256":
        candidate_keys = []
        for secret in [settings.BACKEND_JWT_SECRET, settings.SUPABASE_JWT_SECRET]:
            if secret and secret not in candidate_keys:
                candidate_keys.append(secret)
                try:
                    decoded = base64.b64decode(secret)
                    if len(decoded) >= 32 and decoded not in candidate_keys:
                        candidate_keys.append(decoded)
                except Exception:
                    pass

        last_err = None
        for key in candidate_keys:
            try:
                payload = jwt.decode(
                    token,
                    key,
                    algorithms=["HS256"],
                    audience="authenticated",
                    options={
                        "require": ["exp", "sub", "aud", "iss"],
                        "verify_exp": True,
                        "verify_aud": True,
                        "verify_iss": False,
                    },
                )
                break
            except Exception as e:
                last_err = e

        if payload is None:
            # Fallback to Supabase Auth Cloud validation
            cloud_verified = _verify_with_supabase_cloud(token)
            if cloud_verified:
                payload = cloud_verified
            else:
                logger.warning("[AUTH] HMAC JWT validation failed: %s", type(last_err).__name__ if last_err else "no_key")
                raise GENERIC_UNAUTHORIZED_EXCEPTION

    if not payload:
        raise GENERIC_UNAUTHORIZED_EXCEPTION

    # Required claims validation
    sub = payload.get("sub")
    if not sub or not str(sub).strip():
        logger.warning("[AUTH] Rejecting JWT: missing or empty sub")
        raise GENERIC_UNAUTHORIZED_EXCEPTION

    iss = payload.get("iss")
    if not iss or iss not in allowed_issuers:
        logger.warning("[AUTH] Rejecting JWT: invalid iss '%s'", iss)
        raise GENERIC_UNAUTHORIZED_EXCEPTION

    if payload.get("token_type") == "refresh":
        logger.warning("[AUTH] Rejecting refresh token used as access token")
        raise GENERIC_UNAUTHORIZED_EXCEPTION

    return payload
