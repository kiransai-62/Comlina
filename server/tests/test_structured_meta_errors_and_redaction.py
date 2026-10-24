# server/tests/test_structured_meta_errors_and_redaction.py
import pytest
import httpx
from unittest.mock import AsyncMock, MagicMock, patch
import uuid
from datetime import datetime, timezone

from app.core.logging import redact_string, redact_data, log_diagnostic_event
from app.integrations.instagram.exceptions import (
    MetaGraphAPIError,
    MetaRateLimitError,
    MetaTokenExpiredError,
    MetaFollowerCheckUnavailable,
)
from app.integrations.instagram.client import MetaGraphClient
from app.engine.action_engine import ActionEngine
from app.jobs.process_comment import _update_webhook_event, process_comment_job
from app.models import WebhookEvent


def test_meta_error_creation_and_structured_fields():
    """Verify MetaGraphAPIError preserves safe structured fields and diagnostic dict."""
    err = MetaGraphAPIError(
        message="Application does not have permission",
        code=10,
        error_subcode=200,
        http_status=403,
        error_type="OAuthException",
        is_transient=False,
        fbtrace_id="FBTrace_12345",
        provider="META_INSTAGRAM",
    )

    assert err.provider == "META_INSTAGRAM"
    assert err.code == 10
    assert err.error_subcode == 200
    assert err.http_status == 403
    assert err.error_type == "OAuthException"
    assert err.is_transient is False
    assert err.fbtrace_id == "FBTrace_12345"
    assert "permission" in str(err)
    assert err.sanitized_message == err.message

    diag = err.to_diagnostic_dict()
    assert diag["provider"] == "META_INSTAGRAM"
    assert diag["code"] == 10
    assert diag["error_subcode"] == 200
    assert diag["http_status"] == 403
    assert diag["error_type"] == "OAuthException"
    assert diag["is_transient"] is False
    assert diag["fbtrace_id"] == "FBTrace_12345"
    assert "permission" in diag["sanitized_message"]


def test_meta_error_sanitization_on_init():
    """Verify secrets and Meta access tokens are scrubbed on exception creation."""
    raw_msg = (
        "Invalid token EAABwc56s9876543210zyxwvutsrq - "
        "Bearer eyJhbGciOiJIUzI1NiJ9.secret_part - "
        "client_secret=super_secret_app_key"
    )
    err = MetaGraphAPIError(raw_msg, code=190)

    # All credentials must be redacted from message and str()
    assert "EAABwc56s9876543210zyxwvutsrq" not in err.message
    assert "eyJhbGciOiJIUzI1NiJ9" not in err.message
    assert "super_secret_app_key" not in err.message
    assert "[REDACTED_META_TOKEN]" in err.message
    assert "Bearer [REDACTED]" in err.message
    assert "client_secret=[REDACTED]" in err.message
    assert str(err) == err.message


def test_transient_vs_permanent_classification():
    """Verify transient rate-limits and server errors are distinguished from permanent policy/auth failures."""
    # Transient: Rate limits
    assert MetaGraphAPIError("Rate limit", code=4).is_transient is True
    assert MetaGraphAPIError("Rate limit", code=17).is_transient is True
    assert MetaGraphAPIError("Rate limit", code=32).is_transient is True
    assert MetaGraphAPIError("Rate limit", code=613).is_transient is True
    assert MetaGraphAPIError("Rate limit", http_status=429).is_transient is True

    # Transient: Meta internal server errors
    assert MetaGraphAPIError("Internal error", code=1).is_transient is True
    assert MetaGraphAPIError("Internal error", code=2).is_transient is True
    assert MetaGraphAPIError("Server error", code=500, http_status=500).is_transient is True
    assert MetaGraphAPIError("Bad gateway", code=502, http_status=502).is_transient is True

    # Permanent: Token expired (190)
    assert MetaGraphAPIError("Token expired", code=190).is_transient is False

    # Permanent: Permission denied (10, 200, 298)
    assert MetaGraphAPIError("Permission denied", code=10).is_transient is False
    assert MetaGraphAPIError("Permission denied", code=200).is_transient is False

    # Permanent: Invalid parameter / bad request (100)
    assert MetaGraphAPIError("Invalid parameter", code=100).is_transient is False

    # Permanent: Comment expired subcode (2018001)
    assert MetaGraphAPIError("Comment expired", code=100, error_subcode=2018001).is_transient is False

    # Subclasses have fixed transient properties
    assert MetaRateLimitError("Too many calls").is_transient is True
    assert MetaTokenExpiredError("Session invalidated").is_transient is False
    assert MetaFollowerCheckUnavailable("Cannot check follower").is_transient is False


