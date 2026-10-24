from typing import TYPE_CHECKING
from .client import MetaGraphClient
from .oauth import MetaOAuth
from .messaging import InstagramMessaging
from .comments import InstagramComments
from .follower_status import InstagramFollowerService, FollowerStatus
from .exceptions import (
    MetaGraphAPIError, MetaRateLimitError, MetaTokenExpiredError, MetaFollowerCheckUnavailable
)

if TYPE_CHECKING:
    from .webhooks import InstagramWebhookParser

def __getattr__(name: str):
    if name == "InstagramWebhookParser":
        from .webhooks import InstagramWebhookParser
        return InstagramWebhookParser
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

__all__ = [
    "MetaGraphClient",
    "MetaOAuth",
    "InstagramWebhookParser",
    "InstagramMessaging",
    "InstagramComments",
    "InstagramFollowerService",
    "FollowerStatus",
    "MetaGraphAPIError",
    "MetaRateLimitError",
    "MetaTokenExpiredError",
    "MetaFollowerCheckUnavailable"
]

