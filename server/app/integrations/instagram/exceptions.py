# server/app/integrations/instagram/exceptions.py
from typing import Optional, Dict, Any
from app.core.logging import redact_string


class MetaGraphAPIError(Exception):
    """
    Base exception for all Meta Graph API failures.
    Preserves safe structured fields:
    - provider: "META_INSTAGRAM"
    - http_status: HTTP response status code (e.g. 400, 401, 403, 429, 500)
    - code: Meta Graph API error code (e.g. 190, 4, 100, 10)
    - error_subcode: Meta Graph API subcode (e.g. 463, 2018001)
    - error_type: Meta error type (e.g. "OAuthException", "GraphMethodException")
    - is_transient: Boolean indicating if error is safe to retry
    - fbtrace_id: Safe Meta correlation ID
    - message / sanitized_message: Redacted diagnostic message safe for logs and DB
    """
    def __init__(
        self,
        message: str,
        code: int = 500,
        error_subcode: int = 0,
        http_status: Optional[int] = None,
        error_type: Optional[str] = None,
        is_transient: Optional[bool] = None,
        fbtrace_id: Optional[str] = None,
        provider: str = "META_INSTAGRAM",
    ):
        self.provider = provider
        self.code = code
        self.error_subcode = error_subcode
        self.http_status = http_status if http_status is not None else (code if 100 <= code <= 599 else 500)
        self.error_type = error_type
        self.fbtrace_id = fbtrace_id

        # Classify transient vs permanent if not explicitly provided
        if is_transient is not None:
            self.is_transient = is_transient
        else:
            # 1. Explicit rate limits -> transient
            if code in (4, 17, 32, 613) or self.http_status == 429:
                self.is_transient = True
            # 2. Meta internal temporary errors or 5xx server errors -> transient
            elif code in (1, 2) or (self.http_status in (500, 502, 503, 504) and code not in (10, 100, 190, 200)):
                self.is_transient = True
            # 3. Known permanent failures: expired tokens, invalid parameters, policy/permissions
            elif code in (10, 100, 190, 200, 298) or error_subcode == 2018001 or self.http_status in (400, 401, 403, 404, 422):
                self.is_transient = False
            else:
                self.is_transient = False

        # Redact raw message to protect tokens, keys, and credentials
        self.message = redact_string(message) if message else ""
        super().__init__(self.message)

    @property
    def sanitized_message(self) -> str:
        return self.message

    def to_diagnostic_dict(self) -> Dict[str, Any]:
        """Returns safe structured dictionary for logging, job results, and diagnostic persistence."""
        return {
            "provider": self.provider,
            "http_status": self.http_status,
            "code": self.code,
            "subcode": self.error_subcode,
            "error_subcode": self.error_subcode,
            "error_type": self.error_type,
            "is_transient": self.is_transient,
            "fbtrace_id": self.fbtrace_id,
            "message": self.message,
            "sanitized_message": self.message,
        }

    def __str__(self) -> str:
        return self.message


class MetaRateLimitError(MetaGraphAPIError):
    """Raised when Meta Graph API returns rate limit code (e.g. 4, 17, 32, 613) or HTTP 429."""
    def __init__(
        self,
        message: str,
        code: int = 4,
        error_subcode: int = 0,
        http_status: int = 429,
        **kwargs
    ):
        kwargs.setdefault("is_transient", True)
        super().__init__(message, code=code, error_subcode=error_subcode, http_status=http_status, **kwargs)


class MetaTokenExpiredError(MetaGraphAPIError):
    """Raised when the access token has expired or user deauthorized app (code 190)."""
    def __init__(
        self,
        message: str,
        code: int = 190,
        error_subcode: int = 0,
        http_status: int = 401,
        **kwargs
    ):
        kwargs.setdefault("is_transient", False)
        super().__init__(message, code=code, error_subcode=error_subcode, http_status=http_status, **kwargs)


class MetaFollowerCheckUnavailable(MetaGraphAPIError):
    """Raised when follower status check cannot be completed."""
    def __init__(
        self,
        message: str,
        code: int = 500,
        error_subcode: int = 0,
        http_status: int = 400,
        **kwargs
    ):
        kwargs.setdefault("is_transient", False)
        super().__init__(message, code=code, error_subcode=error_subcode, http_status=http_status, **kwargs)
