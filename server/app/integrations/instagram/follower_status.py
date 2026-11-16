# server/app/integrations/instagram/follower_status.py
from enum import Enum
import logging
from typing import Any, Dict, Optional, Tuple
import httpx
from app.core.config import settings
from app.core.logging import log_event
from app.integrations.instagram.client import MetaGraphClient
from app.integrations.instagram.exceptions import MetaRateLimitError, MetaGraphAPIError

logger = logging.getLogger(__name__)

class FollowerStatus(str, Enum):
    UNKNOWN = "UNKNOWN"
    FOLLOWING = "FOLLOWING"
    NOT_FOLLOWING = "NOT_FOLLOWING"
    CHECK_UNAVAILABLE = "CHECK_UNAVAILABLE"


class FollowerStatusService:
    @staticmethod
    async def check_follower_status(
        commenter_ig_id: str,
        access_token: str,
        correlation_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        if not commenter_ig_id or not access_token:
            res = {
                "status": "CHECK_UNAVAILABLE",
                "is_following": False,
                "limitation": "Missing commenter ID or access token.",
            }
            log_event(logger, "FOLLOW_CONDITION_RESULT", correlation_id=correlation_id, **res)
            return res

        version = getattr(settings, "META_GRAPH_API_VERSION", None) or getattr(settings, "META_API_VERSION", "v21.0")
        url = f"https://graph.instagram.com/{version}/{commenter_ig_id}"
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(
                    url,
                    params={
                        "fields": "name,username,is_user_follow_business,is_business_follow_user",
                        "access_token": access_token,
                    },
                )
                if resp.status_code == 200:
                    data = resp.json()
                    if "is_user_follow_business" in data and data["is_user_follow_business"] is not None:
                        is_following = bool(data["is_user_follow_business"])
                        res = {
                            "status": "FOLLOWING" if is_following else "NOT_FOLLOWING",
                            "is_following": is_following,
                            "limitation": None,
                        }
                        log_event(logger, "FOLLOW_CONDITION_RESULT", correlation_id=correlation_id, **res)
                        return res

                    res = {
                        "status": "CHECK_UNAVAILABLE",
                        "is_following": False,
                        "limitation": (
                            "Meta Graph API did not return 'is_user_follow_business' for this comment sender ID. "
                            "Meta restricts profile relationship fields until a messaging conversation is established "
                            "or requires Advanced Access for instagram_business_manage_messages."
                        ),
                    }
                    log_event(logger, "FOLLOW_CONDITION_RESULT", correlation_id=correlation_id, **res)
                    return res

                err_data = resp.json() if resp.content else {}
                err_msg = err_data.get("error", {}).get("message") or f"HTTP {resp.status_code}"
                res = {
                    "status": "CHECK_UNAVAILABLE",
                    "is_following": False,
                    "limitation": f"Meta Graph API follower lookup unavailable: {err_msg}",
                }
                log_event(
                    logger,
                    "FOLLOW_CONDITION_RESULT",
                    correlation_id=correlation_id,
                    level=logging.WARNING,
                    **res,
                )
                return res
        except Exception as exc:
            res = {
                "status": "UNKNOWN",
                "is_following": False,
                "limitation": f"Follower check network error: {exc}",
            }
            log_event(
                logger,
                "FOLLOW_CONDITION_RESULT",
                correlation_id=correlation_id,
                level=logging.ERROR,
                **res,
            )
            return res


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
            detail = f"code={e.code}" if getattr(e, "code", None) is not None else "permission/consent required"
            return FollowerStatus.CHECK_UNAVAILABLE, f"Graph API Error (messaging consent required): {detail}"
        except Exception:
            return FollowerStatus.CHECK_UNAVAILABLE, "Unexpected error checking follower status"