def test_client_handle_response_meta_error_parsing():
    """Verify client parses Meta error JSON payload with all structured fields."""
    client = MetaGraphClient(access_token="fake_token")

    # 1. Token Expired payload
    mock_resp = MagicMock()
    mock_resp.status_code = 401
    mock_resp.json.return_value = {
        "error": {
            "message": "Error validating access token: Session has expired.",
            "type": "OAuthException",
            "code": 190,
            "error_subcode": 463,
            "is_transient": False,
            "fbtrace_id": "AbCdEf12345",
        }
    }

    with pytest.raises(MetaTokenExpiredError) as exc_info:
        client._handle_response(mock_resp)

    err = exc_info.value
    assert err.code == 190
    assert err.error_subcode == 463
    assert err.http_status == 401
    assert err.error_type == "OAuthException"
    assert err.is_transient is False
    assert err.fbtrace_id == "AbCdEf12345"

    # 2. Rate Limit payload
    mock_resp_rl = MagicMock()
    mock_resp_rl.status_code = 429
    mock_resp_rl.json.return_value = {
        "error": {
            "message": "Application request limit reached",
            "type": "OAuthException",
            "code": 4,
            "error_subcode": 0,
            "fbtrace_id": "TraceRateLimit_99",
        }
    }

    with pytest.raises(MetaRateLimitError) as exc_rl:
        client._handle_response(mock_resp_rl)

    assert exc_rl.value.is_transient is True
    assert exc_rl.value.code == 4
    assert exc_rl.value.fbtrace_id == "TraceRateLimit_99"


def test_client_handle_response_malformed_provider_response():
    """Verify client sanitizes malformed/non-JSON provider responses without dumping secrets."""
    client = MetaGraphClient(access_token="fake_token")

    mock_resp = MagicMock()
    mock_resp.status_code = 502
    # Non-JSON response containing sensitive token in query string
    mock_resp.text = "<html>502 Bad Gateway for https://graph.instagram.com?access_token=EAABwc56s9876543210</html>"
    mock_resp.json.side_effect = ValueError("No JSON object could be decoded")

    with pytest.raises(MetaGraphAPIError) as exc_info:
        client._handle_response(mock_resp)

    err = exc_info.value
    assert err.http_status == 502
    assert err.error_type == "MalformedResponse"
    assert err.is_transient is True  # 502 is transient
    # Verify the raw token was scrubbed from the exception message
    assert "EAABwc56s9876543210" not in err.message
    assert "[REDACTED]" in err.message or "[REDACTED_META_TOKEN]" in err.message


@pytest.mark.asyncio
async def test_client_retry_behavior_transient_vs_permanent():
    """Verify client retries transient failures but never retries permanent invalid parameter or policy errors."""
    client = MetaGraphClient(access_token="fake_token")

    # 1. Transient rate-limit error: Should retry and succeed if attempt 2 succeeds
    with patch("httpx.AsyncClient") as mock_client_cls, patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
        mock_instance = AsyncMock()
        mock_client_cls.return_value.__aenter__.return_value = mock_instance

        resp_429 = MagicMock()
        resp_429.status_code = 429
        resp_429.json.return_value = {"error": {"message": "Rate limited", "code": 4}}

        resp_200 = MagicMock()
        resp_200.status_code = 200
        resp_200.json.return_value = {"success": True}

        mock_instance.get.side_effect = [resp_429, resp_200]

        res = await client.get("/me")
        assert res == {"success": True}
        assert mock_instance.get.call_count == 2
        mock_sleep.assert_called_once()

    # 2. Permanent parameter / policy error (code 100): Must raise on attempt 1 without retry
    with patch("httpx.AsyncClient") as mock_client_cls, patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
        mock_instance = AsyncMock()
        mock_client_cls.return_value.__aenter__.return_value = mock_instance

        resp_100 = MagicMock()
        resp_100.status_code = 400
        resp_100.json.return_value = {"error": {"message": "Invalid parameter", "code": 100}}

        mock_instance.get.side_effect = [resp_100]

        with pytest.raises(MetaGraphAPIError) as exc_info:
            await client.get("/me")

        assert exc_info.value.code == 100
        assert exc_info.value.is_transient is False
        assert mock_instance.get.call_count == 1
        mock_sleep.assert_not_called()


