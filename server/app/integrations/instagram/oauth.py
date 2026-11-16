import urllib.parse
import httpx
import logging
import hashlib
import hmac
import secrets
import time
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, Optional
from urllib.parse import urlencode

from app.core.config import settings
from app.core.logging import redact_data, redact_string, log_event

logger = logging.getLogger("meta_oauth")

IG_AUTHORIZE_URL = "https://www.instagram.com/oauth/authorize"
IG_TOKEN_URL = "https://api.instagram.com/oauth/access_token"
IG_GRAPH = "https://graph.instagram.com"
IG_SCOPES = "instagram_business_basic,instagram_business_manage_messages,instagram_business_manage_comments,instagram_business_content_publish"

IG_OAUTH_AUTHORIZE_URL = "https://www.instagram.com/oauth/authorize"
IG_SHORT_LIVED_TOKEN_URL = "https://api.instagram.com/oauth/access_token"
IG_GRAPH_URL = "https://graph.instagram.com"

REQUIRED_SCOPES = [
    "instagram_business_basic",
    "instagram_business_manage_messages",
    "instagram_business_manage_comments",
    "instagram_business_content_publish",
]


class MetaOAuthError(Exception):
    """Safe-to-show message."""


class InstagramOAuthService:
    @staticmethod
    def create_signed_state(workspace_id: str, user_id: str) -> str:
        nonce = secrets.token_urlsafe(12)
        ts = str(int(time.time()))
        raw = f"{workspace_id}:{user_id}:{nonce}:{ts}"
        key = (getattr(settings, "SUPABASE_JWT_SECRET", None) or getattr(settings, "JWT_SECRET", None) or getattr(settings, "META_APP_SECRET", None) or "comlina-state-key").encode("utf-8")
        sig = hmac.new(key, raw.encode("utf-8"), hashlib.sha256).hexdigest()
        return f"{raw}:{sig}"

    @staticmethod
    def verify_signed_state(state: str, expected_workspace_id: str, max_age: int = 1800) -> bool:
        try:
            parts = state.split(":")
            if len(parts) == 5:
                ws_id, usr_id, nonce, ts_str, sig = parts
                raw = f"{ws_id}:{usr_id}:{nonce}:{ts_str}"
            elif len(parts) == 4:
                ws_id, nonce, ts_str, sig = parts
                raw = f"{ws_id}:{nonce}:{ts_str}"
            else:
                return False

            if str(ws_id) != str(expected_workspace_id):
                return False
            if abs(time.time() - int(ts_str)) > max_age:
                return False

            key = (getattr(settings, "SUPABASE_JWT_SECRET", None) or getattr(settings, "JWT_SECRET", None) or getattr(settings, "META_APP_SECRET", None) or "comlina-state-key").encode("utf-8")
            expected_sig = hmac.new(key, raw.encode("utf-8"), hashlib.sha256).hexdigest()
            return hmac.compare_digest(sig, expected_sig)
        except Exception:
            return False

    @classmethod
    def build_authorization_url(cls, workspace_id: str, user_id: str) -> str:
        state = cls.create_signed_state(workspace_id, user_id)
        query = urlencode({
            "enable_fb_login": "0",
            "force_authentication": "1",
            "client_id": settings.META_APP_ID,
            "redirect_uri": settings.META_REDIRECT_URI,
            "response_type": "code",
            "scope": ",".join(REQUIRED_SCOPES),
            "state": state,
        })
        return f"{IG_OAUTH_AUTHORIZE_URL}?{query}"

    @classmethod
    async def exchange_code_for_long_lived_token(
        cls,
        code: str,
        correlation_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        clean_code = code.split("#_")[0].strip()
        async with httpx.AsyncClient(timeout=20.0) as client:
            short_resp = await client.post(
                IG_SHORT_LIVED_TOKEN_URL,
                data={
                    "client_id": settings.META_APP_ID,
                    "client_secret": settings.META_APP_SECRET,
                    "grant_type": "authorization_code",
                    "redirect_uri": settings.META_REDIRECT_URI,
                    "code": clean_code,
                },
            )
            if short_resp.status_code != 200:
                err_body = short_resp.json() if short_resp.content else {}
                raise ValueError(
                    err_body.get("error_message")
                    or err_body.get("error", {}).get("message")
                    or f"Instagram code exchange failed with HTTP {short_resp.status_code}"
                )

            short_json = short_resp.json()
            if isinstance(short_json.get("data"), list) and short_json["data"]:
                short_json = short_json["data"][0]

            short_token = short_json.get("access_token")
            scoped_uid = str(short_json.get("user_id") or "")
            permissions = short_json.get("permissions", REQUIRED_SCOPES)
            if isinstance(permissions, str):
                permissions = [p.strip() for p in permissions.split(",") if p.strip()]

            if not short_token:
                raise ValueError("Instagram OAuth did not return an access_token.")

            # Upgrade 1-hour short-lived token to 60-day long-lived token
            ll_resp = await client.get(
                f"{IG_GRAPH_URL}/access_token",
                params={
                    "grant_type": "ig_exchange_token",
                    "client_secret": settings.META_APP_SECRET,
                    "access_token": short_token,
                },
            )
            if ll_resp.status_code == 200:
                ll_data = ll_resp.json()
                final_token = ll_data.get("access_token", short_token)
                expires_in = int(ll_data.get("expires_in", 5184000))
                token_type = "long_lived"
            else:
                final_token = short_token
                expires_in = 3600
                token_type = "short_lived"

            return {
                "access_token": final_token,
                "token_type": token_type,
                "expires_in": expires_in,
                "expires_at": datetime.now(timezone.utc) + timedelta(seconds=expires_in),
                "scoped_user_id": scoped_uid,
                "scopes": permissions,
            }

    @classmethod
    async def refresh_long_lived_token(
        cls,
        access_token: str,
        correlation_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(
                f"{IG_GRAPH_URL}/refresh_access_token",
                params={
                    "grant_type": "ig_refresh_token",
                    "access_token": access_token,
                },
            )
            if resp.status_code != 200:
                err_data = resp.json() if resp.content else {}
                err_code = err_data.get("error", {}).get("code")
                err_msg = err_data.get("error", {}).get("message", f"HTTP {resp.status_code}")
                log_event(
                    logger,
                    "INSTAGRAM_TOKEN_REFRESH",
                    status="FAILED",
                    correlation_id=correlation_id,
                    level=logging.WARNING,
                    error_code=err_code,
                    reason=err_msg,
                )
                raise ValueError(f"Token refresh failed ({err_msg})")

            data = resp.json()
            expires_in = int(data.get("expires_in", 5184000))
            log_event(
                logger,
                "INSTAGRAM_TOKEN_REFRESH",
                status="SUCCESS",
                correlation_id=correlation_id,
                expires_in=expires_in,
            )
            return {
                "access_token": data["access_token"],
                "expires_in": expires_in,
                "expires_at": datetime.now(timezone.utc) + timedelta(seconds=expires_in),
            }

    @classmethod
    async def fetch_and_validate_profile(
        cls,
        access_token: str,
        correlation_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Fetches the user's Instagram profile and validates whether the token is active,
        expired, or revoked (Meta Error Code 190).
        """
        version = getattr(settings, "META_GRAPH_API_VERSION", None) or getattr(settings, "META_API_VERSION", "v21.0")
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(
                f"{IG_GRAPH_URL}/{version}/me",
                params={
                    "fields": "id,user_id,username,name,account_type,profile_picture_url,followers_count",
                    "access_token": access_token,
                },
            )
            if resp.status_code == 200:
                data = resp.json()
                ig_business_id = str(data.get("user_id") or data.get("id"))
                ig_app_scoped_id = str(data.get("id") or ig_business_id)
                log_event(
                    logger,
                    "INSTAGRAM_TOKEN_VALIDATION",
                    status="VALID",
                    correlation_id=correlation_id,
                    ig_user_id=ig_business_id,
                    username=data.get("username"),
                )
                return {
                    "valid": True,
                    "revoked": False,
                    "ig_user_id": ig_business_id,
                    "ig_business_account_id": ig_app_scoped_id,
                    "username": data.get("username") or f"ig_{ig_business_id}",
                    "account_type": data.get("account_type") or "BUSINESS",
                    "profile_picture_url": data.get("profile_picture_url"),
                    "followers_count": int(data.get("followers_count") or 0),
                }

            err_payload = resp.json() if resp.content else {}
            error_obj = err_payload.get("error", {})
            error_code = error_obj.get("code")
            error_message = error_obj.get("message") or f"HTTP {resp.status_code}"
            is_revoked = error_code in (190, 102, 10) or resp.status_code in (401, 403)

            log_event(
                logger,
                "INSTAGRAM_TOKEN_VALIDATION",
                status="REVOKED" if is_revoked else "TRANSIENT_ERROR",
                correlation_id=correlation_id,
                level=logging.WARNING,
                error_code=error_code,
                reason=error_message,
            )
            return {
                "valid": False,
                "revoked": is_revoked,
                "error_code": error_code,
                "error_message": error_message,
            }

    @classmethod
    async def subscribe_webhooks(cls, ig_account_id: str, access_token: str) -> bool:
        version = getattr(settings, "META_GRAPH_API_VERSION", None) or getattr(settings, "META_API_VERSION", "v21.0")
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(
                f"{IG_GRAPH_URL}/{version}/{ig_account_id}/subscribed_apps",
                params={
                    "subscribed_fields": "comments,messages,messaging_postbacks",
                    "access_token": access_token,
                },
            )
            return resp.status_code == 200 and bool(resp.json().get("success"))


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

                if resp.status_code == 200 and isinstance(body, dict) and "error" not in body and (body.get("success") is True or "data" in body):
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


async def subscribe_app_to_account(ig_user_id: str, access_token: str) -> bool:
    """Verifies the exact 'success' boolean rather than ignoring the response."""
    async with httpx.AsyncClient(timeout=15.0) as client:
        res = await client.post(
            f"https://graph.facebook.com/v19.0/{ig_user_id}/subscribed_apps",
            params={"subscribed_fields": "comments,messages", "access_token": access_token}
        )
        try:
            data = res.json()
            return data.get("success") is True
        except Exception:
            return False


