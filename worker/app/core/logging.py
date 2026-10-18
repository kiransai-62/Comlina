# worker/app/core/logging.py
import json
import logging
import re
from contextvars import ContextVar
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Union

# Context variables for correlation
request_id_ctx: ContextVar[Optional[str]] = ContextVar("request_id", default=None)
client_ip_ctx: ContextVar[Optional[str]] = ContextVar("client_ip", default=None)
workspace_id_ctx: ContextVar[Optional[str]] = ContextVar("workspace_id", default=None)


def set_log_context(
    request_id: Optional[str] = None,
    client_ip: Optional[str] = None,
    workspace_id: Optional[str] = None
) -> None:
    if request_id is not None:
        request_id_ctx.set(request_id)
    if client_ip is not None:
        client_ip_ctx.set(client_ip)
    if workspace_id is not None:
        workspace_id_ctx.set(workspace_id)


def clear_log_context() -> None:
    request_id_ctx.set(None)
    client_ip_ctx.set(None)
    workspace_id_ctx.set(None)


def get_log_context() -> Dict[str, Optional[str]]:
    return {
        "request_id": request_id_ctx.get(),
        "client_ip": client_ip_ctx.get(),
        "workspace_id": workspace_id_ctx.get(),
    }


# Sensitive field keys for dictionary and JSON inspection
SENSITIVE_KEYS = {
    "password",
    "secret",
    "client_secret",
    "app_secret",
    "access_token",
    "refresh_token",
    "token",
    "api_key",
    "apikey",
    "authorization",
    "signed_request",
    "signature",
    "x-hub-signature",
    "x-hub-signature-256",
    "private_key",
    "encryption_key",
    "service_role_key",
    "anon_key",
}

# Regex patterns for stripping sensitive strings in log messages
BEARER_PATTERN = re.compile(r"(?i)\b(Bearer|Basic)\s+[A-Za-z0-9\-._~+/]+=*", re.IGNORECASE)
SIGNATURE_HEADER_PATTERN = re.compile(r"(?i)(sha256=)[0-9a-fA-F]{32,64}")

KEY_VALUE_PATTERN = re.compile(
    r"(?i)(['\"]?(?:password|secret|client_secret|access_token|refresh_token|api_key|signed_request|signature|token)['\"]?\s*[:=]\s*['\"]?)([^\"'\s,;&]+)(['\"]?)",
    re.IGNORECASE
)

QUERY_PARAM_PATTERN = re.compile(
    r"(?i)([?&](?:access_token|code|client_secret|signed_request|signature)=)([^& \t\r\n]+)",
    re.IGNORECASE
)


def redact_string(text: str) -> str:
    """Scrub sensitive credentials, tokens, and query parameters from text."""
    if not isinstance(text, str) or not text:
        return text

    # 1. Bearer / Basic auth tokens
    text = BEARER_PATTERN.sub(r"\1 [REDACTED]", text)

    # 2. Meta webhook signature header sha256=...
    text = SIGNATURE_HEADER_PATTERN.sub(r"\1[REDACTED]", text)

    # 3. Query string secrets (?access_token=... / &signed_request=...)
    text = QUERY_PARAM_PATTERN.sub(r"\1[REDACTED]", text)

    # 4. Key-value pairs (key=value, "key": "value", key: value)
    text = KEY_VALUE_PATTERN.sub(r"\1[REDACTED]\3", text)

    return text


def redact_data(data: Any) -> Any:
    """Recursively redact dictionary and list data structures."""
    if isinstance(data, dict):
        cleaned = {}
        for k, v in data.items():
            if isinstance(v, (dict, list, tuple, set)):
                cleaned[k] = redact_data(v)
            else:
                key_lower = str(k).lower().replace("_", "").replace("-", "")
                if any(s.replace("_", "").replace("-", "") == key_lower for s in SENSITIVE_KEYS):
                    cleaned[k] = "[REDACTED]"
                else:
                    cleaned[k] = redact_data(v)
        return cleaned
    elif isinstance(data, (list, tuple, set)):
        items = [redact_data(item) for item in data]
        return type(data)(items)
    elif isinstance(data, str):
        return redact_string(data)
    return data


class RedactionFilter(logging.Filter):
    """
    Logging filter that sanitizes sensitive data from log records and
    injects context variables (request_id, client_ip, workspace_id).
    """

    def filter(self, record: logging.LogRecord) -> bool:
        # 1. Inject contextvars if not already set on the record
        if not hasattr(record, "request_id") or record.request_id is None:
            record.request_id = request_id_ctx.get()
        if not hasattr(record, "client_ip") or record.client_ip is None:
            record.client_ip = client_ip_ctx.get()
        if not hasattr(record, "workspace_id") or record.workspace_id is None:
            record.workspace_id = workspace_id_ctx.get()

        # 2. Redact record message
        if isinstance(record.msg, str):
            record.msg = redact_string(record.msg)
        elif isinstance(record.msg, dict):
            record.msg = redact_data(record.msg)

        # 3. Redact args if present
        if record.args:
            if isinstance(record.args, dict):
                record.args = redact_data(record.args)
            elif isinstance(record.args, tuple):
                record.args = tuple(redact_data(a) for a in record.args)
            elif isinstance(record.args, list):
                record.args = [redact_data(a) for a in record.args]

        return True


class JsonFormatter(logging.Formatter):
    """Structured JSON log formatter for production observability."""

    def format(self, record: logging.LogRecord) -> str:
        # Format the log message with any args
        try:
            msg = record.getMessage()
        except Exception:
            msg = str(record.msg)

        # Scrub the final rendered message as defense-in-depth
        msg = redact_string(msg)

        log_entry: Dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": msg,
            "request_id": getattr(record, "request_id", None),
            "client_ip": getattr(record, "client_ip", None),
            "workspace_id": getattr(record, "workspace_id", None),
        }

        # Include exception traceback if present (with redaction)
        if record.exc_info:
            exc_text = self.formatException(record.exc_info)
            log_entry["exception"] = redact_string(exc_text)

        return json.dumps(log_entry, default=str)


def setup_logging(level: int = logging.INFO, force_json: bool = False) -> None:
    """
    Configures worker logging with the RedactionFilter and JsonFormatter.
    Safe to call multiple times (idempotent).
    """
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    has_redaction = any(isinstance(f, RedactionFilter) for f in root_logger.filters)
    if not has_redaction:
        root_logger.addFilter(RedactionFilter())

    for handler in root_logger.handlers:
        if not any(isinstance(f, RedactionFilter) for f in handler.filters):
            handler.addFilter(RedactionFilter())
        if force_json and not isinstance(handler.formatter, JsonFormatter):
            handler.setFormatter(JsonFormatter())
