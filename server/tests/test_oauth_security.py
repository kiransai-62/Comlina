# server/tests/test_oauth_security.py
"""
Unit and integration tests for Work Item 9:
- OAuth redirect allowlist enforcement (canonical domains, scheme validation, credentials injection, wildcard blocking in production)
- OAuth state cryptographic signing, multi-key rotation, TTL window, and single-use replay prevention
- Meta signed_request HMAC-SHA256 verification, TTL window (issued_at), and distributed replay cache
"""

import time
import json
import base64
import hmac
import hashlib
import uuid
import pytest
from fastapi import HTTPException
from app.core.config import settings
from app.core.replay_cache import replay_cache
from app.api.instagram import (
    _is_allowed_redirect_uri,
    generate_oauth_state,
    verify_oauth_state,
)
from app.api.webhooks import (
    parse_signed_request,
    verify_and_parse_signed_request,
)


class MockRedisClient:
    """Mock Redis client implementing atomic set with nx and ex."""
    def __init__(self):
        self.store = {}

    async def set(self, key, value, ex=None, nx=False):
        if nx and key in self.store:
            return None  # Redis returns None when NX condition is not met
        self.store[key] = value
        return True

    async def ping(self):
        return True


def _make_signed_request(payload: dict, secret: str) -> str:
    payload_b64 = base64.urlsafe_b64encode(json.dumps(payload).encode("utf-8")).decode("utf-8").rstrip("=")
    sig = hmac.new(secret.encode("utf-8"), payload_b64.encode("utf-8"), hashlib.sha256).digest()
    sig_b64 = base64.urlsafe_b64encode(sig).decode("utf-8").rstrip("=")
    return f"{sig_b64}.{payload_b64}"


class TestOAuthRedirectAllowlist:
    def setup_method(self):
        replay_cache.reset()

    def test_allowed_canonical_domains(self):
        """Canonical Comlina domains must be permitted."""
        assert _is_allowed_redirect_uri(None) is True
        assert _is_allowed_redirect_uri("https://app.comlina.ai/auth/callback") is True
        assert _is_allowed_redirect_uri("https://comlina.ai/oauth/callback") is True
        assert _is_allowed_redirect_uri("https://www.comlina.ai/connect/instagram") is True
        assert _is_allowed_redirect_uri("https://app.comlina.com/connect/instagram") is True
        assert _is_allowed_redirect_uri("https://comlina.com/api/callback") is True

    def test_malicious_domains_rejected(self):
        """External or untrusted domains must always be rejected."""
        assert _is_allowed_redirect_uri("https://evil.com/callback") is False
        assert _is_allowed_redirect_uri("https://attacker.com/steal-token") is False
        assert _is_allowed_redirect_uri("https://phishing-comlina.com") is False
        assert _is_allowed_redirect_uri("http://evil-localhost:3000") is False

    def test_scheme_validation(self):
        """Non-http/https schemes must be rejected."""
        assert _is_allowed_redirect_uri("javascript:alert(1)") is False
        assert _is_allowed_redirect_uri("data:text/html,<script>alert(1)</script>") is False
        assert _is_allowed_redirect_uri("file:///etc/passwd") is False
        assert _is_allowed_redirect_uri("//app.comlina.ai/callback") is False

    def test_credential_userinfo_injection_rejected(self):
        """URLs containing credentials or authority injection must be rejected."""
        assert _is_allowed_redirect_uri("https://user:pass@app.comlina.ai/callback") is False
        assert _is_allowed_redirect_uri("https://app.comlina.ai@attacker.com/callback") is False

    def test_production_environment_blocks_wildcards_and_plaintext(self, monkeypatch):
        """In production, wildcard subdomains and plaintext http must be strictly rejected."""
        monkeypatch.setattr(settings, "ENVIRONMENT", "production")

        # Wildcards forbidden in production
        assert _is_allowed_redirect_uri("https://attacker.vercel.app/connect") is False
        assert _is_allowed_redirect_uri("https://evil.onrender.com/connect") is False

        # Plaintext HTTP forbidden in production even for localhost
        assert _is_allowed_redirect_uri("http://localhost:3000/connect") is False
        assert _is_allowed_redirect_uri("http://127.0.0.1:3000/connect") is False

        # HTTPS canonical domains remain valid
        assert _is_allowed_redirect_uri("https://app.comlina.ai/connect/instagram") is True
        assert _is_allowed_redirect_uri("https://comlina.com/connect/instagram") is True

    def test_development_environment_allows_localhost_and_staging(self, monkeypatch):
        """In development/test, localhost and preview deployments are permitted."""
        monkeypatch.setattr(settings, "ENVIRONMENT", "development")

        assert _is_allowed_redirect_uri("http://localhost:3000/connect/instagram") is True
        assert _is_allowed_redirect_uri("http://127.0.0.1:3000/oauth/callback") is True
        assert _is_allowed_redirect_uri("https://my-preview.vercel.app/connect") is True
        assert _is_allowed_redirect_uri("https://staging.onrender.com/connect") is True


