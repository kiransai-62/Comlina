# worker/tests/test_worker_structured_errors_and_redaction.py
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import uuid

from app.core.logging import redact_string, redact_data
from app.integrations.instagram.exceptions import (
    MetaGraphAPIError,
    MetaRateLimitError,
    MetaTokenExpiredError,
    MetaFollowerCheckUnavailable,
)
from app.integrations.instagram.client import MetaGraphClient
from app.engine.action_engine import ActionEngine
from app.jobs.process_comment import _update_webhook_event
from app.models import WebhookEvent


def test_worker_meta_error_structured_fields_and_redaction():
    """Verify worker MetaGraphAPIError preserves structured fields and redacts secrets."""
    raw_msg = "Error validating access token: EAABwc56s9876543210 with secret=mock_synthetic_secret_fixture"
    err = MetaGraphAPIError(
        message=raw_msg,
        code=190,
        error_subcode=463,
        http_status=401,
        error_type="OAuthException",
        is_transient=False,
        fbtrace_id="TraceWorker_123"
    )

    assert err.provider == "META_INSTAGRAM"
    assert err.code == 190
    assert err.error_subcode == 463
    assert err.http_status == 401
    assert err.error_type == "OAuthException"
    assert err.is_transient is False
    assert err.fbtrace_id == "TraceWorker_123"

    assert "EAABwc56s9876543210" not in err.message
    assert "mock_synthetic_secret_fixture" not in err.message
    assert "[REDACTED_META_TOKEN]" in err.message
    assert "secret=[REDACTED]" in err.message

    diag = err.to_diagnostic_dict()
    assert diag["code"] == 190
    assert diag["is_transient"] is False
    assert "EAABwc56s9876543210" not in diag["sanitized_message"]


def test_worker_transient_vs_permanent_classification():
    """Verify worker transient/permanent error distinction."""
    # Transient rate limits
    assert MetaGraphAPIError("Rate limited", code=4).is_transient is True
    assert MetaRateLimitError("Rate limit").is_transient is True
    assert MetaGraphAPIError("Rate limit", http_status=429).is_transient is True

    # Transient 5xx
    assert MetaGraphAPIError("Meta server error", code=500, http_status=500).is_transient is True

    # Permanent failures
    assert MetaTokenExpiredError("Token expired").is_transient is False
    assert MetaGraphAPIError("Invalid parameters", code=100).is_transient is False
    assert MetaGraphAPIError("Permission denied", code=10).is_transient is False
    assert MetaFollowerCheckUnavailable("Check unavailable").is_transient is False


@pytest.mark.asyncio
async def test_worker_client_retry_behavior():
    """Verify worker client retries transient errors and immediately fails on permanent errors."""
    client = MetaGraphClient(access_token="fake_token")

    # 1. Transient rate limit: retries and succeeds on 2nd attempt
    with patch("httpx.AsyncClient") as mock_client_cls, patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
        mock_instance = AsyncMock()
        mock_client_cls.return_value.__aenter__.return_value = mock_instance

        resp_429 = MagicMock(status_code=429)
        resp_429.json.return_value = {"error": {"message": "Rate limited", "code": 613}}

        resp_200 = MagicMock(status_code=200)
        resp_200.json.return_value = {"data": [{"id": "123"}]}

        mock_instance.get.side_effect = [resp_429, resp_200]

        res = await client.get("/me")
        assert res == {"data": [{"id": "123"}]}
        assert mock_instance.get.call_count == 2
        mock_sleep.assert_called_once()

    # 2. Permanent error (code 100): does not retry
    with patch("httpx.AsyncClient") as mock_client_cls, patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
        mock_instance = AsyncMock()
        mock_client_cls.return_value.__aenter__.return_value = mock_instance

        resp_100 = MagicMock(status_code=400)
        resp_100.json.return_value = {"error": {"message": "Invalid param", "code": 100}}

        mock_instance.get.side_effect = [resp_100]

        with pytest.raises(MetaGraphAPIError) as exc_info:
            await client.get("/me")

        assert exc_info.value.code == 100
        assert exc_info.value.is_transient is False
        assert mock_instance.get.call_count == 1
        mock_sleep.assert_not_called()


@pytest.mark.asyncio
async def test_worker_action_engine_structured_meta_error_attachment():
    """Verify worker ActionEngine attaches structured meta_error diagnostics on failure."""
    client_mock = MagicMock()
    meta_err = MetaGraphAPIError(
        message="Cannot send private reply: token EAABwc56s9876543210 expired",
        code=190,
        error_subcode=463,
        http_status=401,
        is_transient=False,
        fbtrace_id="TraceWorkerAction",
    )

    with patch("app.integrations.instagram.InstagramMessaging.send_private_reply", side_effect=meta_err):
        action_config = {"type": "PRIVATE_DM", "text": "Hello {first_name}!"}
        context = {"comment_id": "comm_111", "sender_id": "user_222", "sender_username": "worker_user"}

        result = await ActionEngine.execute_action(action_config, context, instagram_client=client_mock)

        assert result["status"] == "FAILED"
        assert result["meta_error"]["code"] == 190
        assert result["meta_error"]["subcode"] == 463
        assert result["meta_diagnostic"]["is_transient"] is False
        assert result["meta_diagnostic"]["fbtrace_id"] == "TraceWorkerAction"
        assert "EAABwc56s9876543210" not in result["meta_diagnostic"]["sanitized_message"]
