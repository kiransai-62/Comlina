# server/tests/test_logging_and_redaction.py
import json
import logging
import pytest
from unittest.mock import MagicMock
from fastapi.testclient import TestClient

from app.core.logging import (
    redact_string,
    redact_data,
    RedactionFilter,
    JsonFormatter,
    set_log_context,
    clear_log_context,
    get_log_context,
    setup_logging
)
from app.main import app


def test_redact_bearer_and_basic_auth():
    raw_bearer = "Authorization: Bearer test_token_abc123_xyz"
    scrubbed = redact_string(raw_bearer)
    assert "test_token_abc123_xyz" not in scrubbed
    assert "Bearer [REDACTED]" in scrubbed

    raw_basic = "Authorization: Basic dXNlcjpwYXNz"
    scrubbed_basic = redact_string(raw_basic)
    assert "Basic [REDACTED]" in scrubbed_basic


def test_redact_meta_webhook_signatures():
    raw_sig = "X-Hub-Signature-256: sha256=abcdef0123456789abcdef0123456789abcdef0123456789abcdef0123456789"
    scrubbed = redact_string(raw_sig)
    assert "sha256=[REDACTED]" in scrubbed
    assert "abcdef0123456789" not in scrubbed


def test_redact_query_param_secrets():
    url = "https://graph.facebook.com/v19.0/oauth/access_token?client_secret=top_secret_code_123&signed_request=signed_req_token_456"
    scrubbed = redact_string(url)
    assert "top_secret_code_123" not in scrubbed
    assert "signed_req_token_456" not in scrubbed
    assert "client_secret=[REDACTED]" in scrubbed
    assert "signed_request=[REDACTED]" in scrubbed


def test_redact_key_value_assignments():
    text = "User login attempt with password=sensitive_password_999 and token: my_secret_token_888"
    scrubbed = redact_string(text)
    assert "sensitive_password_999" not in scrubbed
    assert "my_secret_token_888" not in scrubbed
    assert "[REDACTED]" in scrubbed


def test_redact_nested_dictionary():
    payload = {
        "user_id": "usr_123",
        "username": "alice",
        "auth": {
            "password": "plain_password_123",
            "access_token": "token_xyz",
            "api_key": "api_key_abc",
            "metadata": {
                "secret": "deep_secret",
                "normal_field": "visible_value"
            }
        },
        "tags": ["admin", "staff"]
    }
    cleaned = redact_data(payload)
    assert cleaned["user_id"] == "usr_123"
    assert cleaned["username"] == "alice"
    assert cleaned["auth"]["password"] == "[REDACTED]"
    assert cleaned["auth"]["access_token"] == "[REDACTED]"
    assert cleaned["auth"]["api_key"] == "[REDACTED]"
    assert cleaned["auth"]["metadata"]["secret"] == "[REDACTED]"
    assert cleaned["auth"]["metadata"]["normal_field"] == "visible_value"
    assert cleaned["tags"] == ["admin", "staff"]


def test_redaction_filter_and_contextvars():
    filter_obj = RedactionFilter()
    clear_log_context()
    set_log_context(request_id="req-unit-123", client_ip="192.168.1.50", workspace_id="ws-uuid-789")

    record = logging.LogRecord(
        name="test_logger",
        level=logging.INFO,
        pathname=__file__,
        lineno=10,
        msg="Connecting with access_token=secret_key_val to backend",
        args=(),
        exc_info=None
    )

    filter_obj.filter(record)

    assert record.request_id == "req-unit-123"
    assert record.client_ip == "192.168.1.50"
    assert record.workspace_id == "ws-uuid-789"
    assert "secret_key_val" not in record.msg
    assert "[REDACTED]" in record.msg

    clear_log_context()
    ctx = get_log_context()
    assert ctx["request_id"] is None
    assert ctx["client_ip"] is None
    assert ctx["workspace_id"] is None


def test_json_formatter_structure():
    formatter = JsonFormatter()
    record = logging.LogRecord(
        name="api_logger",
        level=logging.ERROR,
        pathname=__file__,
        lineno=42,
        msg="Failed request for user %s with bearer token %s",
        args=("bob", "Bearer my_super_secret_token_123"),
        exc_info=None
    )
    record.request_id = "req-json-456"
    record.client_ip = "10.0.0.1"
    record.workspace_id = "ws-999"

    formatted_json_str = formatter.format(record)
    parsed = json.loads(formatted_json_str)

    assert parsed["level"] == "ERROR"
    assert parsed["logger"] == "api_logger"
    assert parsed["request_id"] == "req-json-456"
    assert parsed["client_ip"] == "10.0.0.1"
    assert parsed["workspace_id"] == "ws-999"
    assert "my_super_secret_token_123" not in parsed["message"]
    assert "Bearer [REDACTED]" in parsed["message"]
    assert "timestamp" in parsed


def test_request_lifecycle_context_propagation():
    client = TestClient(app)
    clear_log_context()

    response = client.get(
        "/health",
        headers={
            "X-Request-ID": "req-e2e-correlation-id",
            "X-Workspace-ID": "ws-e2e-correlation-id"
        }
    )
    assert response.status_code == 200
    assert response.headers.get("x-request-id") == "req-e2e-correlation-id"

    # Context should be cleaned up after request dispatch completes
    ctx = get_log_context()
    assert ctx["request_id"] is None
    assert ctx["workspace_id"] is None
