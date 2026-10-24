# server/tests/test_token_and_subscription_health.py
import pytest
from unittest.mock import MagicMock, patch
from app.main import verify_encryption_keys
from app.core.config import settings
from app.integrations.instagram.oauth import subscribe_app_to_account


@pytest.mark.asyncio
async def test_verify_encryption_keys_production_missing_keys(monkeypatch):
    monkeypatch.setattr(settings, "ENVIRONMENT", "production")
    monkeypatch.setattr(settings, "TOKEN_ENCRYPTION_KEYS", "")
    with pytest.raises(RuntimeError, match="CRITICAL: TOKEN_ENCRYPTION_KEYS missing in production"):
        await verify_encryption_keys()


@pytest.mark.asyncio
async def test_verify_encryption_keys_production_failure(monkeypatch):
    monkeypatch.setattr(settings, "ENVIRONMENT", "production")
    monkeypatch.setattr(settings, "TOKEN_ENCRYPTION_KEYS", "dummy_key")
    with patch("app.core.encryption.decrypt_token", side_effect=Exception("Corrupted decryption")):
        with pytest.raises(RuntimeError, match="CRITICAL: Token decryption healthcheck failed"):
            await verify_encryption_keys()


@pytest.mark.asyncio
async def test_verify_encryption_keys_production_valid(monkeypatch):
    from cryptography.fernet import Fernet
    key = Fernet.generate_key().decode()
    monkeypatch.setattr(settings, "ENVIRONMENT", "production")
    monkeypatch.setattr(settings, "TOKEN_ENCRYPTION_KEYS", key)
    # Should not raise any error
    await verify_encryption_keys()


@pytest.mark.asyncio
async def test_subscribe_app_to_account_success():
    mock_resp = MagicMock()
    mock_resp.json.return_value = {"success": True}
    
    with patch("httpx.AsyncClient.post", return_value=mock_resp):
        res = await subscribe_app_to_account("ig_12345", "mock_token")
        assert res is True


@pytest.mark.asyncio
async def test_subscribe_app_to_account_failure():
    mock_resp = MagicMock()
    mock_resp.json.return_value = {"success": False, "error": {"message": "Permission denied"}}
    
    with patch("httpx.AsyncClient.post", return_value=mock_resp):
        res = await subscribe_app_to_account("ig_12345", "mock_token")
        assert res is False
