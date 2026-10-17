# worker/app/integrations/instagram/exceptions.py

class MetaGraphAPIError(Exception):
    """Base exception for all Meta Graph API failures."""
    def __init__(self, message: str, code: int = 500, error_subcode: int = 0):
        super().__init__(message)
        self.code = code
        self.error_subcode = error_subcode

class MetaRateLimitError(MetaGraphAPIError):
    """Raised when Meta Graph API returns rate limit code (e.g. 4, 17, 32, 613)."""
    pass

class MetaTokenExpiredError(MetaGraphAPIError):
    """Raised when the access token has expired or user deauthorized app (code 190)."""
    pass

class MetaFollowerCheckUnavailable(MetaGraphAPIError):
    """Raised when follower status check cannot be completed."""
    pass
