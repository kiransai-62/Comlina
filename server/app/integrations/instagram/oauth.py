import urllib.parse
import httpx
import logging
from typing import Dict, Any, Optional
from app.core.config import settings
from app.core.logging import redact_data, redact_string

logger = logging.getLogger("meta_oauth")

IG_AUTHORIZE_URL = "https://www.instagram.com/oauth/authorize"
IG_TOKEN_URL = "https://api.instagram.com/oauth/access_token"
IG_GRAPH = "https://graph.instagram.com"
IG_SCOPES = "instagram_business_basic,instagram_business_manage_messages,instagram_business_manage_comments,instagram_business_content_publish"


class MetaOAuthError(Exception):
    """Safe-to-show message."""


def _error_message(data: Any, fallback: str) -> str:
    msg = fallback
    if isinstance(data, dict):
        err = data.get("error")
        if isinstance(err, dict) and err.get("message"):
            msg = str(err["message"])
        elif data.get("error_message"):
            msg = str(data["error_message"])
    return redact_string(msg)


async def _get(url: str, params: dict, fail_msg: str) -> Dict[str, Any]:
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(url, params=params)
            body = resp.json()
    except Exception as e:
        raise MetaOAuthError("Could not reach Instagram.") from e
    if resp.status_code != 200 or not isinstance(body, dict) or "error" in body:
        logger.warning("[OAUTH] %s: %s", fail_msg, redact_data(body))
        raise MetaOAuthError(_error_message(body, fail_msg))
    return body