class TestOAuthStateSigningAndTTL:
    def setup_method(self):
        replay_cache.reset()

    def test_state_generation_and_verification(self):
        ws_id = uuid.uuid4()
        user_id = uuid.uuid4()
        state = generate_oauth_state(ws_id, user_id)

        assert verify_oauth_state(state, ws_id, user_id) is True

    def test_state_mismatched_workspace_or_user(self):
        ws_id = uuid.uuid4()
        user_id = uuid.uuid4()
        state = generate_oauth_state(ws_id, user_id)

        assert verify_oauth_state(state, uuid.uuid4(), user_id) is False
        assert verify_oauth_state(state, ws_id, uuid.uuid4()) is False

    def test_state_tampered_signature(self):
        ws_id = uuid.uuid4()
        user_id = uuid.uuid4()
        state = generate_oauth_state(ws_id, user_id)

        parts = state.split(":")
        parts[-1] = "bad_signature"
        tampered = ":".join(parts)

        assert verify_oauth_state(tampered, ws_id, user_id) is False

    def test_state_ttl_expired(self):
        ws_id = uuid.uuid4()
        user_id = uuid.uuid4()
        old_time = int(time.time()) - 1000  # Older than 900s
        nonce = "0123456789abcdef"
        state_payload = f"{ws_id}:{user_id}:{old_time}:{nonce}"
        key = settings.get_primary_encryption_key() or settings.TOKEN_ENCRYPTION_KEY or "fallback_key"
        sig = hmac.new(key.encode("utf-8"), state_payload.encode("utf-8"), hashlib.sha256).hexdigest()[:16]
        expired_state = f"{state_payload}:{sig}"

        assert verify_oauth_state(expired_state, ws_id, user_id, max_age_seconds=900) is False

    def test_state_future_timestamp_rejected(self):
        ws_id = uuid.uuid4()
        user_id = uuid.uuid4()
        future_time = int(time.time()) + 400  # More than 300s skew
        nonce = "0123456789abcdef"
        state_payload = f"{ws_id}:{user_id}:{future_time}:{nonce}"
        key = settings.get_primary_encryption_key() or settings.TOKEN_ENCRYPTION_KEY or "fallback_key"
        sig = hmac.new(key.encode("utf-8"), state_payload.encode("utf-8"), hashlib.sha256).hexdigest()[:16]
        future_state = f"{state_payload}:{sig}"

        assert verify_oauth_state(future_state, ws_id, user_id) is False

    @pytest.mark.asyncio
    async def test_state_single_use_replay_prevention_memory(self):
        replay_cache.reset()
        state = f"state_token_{uuid.uuid4()}"
        state_hash = hashlib.sha256(state.encode("utf-8")).hexdigest()

        # First use succeeds
        is_fresh = await replay_cache.check_and_record(state_hash, ttl_seconds=900, namespace="oauth_state")
        assert is_fresh is True

        # Second use (replay) fails
        is_replayed = await replay_cache.check_and_record(state_hash, ttl_seconds=900, namespace="oauth_state")
        assert is_replayed is False

    @pytest.mark.asyncio
    async def test_state_single_use_replay_prevention_redis(self):
        mock_redis = MockRedisClient()
        replay_cache.set_redis_client(mock_redis)
        state = f"state_token_{uuid.uuid4()}"
        state_hash = hashlib.sha256(state.encode("utf-8")).hexdigest()

        # First use succeeds with Redis
        is_fresh = await replay_cache.check_and_record(state_hash, ttl_seconds=900, namespace="oauth_state")
        assert is_fresh is True

        # Second use fails because Redis NX condition fails
        is_replayed = await replay_cache.check_and_record(state_hash, ttl_seconds=900, namespace="oauth_state")
        assert is_replayed is False


