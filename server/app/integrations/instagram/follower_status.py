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
        Never throws unhandled exceptions.
        Guarantees distinct states:
        - FOLLOWING: Meta confirmed is_user_follow_business is True.
        - NOT_FOLLOWING: Meta confirmed is_user_follow_business is False.
        - CHECK_UNAVAILABLE: Meta rate limit, missing messaging consent on comment, API block, or omitted field.
        - UNKNOWN: Missing account IDs or unresolvable identity.
        Never treats an unavailable or omitted status as proof of following or not following.
        """
        if not commenter_ig_id or not business_ig_id:
            return FollowerStatus.UNKNOWN, "Missing account IDs"

        try:
            # Query official Meta Instagram Graph API
            # GET /vXX.X/{user-id}?fields=is_user_follow_business
            # Note: Meta requires active messaging consent to read is_user_follow_business on IGSID
            data = await self.client.get(
                f"{commenter_ig_id}",
                params={"fields": "is_user_follow_business"}
            )
            if not isinstance(data, dict):
                return FollowerStatus.CHECK_UNAVAILABLE, "Invalid response format from Meta Graph API"

            if "is_user_follow_business" not in data or data.get("is_user_follow_business") is None:
                # Meta returned user data but omitted follower status field
                # (e.g. comment-only user without messaging consent or permission not granted)
                return FollowerStatus.CHECK_UNAVAILABLE, "Meta did not return follower status field (messaging consent or permission required)"

            is_following = data["is_user_follow_business"]
            if is_following is True:
                return FollowerStatus.FOLLOWING, "Confirmed follower via Meta Graph API"
            elif is_following is False:
                return FollowerStatus.NOT_FOLLOWING, "Confirmed non-follower via Meta Graph API"
            else:
                return FollowerStatus.CHECK_UNAVAILABLE, "Meta returned non-boolean follower status"
        except MetaRateLimitError:
            # Safe degradation under Meta API rate pressure
            return FollowerStatus.CHECK_UNAVAILABLE, "Meta Rate Limit Exceeded"
        except MetaGraphAPIError as e:
            # Missing messaging consent (comment-only user) or permission not granted
            return FollowerStatus.CHECK_UNAVAILABLE, f"Graph API Error (messaging consent required): {str(e)}"
        except Exception as e:
            return FollowerStatus.CHECK_UNAVAILABLE, f"Unexpected error checking follower status: {str(e)}"