def test_privacy_safe_redaction_patterns():
    """Verify redact_string and redact_data properly scrub all sensitive keys and tokens."""
    # Standalone Meta token
    assert "EAABwc56s9876543210zyx" not in redact_string("OAuth error with EAABwc56s9876543210zyx token")

    # Authorization header
    raw_header = "Authorization: Bearer my_secret_token_12345"
    assert "my_secret_token_12345" not in redact_string(raw_header)

    # Query param
    url = "https://api.com/v1?access_token=secret_tok_99&app_secret=secret_app_88"
    assert "secret_tok_99" not in redact_string(url)
    assert "secret_app_88" not in redact_string(url)

    # Dict redaction
    payload = {
        "event_id": "evt_123",
        "action": "PUBLIC_REPLY",
        "credentials": {
            "access_token": "token_111",
            "encryption_key": "enc_222",
            "client_secret": "sec_333",
            "normal_data": "safe_val"
        }
    }
    redacted = redact_data(payload)
    assert redacted["credentials"]["access_token"] == "[REDACTED]"
    assert redacted["credentials"]["encryption_key"] == "[REDACTED]"
    assert redacted["credentials"]["client_secret"] == "[REDACTED]"
    assert redacted["credentials"]["normal_data"] == "safe_val"


@pytest.mark.asyncio
async def test_action_engine_structured_meta_error_and_content_safe_logging():
    """Verify ActionEngine logs metadata only and attaches structured meta_error diagnostics on failure."""
    client_mock = MagicMock()

    # Create MetaGraphAPIError with token in message
    meta_err = MetaGraphAPIError(
        message="Cannot reply to comment with token EAABwc56s9876543210",
        code=100,
        error_subcode=2018001,
        http_status=400,
        error_type="GraphMethodException",
        is_transient=False,
        fbtrace_id="TraceCommentExpired",
    )

    with patch("app.integrations.instagram.InstagramComments.reply_to_comment", side_effect=meta_err):
        action_config = {"type": "PUBLIC_REPLY", "text": "Thanks @{username}! Check your DMs"}
        context = {"comment_id": "comm_999", "sender_username": "testuser"}

        with patch("app.engine.action_engine.logger.info") as mock_info:
            result = await ActionEngine.execute_action(action_config, context, instagram_client=client_mock)

        assert result["status"] == "FAILED"
        assert result["meta_error"]["code"] == 100
        assert result["meta_error"]["subcode"] == 2018001
        assert result["meta_diagnostic"]["is_transient"] is False
        assert result["meta_diagnostic"]["fbtrace_id"] == "TraceCommentExpired"
        assert "EAABwc56s9876543210" not in result["meta_diagnostic"]["sanitized_message"]

        # Verify logger.info did NOT log the raw message text
        log_msg = mock_info.call_args[0][0]
        assert "text_len=" in log_msg
        assert "Thanks @testuser" not in log_msg


@pytest.mark.asyncio
async def test_persisted_diagnostics_and_webhook_event_error_sanitization():
    """Verify _update_webhook_event redacts secrets before storing in WebhookEvent.error."""
    mock_session = AsyncMock()
    wh_event = WebhookEvent(
        id=uuid.uuid4(),
        provider_event_id="prov_123",
        event_type="COMMENT",
        payload={},
        status="PENDING",
    )
    mock_res = MagicMock()
    mock_res.scalar_one_or_none.return_value = wh_event
    mock_session.execute.return_value = mock_res

    sensitive_error = "Meta error for EAABwc56s9876543210 with client_secret=very_secret_key"
    await _update_webhook_event(mock_session, str(wh_event.id), "prov_123", "FAILED", sensitive_error)

    assert wh_event.status == "FAILED"
    assert wh_event.error is not None
    assert "EAABwc56s9876543210" not in wh_event.error
    assert "very_secret_key" not in wh_event.error
    assert "[REDACTED_META_TOKEN]" in wh_event.error
    assert "client_secret=[REDACTED]" in wh_event.error
