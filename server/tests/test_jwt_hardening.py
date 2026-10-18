import time
import uuid
import jwt
import pytest
from fastapi import HTTPException
from app.core.config import settings
from app.core.security import decode_supabase_jwt

def create_raw_token(payload: dict, key: str = "", alg: str = "HS256", headers: dict = None) -> str:
    signing_key = key or settings.BACKEND_JWT_SECRET or settings.SUPABASE_JWT_SECRET
    if alg == "none":
        return jwt.encode(payload, key="", algorithm="none", headers=headers)
    return jwt.encode(payload, signing_key, algorithm=alg, headers=headers)

def get_valid_payload():
    now = int(time.time())
    supabase_iss = f"{settings.SUPABASE_URL.rstrip('/')}/auth/v1"
    return {
        "sub": str(uuid.uuid4()),
        "email": "security_test@comlina.ai",
        "iss": supabase_iss,
        "aud": "authenticated",
        "iat": now,
        "exp": now + 3600,
        "role": "authenticated",
    }

def test_valid_token_decodes_successfully():
    payload = get_valid_payload()
    token = create_raw_token(payload)
    decoded = decode_supabase_jwt(token)
    assert decoded["sub"] == payload["sub"]
    assert decoded["aud"] == "authenticated"

def test_reject_alg_none():
    payload = get_valid_payload()
    token = create_raw_token(payload, alg="none")
    with pytest.raises(HTTPException) as exc_info:
        decode_supabase_jwt(token)
    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Could not validate credentials"

def test_reject_expired_token():
    payload = get_valid_payload()
    payload["exp"] = int(time.time()) - 60  # expired 1 minute ago
    token = create_raw_token(payload)
    with pytest.raises(HTTPException) as exc_info:
        decode_supabase_jwt(token)
    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Could not validate credentials"

def test_reject_wrong_audience():
    payload = get_valid_payload()
    payload["aud"] = "unauthenticated"
    token = create_raw_token(payload)
    with pytest.raises(HTTPException) as exc_info:
        decode_supabase_jwt(token)
    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Could not validate credentials"

def test_reject_wrong_issuer():
    payload = get_valid_payload()
    payload["iss"] = "https://rogue-supabase.attacker.com/auth/v1"
    token = create_raw_token(payload)
    with pytest.raises(HTTPException) as exc_info:
        decode_supabase_jwt(token)
    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Could not validate credentials"

def test_reject_wrong_signature():
    payload = get_valid_payload()
    token = create_raw_token(payload, key="x" * 32)
    with pytest.raises(HTTPException) as exc_info:
        decode_supabase_jwt(token)
    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Could not validate credentials"

def test_reject_malformed_token():
    for malformed in ["", "not.a.jwt", "only.two.parts", "a.b.c.d", "dev-bypass-token", None]:
        with pytest.raises(HTTPException) as exc_info:
            decode_supabase_jwt(malformed)
        assert exc_info.value.status_code == 401
        assert exc_info.value.detail == "Could not validate credentials"

def test_reject_missing_sub():
    payload = get_valid_payload()
    del payload["sub"]
    token = create_raw_token(payload)
    with pytest.raises(HTTPException) as exc_info:
        decode_supabase_jwt(token)
    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Could not validate credentials"

def test_reject_missing_exp():
    payload = get_valid_payload()
    del payload["exp"]
    token = create_raw_token(payload)
    with pytest.raises(HTTPException) as exc_info:
        decode_supabase_jwt(token)
    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Could not validate credentials"

def test_reject_refresh_token_as_access_token():
    payload = get_valid_payload()
    payload["token_type"] = "refresh"
    token = create_raw_token(payload)
    with pytest.raises(HTTPException) as exc_info:
        decode_supabase_jwt(token)
    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Could not validate credentials"