class TestSignedRequestVerificationAndReplay:
    def setup_method(self):
        replay_cache.reset()

    def test_signed_request_valid(self):
        secret = "test_meta_app_secret_12345"
        payload = {
            "algorithm": "HMAC-SHA256",
            "user_id": f"meta_user_{uuid.uuid4()}",
            "issued_at": int(time.time()),
        }
        signed_request = _make_signed_request(payload, secret)

        parsed = parse_signed_request(signed_request, secret, check_replay=False)
        assert parsed["algorithm"] == "HMAC-SHA256"

    def test_signed_request_tampered_payload_rejected(self):
        secret = "test_meta_app_secret_12345"
        payload = {"algorithm": "HMAC-SHA256", "user_id": "meta_user_9988"}
        signed_request = _make_signed_request(payload, secret)

        # Alter payload
        sig_b64, _ = signed_request.split(".", 1)
        tampered_payload = {"algorithm": "HMAC-SHA256", "user_id": "meta_user_ATTACKER"}
        tampered_b64 = base64.urlsafe_b64encode(json.dumps(tampered_payload).encode()).decode().rstrip("=")
        tampered_sr = f"{sig_b64}.{tampered_b64}"

        with pytest.raises(HTTPException) as exc_info:
            parse_signed_request(tampered_sr, secret, check_replay=False)
        assert exc_info.value.status_code == 400
        assert "Invalid signed_request signature" in exc_info.value.detail

    def test_signed_request_wrong_secret_rejected(self):
        secret = "correct_secret"
        payload = {"algorithm": "HMAC-SHA256", "user_id": "meta_user_9988"}
        signed_request = _make_signed_request(payload, secret)

        with pytest.raises(HTTPException) as exc_info:
            parse_signed_request(signed_request, "wrong_secret", check_replay=False)
        assert exc_info.value.status_code == 400
        assert "Invalid signed_request signature" in exc_info.value.detail

    def test_signed_request_expired_issued_at_rejected(self):
        secret = "test_meta_app_secret_12345"
        payload = {
            "algorithm": "HMAC-SHA256",
            "user_id": "meta_user_9988",
            "issued_at": int(time.time()) - 1000,  # Older than 900s
        }
        signed_request = _make_signed_request(payload, secret)

        with pytest.raises(HTTPException) as exc_info:
            parse_signed_request(signed_request, secret, max_age_seconds=900, check_replay=False)
        assert exc_info.value.status_code == 400
        assert "signed_request has expired" in exc_info.value.detail

    def test_signed_request_future_issued_at_rejected(self):
        secret = "test_meta_app_secret_12345"
        payload = {
            "algorithm": "HMAC-SHA256",
            "user_id": "meta_user_9988",
            "issued_at": int(time.time()) + 400,  # More than 300s clock skew
        }
        signed_request = _make_signed_request(payload, secret)

        with pytest.raises(HTTPException) as exc_info:
            parse_signed_request(signed_request, secret, check_replay=False)
        assert exc_info.value.status_code == 400
        assert "signed_request timestamp is in the future" in exc_info.value.detail

    def test_signed_request_replay_rejection_sync(self):
        secret = "test_meta_app_secret_12345"
        uid = str(uuid.uuid4())
        payload = {
            "algorithm": "HMAC-SHA256",
            "user_id": uid,
            "issued_at": int(time.time()),
        }
        signed_request = _make_signed_request(payload, secret)

        # First verification succeeds
        parsed = parse_signed_request(signed_request, secret, check_replay=True)
        assert parsed["user_id"] == uid

        # Immediate replay must fail
        with pytest.raises(HTTPException) as exc_info:
            parse_signed_request(signed_request, secret, check_replay=True)
        assert exc_info.value.status_code == 400
        assert "already been processed or replayed" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_signed_request_replay_rejection_async_memory(self):
        replay_cache.reset()
        secret = "test_meta_app_secret_12345"
        uid = str(uuid.uuid4())
        payload = {
            "algorithm": "HMAC-SHA256",
            "user_id": uid,
            "issued_at": int(time.time()),
        }
        signed_request = _make_signed_request(payload, secret)

        # First async verification succeeds
        parsed = await verify_and_parse_signed_request(signed_request, secret)
        assert parsed["user_id"] == uid

        # Replay must be rejected
        with pytest.raises(HTTPException) as exc_info:
            await verify_and_parse_signed_request(signed_request, secret)
        assert exc_info.value.status_code == 400
        assert "already been processed or replayed" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_signed_request_replay_rejection_async_redis(self):
        mock_redis = MockRedisClient()
        replay_cache.set_redis_client(mock_redis)
        secret = "test_meta_app_secret_12345"
        uid = str(uuid.uuid4())
        payload = {
            "algorithm": "HMAC-SHA256",
            "user_id": uid,
            "issued_at": int(time.time()),
        }
        signed_request = _make_signed_request(payload, secret)

        # First async verification succeeds with Redis
        parsed = await verify_and_parse_signed_request(signed_request, secret)
        assert parsed["user_id"] == uid

        # Replay must be rejected with Redis
        with pytest.raises(HTTPException) as exc_info:
            await verify_and_parse_signed_request(signed_request, secret)
        assert exc_info.value.status_code == 400
        assert "already been processed or replayed" in exc_info.value.detail
