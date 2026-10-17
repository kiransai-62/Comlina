# server/app/integrations/instagram/follower_status.py
from enum import Enum
from typing import Tuple
from app.integrations.instagram.client import MetaGraphClient
from app.integrations.instagram.exceptions import MetaRateLimitError, MetaGraphAPIError

class FollowerStatus(str, Enum):
    UNKNOWN = "UNKNOWN"
    FOLLOWING = "FOLLOWING"
    NOT_FOLLOWING = "NOT_FOLLOWING"
    CHECK_UNAVAILABLE = "CHECK_UNAVAILABLE"

class InstagramFollowerService:
    def __init__(self, client: MetaGraphClient):
        self.client = client

    async def check_follower_status(self, business_ig_id: str, commenter_ig_id: str) -> Tuple[FollowerStatus, str]:
        """
        Checks whether the commenter follows the business account.
        Returns (FollowerStatus, reason).
        Never throws unhandled exceptions; returns CHECK_UNAVAILABLE on rate limits or API blocks.
        """
        if not commenter_ig_id or not business_ig_id:
            return FollowerStatus.UNKNOWN, "Missing account IDs"

        try:
            # Query Instagram Graph relationship API
            # GET /vXX.X/{user-id}?fields=is_user_follow_business
            data = await self.client.get(
                f"{business_ig_id}",
                params={"fields": f"follows_business({commenter_ig_id})"}
            )
            is_following = data.get("follows_business", False)
            if is_following:
                return FollowerStatus.FOLLOWING, "Confirmed follower"
            else:
                return FollowerStatus.NOT_FOLLOWING, "Confirmed non-follower"
        except MetaRateLimitError:
            # Safe degradation under Meta API rate pressure
            return FollowerStatus.CHECK_UNAVAILABLE, "Meta Rate Limit Exceeded"
        except MetaGraphAPIError as e:
            # Private profile or Graph permission not granted
            return FollowerStatus.CHECK_UNAVAILABLE, f"Graph API Error: {str(e)}"
        except Exception as e:
            return FollowerStatus.CHECK_UNAVAILABLE, f"Unexpected error: {str(e)}"
