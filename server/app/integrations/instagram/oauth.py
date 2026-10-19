import urllib.parse
import httpx
import logging
from typing import Dict, Any, Optional
from app.core.config import settings

logger = logging.getLogger("meta_oauth")

IG_AUTHORIZE_URL = "https://www.instagram.com/oauth/authorize"
IG_TOKEN_URL = "https://api.instagram.com/oauth/access_token"
IG_GRAPH = "https://graph.instagram.com"
IG_SCOPES = "instagram_business_basic,instagram_business_manage_messages,instagram_business_manage_comments,instagram_business_content_publish"


class MetaOAuthError(Exception):
    """Safe-to-show message."""


def _error_message(data: Any, fallback: str) -> str:
    if isinstance(data, dict):
        err = data.get("error")
        if isinstance(err, dict) and err.get("message"):
            return str(err["message"])
        if data.get("error_message"):
            return str(data["error_message"])
    return fallback


async def _get(url: str, params: dict, fail_msg: str) -> Dict[str, Any]:
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(url, params=params)
            body = resp.json()
    except Exception as e:
        raise MetaOAuthError("Could not reach Instagram.") from e
    if resp.status_code != 200 or not isinstance(body, dict) or "error" in body:
        logger.warning("[OAUTH] %s: %s", fail_msg, body)
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
            logger.warning("[OAUTH] code exchange rejected: %s", body)
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
    async def subscribe_app_to_account(access_token: str, ig_user_id: str) -> Dict[str, Any]:
        """
        Subscribes the Meta app to receive real-time webhooks (comments, messages) for the Instagram account.
        Calls POST https://graph.instagram.com/{META_GRAPH_API_VERSION}/{ig_user_id}/subscribed_apps
        with subscribed_fields=comments,messages.
        """
        url = f"{IG_GRAPH}/{settings.META_GRAPH_API_VERSION}/{ig_user_id}/subscribed_apps"
        params = {
            "subscribed_fields": "comments,messages",
            "access_token": access_token,
        }
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.post(url, params=params)
                body = resp.json()
                logger.info(f"[OAUTH] Subscribed app to account {ig_user_id}: status={resp.status_code} body={body}")
                return body
        except Exception as e:
            logger.warning(f"[OAUTH] Failed to subscribe app to account {ig_user_id}: {e}")
            return {"success": False, "error": str(e)}

    fetch_profile = fetch_instagram_profile