class MetaOAuth:
    @staticmethod
    def get_authorization_url(state: str, redirect_uri: Optional[str] = None) -> str:
        params = {
            "client_id": settings.META_APP_ID,
            "redirect_uri": redirect_uri or settings.META_REDIRECT_URI,
            "scope": IG_SCOPES,
            "response_type": "code",
            "state": state,
        }
        return IG_AUTHORIZE_URL + "?" + urllib.parse.urlencode(params)

    @staticmethod
    async def exchange_code_for_token(code: str, redirect_uri: Optional[str] = None) -> Dict[str, Any]:
        data = {
            "client_id": settings.META_APP_ID,
            "client_secret": settings.META_APP_SECRET,
            "grant_type": "authorization_code",
            "redirect_uri": redirect_uri or settings.META_REDIRECT_URI,
            "code": code,
        }
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.post(IG_TOKEN_URL, data=data)
                body = resp.json()
        except Exception as e:
            raise MetaOAuthError("Could not reach Instagram to complete login.") from e
        if isinstance(body, dict) and isinstance(body.get("data"), list) and body["data"]:
            body = body["data"][0]          # some versions wrap the payload
        if resp.status_code != 200 or "access_token" not in body:
            logger.warning("[OAUTH] code exchange rejected: %s", redact_data(body))
            raise MetaOAuthError(_error_message(body, "Instagram rejected the authorization code."))
        return body

    @staticmethod
    async def exchange_for_long_lived_token(short_lived_token: str) -> Dict[str, Any]:
        body = await _get(f"{IG_GRAPH}/access_token", {
            "grant_type": "ig_exchange_token",
            "client_secret": settings.META_APP_SECRET,
            "access_token": short_lived_token,
        }, "Instagram refused the long-lived token exchange.")
        if "access_token" not in body:
            raise MetaOAuthError("Instagram returned no long-lived token.")
        return body

    @staticmethod
    async def refresh_long_lived_token(long_lived_token: str) -> Dict[str, Any]:
        body = await _get(f"{IG_GRAPH}/refresh_access_token", {
            "grant_type": "ig_refresh_token",
            "access_token": long_lived_token,
        }, "Instagram refused the token refresh.")
        if "access_token" not in body:
            raise MetaOAuthError("Instagram returned no refreshed token.")
        return body

    @staticmethod
    async def fetch_instagram_profile(access_token: str) -> Dict[str, Any]:
        body = await _get(f"{IG_GRAPH}/{settings.META_GRAPH_API_VERSION}/me", {
            "access_token": access_token,
            "fields": "id,user_id,username,name,account_type,profile_picture_url,followers_count,media_count",
        }, "Could not read the Instagram account profile.")
        if not (body.get("user_id") or body.get("id")):
            raise MetaOAuthError("Instagram returned no account id.")
        return body

    @staticmethod
    def parse_subscription_meta_error(body: Any, status_code: int = 400) -> Dict[str, Any]:
        """
        Classifies Meta Graph API subscription errors into safe, structured status values:
        - TOKEN_EXPIRED: code 190 or expired session (requires user reconnect)
        - PERMISSION_DENIED: code 10, 200, or missing permissions (requires user reconnect)
        - RATE_LIMITED: code 4, 17, 32 (transient, retryable without reconnect)
        - META_ERROR: code 1, 2, HTTP 5xx, or network failure (transient, retryable without reconnect)
        Never exposes access tokens or raw traces.
        """
        err_msg = ""
        err_code = None
        err_subcode = None

        if isinstance(body, dict):
            err = body.get("error")
            if isinstance(err, dict):
                err_msg = str(err.get("message") or "")
                err_code = err.get("code")
                err_subcode = err.get("error_subcode")
            elif body.get("error_message"):
                err_msg = str(body["error_message"])
            elif body.get("error"):
                err_msg = str(body["error"])

        err_msg_lower = err_msg.lower()

        # 1. Expired / Revoked Token
        if err_code == 190 or any(w in err_msg_lower for w in ["expired", "revoked", "invalid token", "session has expired"]):
            return {
                "success": False,
                "is_subscribed": False,
                "subscribed_fields": [],
                "status": "TOKEN_EXPIRED",
                "requires_reconnect": True,
                "can_retry": False,
                "error_code": "TOKEN_EXPIRED",
                "error_message": "Instagram access token has expired or was revoked. Please reconnect your account.",
                "meta_code": err_code,
                "meta_subcode": err_subcode,
            }

        # 2. Permission Denied
        if err_code in (10, 200) or any(w in err_msg_lower for w in ["permission", "manage_comments", "manage_messages", "scope"]):
            return {
                "success": False,
                "is_subscribed": False,
                "subscribed_fields": [],
                "status": "PERMISSION_DENIED",
                "requires_reconnect": True,
                "can_retry": False,
                "error_code": "PERMISSION_DENIED",
                "error_message": "Meta denied subscription due to missing permissions. Please reconnect your account and grant all required permissions.",
                "meta_code": err_code,
                "meta_subcode": err_subcode,
            }

        # 3. Rate Limited
        if err_code in (4, 17, 32) or any(w in err_msg_lower for w in ["rate limit", "request limit", "too many calls", "user request limit"]):
            return {
                "success": False,
                "is_subscribed": False,
                "subscribed_fields": [],
                "status": "RATE_LIMITED",
                "requires_reconnect": False,
                "can_retry": True,
                "error_code": "RATE_LIMITED",
                "error_message": "Meta API rate limit reached. Please wait a few moments before retrying.",
                "meta_code": err_code,
            }

        # 4. Meta Service Outage / Transient Server Error
        if status_code >= 500 or err_code in (1, 2) or "temporarily unavailable" in err_msg_lower:
            return {
                "success": False,
                "is_subscribed": False,
                "subscribed_fields": [],
                "status": "META_ERROR",
                "requires_reconnect": False,
                "can_retry": True,
                "error_code": "META_SERVICE_UNAVAILABLE",
                "error_message": "Meta Graph API is temporarily unavailable. Please retry in a few minutes.",
                "meta_code": err_code,
            }

        # Generic / Unknown Meta Error
        return {
            "success": False,
            "is_subscribed": False,
            "subscribed_fields": [],
            "status": "META_ERROR",
            "requires_reconnect": False,
            "can_retry": True,
            "error_code": "SUBSCRIPTION_REQUEST_FAILED",
            "error_message": err_msg or "Failed to communicate with Meta Graph API for webhook subscription.",
            "meta_code": err_code,
        }

    @staticmethod
    async def check_app_subscription(access_token: str, ig_user_id: str) -> Dict[str, Any]:
        """
        Inspects account-level webhook subscription via GET /{ig_user_id}/subscribed_apps.
        Returns structured verification status distinguishing ACTIVE, NOT_SUBSCRIBED,
        TOKEN_EXPIRED, PERMISSION_DENIED, RATE_LIMITED, and META_ERROR.
        """
        url = f"{IG_GRAPH}/{settings.META_GRAPH_API_VERSION}/{ig_user_id}/subscribed_apps"
        params = {"access_token": access_token}
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.get(url, params=params)
                try:
                    body = resp.json()
                except Exception:
                    body = {"error": {"message": redact_string(resp.text[:300] if resp.text else "")}}

                if resp.status_code == 200 and isinstance(body, dict) and "error" not in body:
                    data = body.get("data", [])
                    if isinstance(data, list) and len(data) > 0:
                        all_fields = set()
                        for entry in data:
                            if isinstance(entry, dict):
                                fields = entry.get("subscribed_fields", [])
                                if isinstance(fields, list):
                                    all_fields.update(fields)
                                elif isinstance(fields, str):
                                    all_fields.update([f.strip() for f in fields.split(",") if f.strip()])
                        fields_list = sorted(list(all_fields)) or ["comments", "messages"]
                        return {
                            "success": True,
                            "is_subscribed": True,
                            "subscribed_fields": fields_list,
                            "status": "SUBSCRIBED",
                            "requires_reconnect": False,
                            "can_retry": True,
                            "raw_data": data,
                        }
                    else:
                        # Empty list: App is not subscribed to this account's webhooks
                        return {
                            "success": True,
                            "is_subscribed": False,
                            "subscribed_fields": [],
                            "status": "NOT_SUBSCRIBED",
                            "requires_reconnect": False,
                            "can_retry": True,
                        }

                return MetaOAuth.parse_subscription_meta_error(body, status_code=resp.status_code)
        except Exception as e:
            logger.warning(f"[OAUTH] Failed to check app subscription for account {ig_user_id}: {e}")
            return {
                "success": False,
                "is_subscribed": False,
                "subscribed_fields": [],
                "status": "META_ERROR",
                "requires_reconnect": False,
                "can_retry": True,
                "error_code": "NETWORK_ERROR",
                "error_message": f"Network error connecting to Meta: {str(e)}",
            }

    @staticmethod
    async def subscribe_app_to_account(access_token: str, ig_user_id: str, fields: str = "comments,messages") -> Dict[str, Any]:
        """
        Subscribes the Meta app to receive real-time webhooks (comments, messages) for the Instagram account.
        Calls POST https://graph.instagram.com/{META_GRAPH_API_VERSION}/{ig_user_id}/subscribed_apps
        with subscribed_fields=comments,messages.
        Returns structured verification status and retains {"success": True} for backward compatibility.
        """
        url = f"{IG_GRAPH}/{settings.META_GRAPH_API_VERSION}/{ig_user_id}/subscribed_apps"
        params = {
            "subscribed_fields": fields,
            "access_token": access_token,
        }
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.post(url, params=params)
                try:
                    body = resp.json()
                except Exception:
                    body = {"error": {"message": redact_string(resp.text[:300] if resp.text else "")}}

                if resp.status_code == 200 and isinstance(body, dict) and "error" not in body:
                    fields_list = [f.strip() for f in fields.split(",") if f.strip()]
                    logger.info(f"[OAUTH] Successfully subscribed app to account {ig_user_id}: status={resp.status_code} body={redact_data(body)}")
                    return {
                        "success": True,
                        "is_subscribed": True,
                        "subscribed_fields": fields_list,
                        "status": "SUBSCRIBED",
                        "requires_reconnect": False,
                        "can_retry": True,
                        "raw_data": body,
                    }

                err_res = MetaOAuth.parse_subscription_meta_error(body, status_code=resp.status_code)
                logger.warning(f"[OAUTH] Meta rejected subscribed_apps for account {ig_user_id}: {err_res}")
                return err_res
        except Exception as e:
            logger.warning(f"[OAUTH] Exception subscribing app to account {ig_user_id}: {e}")
            return {
                "success": False,
                "is_subscribed": False,
                "subscribed_fields": [],
                "status": "META_ERROR",
                "requires_reconnect": False,
                "can_retry": True,
                "error_code": "NETWORK_ERROR",
                "error_message": f"Network error connecting to Meta: {str(e)}",
            }

    fetch_profile = fetch_instagram_profile

