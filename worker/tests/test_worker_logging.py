# worker/tests/test_worker_logging.py
import json
import logging
import pytest

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


def test_worker_redact_secrets():
    text = "Executing task for access_token=tok_abc123 and secret=my_key"
    scrubbed = redact_string(text)
    assert "tok_abc123" not in scrubbed
    assert "my_key" not in scrubbed
    assert "[REDACTED]" in scrubbed


def test_worker_json_formatter():
    formatter = JsonFormatter()
    clear_log_context()
    set_log_context(request_id="worker-job-123", workspace_id="ws-uuid-456")

    record = logging.LogRecord(
        name="worker_job",
        level=logging.INFO,
        pathname=__file__,
        lineno=25,
        msg="Processing DM delivery with Authorization: Bearer sensitive_token_xyz",
        args=(),
        exc_info=None
    )

    filter_obj = RedactionFilter()
    filter_obj.filter(record)

    formatted = formatter.format(record)
    parsed = json.loads(formatted)

    assert parsed["level"] == "INFO"
    assert parsed["logger"] == "worker_job"
    assert parsed["request_id"] == "worker-job-123"
    assert parsed["workspace_id"] == "ws-uuid-456"
    assert "sensitive_token_xyz" not in parsed["message"]
    assert "Bearer [REDACTED]" in parsed["message"]

    clear_log_context()
