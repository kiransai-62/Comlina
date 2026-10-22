# server/app/api/instagram.py
import os
import uuid
import httpx
import logging
import secrets
import hashlib
import hmac
import time
from urllib.parse import urlparse
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.core.database import get_db
from app.core.config import settings
from app.api.deps import get_current_workspace, require_workspace_owner, get_current_user
from app.models import Workspace, InstagramAccount, Automation, User, WorkspaceMember
from app.schemas import (
    InstagramAccountOut,
    ConnectAccountRequest,
    InstagramMediaPage,
    InstagramConnectionStatusResponse,
    InstagramAccountSummary,
    WebhookSubscriptionStatusOut,
)
from app.integrations.instagram.oauth import MetaOAuth, MetaOAuthError
from app.integrations.instagram.client import MetaGraphClient
from app.integrations.instagram.exceptions import MetaGraphAPIError, MetaTokenExpiredError, MetaRateLimitError
from app.core.encryption import encrypt_token, decrypt_token
from app.core.replay_cache import replay_cache

logger = logging.getLogger("instagram_api")
router = APIRouter(prefix="/instagram", tags=["Instagram"])

def _determine_account_status(account: InstagramAccount) -> str:
    now = datetime.now(timezone.utc)
    if not account.is_active or account.connection_status == "REAUTHORIZATION_REQUIRED":
        return "REAUTHORIZATION_REQUIRED"
    try:
        token = decrypt_token(account.access_token_encrypted)
        if not token:
            return "REAUTHORIZATION_REQUIRED"
    except Exception:
        return "REAUTHORIZATION_REQUIRED"

    if account.token_expires_at:
        exp = account.token_expires_at
        if exp.tzinfo is None:
            exp = exp.replace(tzinfo=timezone.utc)
        if exp <= now:
            return "EXPIRED"
        elif exp <= now + timedelta(days=7):
            return "EXPIRING_SOON"
    return "CONNECTED"

@router.get("/connection-status", response_model=InstagramConnectionStatusResponse)
async def get_instagram_connection_status(
    user: User = Depends(get_current_user),
    workspace: Workspace = Depends(get_current_workspace),
    db: AsyncSession = Depends(get_db)
):
    """
    Authoritative connection status endpoint.
    Retrieves the current workspace and user Instagram connection state.
    Returns safe metadata only. Never exposes access tokens.
    Possible states: connected | not_connected | token_expiring | reauthorization_required | temporarily_unavailable
    """
    try:
        stmt = (
            select(InstagramAccount)
            .where(_get_owner_filter(workspace, user))
            .order_by(InstagramAccount.updated_at.desc(), InstagramAccount.connected_at.desc())
        )
        res = await db.execute(stmt)
        accounts = list(res.scalars().all())
        account = accounts[0] if accounts else None

        if not account:
            return InstagramConnectionStatusResponse(
                status="not_connected",
                account=None,
                requires_reconnect=False,
                requires_connect=True,
                error_code=None,
                message="No Instagram account is connected to this workspace."
            )

        account_summary = InstagramAccountSummary(
            id=account.id,
            workspace_id=account.workspace_id,
            user_id=account.user_id,
            ig_user_id=account.ig_user_id,
            username=account.username,
            account_type=account.account_type,
            follower_count=account.follower_count,
            profile_pic_url=account.profile_pic_url,
            token_expires_at=account.token_expires_at,
            connected_at=account.connected_at,
            last_validated_at=account.last_validated_at,
            last_refreshed_at=account.last_refreshed_at,
        )

        # 1. Check if explicitly inactive or reauth required
        if not account.is_active or account.connection_status == "REAUTHORIZATION_REQUIRED":
            return InstagramConnectionStatusResponse(
                status="reauthorization_required",
                account=account_summary,
                requires_reconnect=True,
                requires_connect=False,
                error_code=account.last_error_code or "PERMISSIONS_REVOKED",
                message=f"Instagram authorization for @{account.username} has been revoked or expired. Please reconnect."
            )

        # 2. Check token decryptability
        try:
            token = decrypt_token(account.access_token_encrypted)
            if not token:
                return InstagramConnectionStatusResponse(
                    status="reauthorization_required",
                    account=account_summary,
                    requires_reconnect=True,
                    requires_connect=False,
                    error_code="TOKEN_CORRUPT",
                    message="Stored credentials cannot be verified. Reconnection required."
                )
        except Exception:
            return InstagramConnectionStatusResponse(
                status="reauthorization_required",
                account=account_summary,
                requires_reconnect=True,
                requires_connect=False,
                error_code="DECRYPTION_FAILED",
                message="Stored access credentials cannot be decrypted. Reconnection required."
            )

        # 3. Check expiration
        now = datetime.now(timezone.utc)
        if account.token_expires_at:
            exp = account.token_expires_at
            if exp.tzinfo is None:
                exp = exp.replace(tzinfo=timezone.utc)
            if exp <= now:
                return InstagramConnectionStatusResponse(
                    status="reauthorization_required",
                    account=account_summary,
                    requires_reconnect=True,
                    requires_connect=False,
                    error_code="TOKEN_EXPIRED",
                    message=f"Instagram access token for @{account.username} has expired. Please reconnect."
                )
            elif exp <= now + timedelta(days=7):
                days_left = max(1, (exp - now).days)
                return InstagramConnectionStatusResponse(
                    status="token_expiring",
                    account=account_summary,
                    requires_reconnect=False,
                    requires_connect=False,
                    error_code=None,
                    message=f"Token expires in {days_left} days and will be refreshed automatically."
                )

        return InstagramConnectionStatusResponse(
            status="connected",
            account=account_summary,
            requires_reconnect=False,
            requires_connect=False,
            error_code=None,
            message=f"Connected as @{account.username}."
        )

    except Exception as e:
        logger.error(f"[INSTAGRAM] Error checking connection status: {e}")
        return InstagramConnectionStatusResponse(
            status="temporarily_unavailable",
            account=None,
            requires_reconnect=False,
            requires_connect=False,
            error_code="SERVICE_UNAVAILABLE",
            message="Connection verification is temporarily unavailable. Retrying..."
        )

def _get_owner_filter(workspace: Workspace, user: Any):
    return (InstagramAccount.workspace_id == workspace.id)

@router.get("/accounts", response_model=List[InstagramAccountOut])
async def list_instagram_accounts(
    user: User = Depends(get_current_user),
    workspace: Workspace = Depends(get_current_workspace),
    db: AsyncSession = Depends(get_db)
):
    stmt = (
        select(InstagramAccount)
        .where(_get_owner_filter(workspace, user))
        .order_by(InstagramAccount.updated_at.desc(), InstagramAccount.connected_at.desc())
    )
    res = await db.execute(stmt)
    raw_accounts = list(res.scalars().all())

    out = []
    for acc in raw_accounts:
        acc_dict = {
            "id": acc.id,
            "workspace_id": acc.workspace_id,
            "user_id": acc.user_id,
            "ig_user_id": acc.ig_user_id,
            "username": acc.username,
            "account_type": acc.account_type,
            "follower_count": acc.follower_count,
            "profile_pic_url": acc.profile_pic_url,
            "token_expires_at": acc.token_expires_at,
            "is_active": acc.is_active,
            "auth_method": getattr(acc, "auth_method", "META_INSTAGRAM_OAUTH"),
            "connection_status": getattr(acc, "connection_status", "CONNECTED"),
            "last_validated_at": getattr(acc, "last_validated_at", None),
            "last_refreshed_at": getattr(acc, "last_refreshed_at", None),
            "last_error_code": getattr(acc, "last_error_code", None),
            "connected_at": acc.connected_at,
            "status": _determine_account_status(acc),
        }
        out.append(InstagramAccountOut(**acc_dict))
    return out

def _normalize_media_item(item: Dict[str, Any]) -> Dict[str, Any]:
    raw_media_type = item.get("media_type") or "IMAGE"
    media_product_type = item.get("media_product_type") or ""
    if raw_media_type == "VIDEO" or (media_product_type and media_product_type.upper() == "REELS"):
        m_type = "REEL"
    else:
        m_type = "POST"
    image_url = item.get("thumbnail_url") or item.get("media_url") or ""

    # Real engagement metrics: None if missing, int if present (never fake)
    likes = int(item["like_count"]) if item.get("like_count") is not None else None
    comments = int(item["comments_count"]) if item.get("comments_count") is not None else None

    return {
        "id": str(item.get("id", "")),
        "type": m_type,
        "rawMediaType": raw_media_type,
        "mediaProductType": media_product_type,
        "caption": item.get("caption") if item.get("caption") is not None else "",
        "imageUrl": image_url,
        "commentsCount": comments,
        "likesCount": likes,
        "publishedDate": str(item.get("timestamp") or ""),
        "permalink": item.get("permalink") or ""
    }

@router.get("/media")
@router.get("/accounts/{account_id}/media")
async def list_instagram_media(
    account_id: Optional[uuid.UUID] = None,
    limit: int = Query(24, ge=1, le=50),
    after: Optional[str] = Query(None),
    format: Optional[str] = Query(None),
    user: User = Depends(get_current_user),
    workspace: Workspace = Depends(get_current_workspace),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(InstagramAccount).where(
        _get_owner_filter(workspace, user),
        InstagramAccount.is_active == True  # noqa: E712
    )
    if account_id:
        stmt = stmt.where(InstagramAccount.id == account_id)
    stmt = stmt.order_by(InstagramAccount.updated_at.desc(), InstagramAccount.connected_at.desc())
    account = (await db.execute(stmt)).scalars().first()
    if not account:
        raise HTTPException(status_code=404, detail="No connected Instagram account found.")
    try:
        token = decrypt_token(account.access_token_encrypted)
    except Exception:
        raise HTTPException(status_code=409, detail="Stored token is unreadable. Reconnect your Instagram account.")

    if not token or token.startswith("mock_"):
        if format == "list":
            return []
        return {"data": [], "next_cursor": None, "paging": {}}

    params: Dict[str, Any] = {
        "fields": "id,caption,media_type,media_product_type,media_url,thumbnail_url,permalink,timestamp,like_count,comments_count",
        "limit": limit
    }
    if after:
        params["after"] = after

    # Official Meta Instagram Graph API endpoint:
    endpoint = "me/media"

    try:
        raw = await MetaGraphClient(token).get(endpoint, params=params)
    except MetaTokenExpiredError:
        # Before revoking credentials or setting REAUTHORIZATION_REQUIRED in DB,
        # perform a lightweight sanity check with fetch_instagram_profile
        # to ensure the token is truly dead, rather than an endpoint routing anomaly.
        is_token_alive = False
        try:
            profile = await MetaOAuth.fetch_instagram_profile(token)
            if profile.get("id") or profile.get("user_id"):
                is_token_alive = True
        except Exception:
            is_token_alive = False

        if not is_token_alive:
            account.connection_status = "REAUTHORIZATION_REQUIRED"
            account.last_error_code = "TOKEN_EXPIRED"
            await db.commit()
            raise HTTPException(status_code=409, detail="Instagram token expired or revoked. Please reconnect the account.")
        else:
            logger.warning("Media fetch returned code 190, but profile check verified token is active. Preserving connection status.")
            raise HTTPException(status_code=502, detail="Instagram media service is temporarily unavailable. Please retry.")
    except MetaRateLimitError:
        raise HTTPException(status_code=429, detail="Instagram rate limit reached. Try again shortly.")
    except MetaGraphAPIError as e:
        logger.warning(f"Failed to fetch media from Meta endpoint {endpoint}: {e}")
        raise HTTPException(status_code=400, detail=f"Instagram media fetch failed: {e}")

    raw_items = raw.get("data", []) if isinstance(raw, dict) else []
    paging = raw.get("paging", {}) if isinstance(raw, dict) else {}
    cursors = paging.get("cursors", {}) if isinstance(paging, dict) else {}
    next_cursor = cursors.get("after") if isinstance(cursors, dict) else None

    # Deduplicate media by actual media ID
    seen_ids = set()
    normalized_items = []
    for m in raw_items:
        mid = str(m.get("id", ""))
        if mid and mid not in seen_ids:
            seen_ids.add(mid)
            normalized_items.append(_normalize_media_item(m))

    if format == "list":
        return normalized_items

    return {
        "data": normalized_items,
        "next_cursor": next_cursor,
        "paging": paging
    }

def _is_allowed_redirect_uri(redirect_uri: Optional[str]) -> bool:
    if not redirect_uri:
        return True
    try:
        parsed = urlparse(redirect_uri)
        if not parsed.scheme or not parsed.netloc:
            return False

        scheme = parsed.scheme.lower()
        if scheme not in ("http", "https"):
            return False

        # Reject any credentials in URI authority (e.g. user:pass@host or host@attacker.com)
        if parsed.username or parsed.password or "@" in parsed.netloc:
            return False

        host = (parsed.hostname or "").lower()
        if not host:
            return False

        is_prod = (settings.ENVIRONMENT == "production")

        # In production, scheme MUST be https
        if is_prod and scheme != "https":
            return False

        # Canonical production domains
        allowed_hosts = {
            "app.comlina.ai",
            "comlina.ai",
            "www.comlina.ai",
            "app.comlina.com",
            "comlina.com",
            "www.comlina.com",
        }

        # Add host from configured META_REDIRECT_URI
        if settings.META_REDIRECT_URI:
            meta_parsed = urlparse(settings.META_REDIRECT_URI)
            if meta_parsed.hostname:
                allowed_hosts.add(meta_parsed.hostname.lower())

        # Add hosts from configured ALLOWED_ORIGINS
        if settings.ALLOWED_ORIGINS:
            origins = settings.ALLOWED_ORIGINS if isinstance(settings.ALLOWED_ORIGINS, list) else settings.ALLOWED_ORIGINS.split(",")
            for orig in origins:
                orig_clean = orig.strip()
                if orig_clean:
                    parsed_orig = urlparse(orig_clean)
                    if parsed_orig.hostname:
                        allowed_hosts.add(parsed_orig.hostname.lower())

        # Add hosts from CORS_ORIGINS
        if settings.CORS_ORIGINS:
            cors_list = settings.CORS_ORIGINS if isinstance(settings.CORS_ORIGINS, list) else settings.CORS_ORIGINS.split(",")
            for cor in cors_list:
                cor_clean = cor.strip()
                if cor_clean:
                    parsed_cor = urlparse(cor_clean)
                    if parsed_cor.hostname:
                        allowed_hosts.add(parsed_cor.hostname.lower())

        # Localhost/Loopback and staging wildcard suffixes allowed only in non-production environments
        dev_hosts = {"localhost", "127.0.0.1", "0.0.0.0"}
        if not is_prod:
            allowed_hosts.update(dev_hosts)
            if host.endswith(".onrender.com") or host.endswith(".vercel.app"):
                return True

        if host in allowed_hosts:
            return True

        return False
    except Exception:
        return False

def generate_oauth_state(workspace_id: uuid.UUID, user_id: Optional[uuid.UUID] = None) -> str:
    timestamp = int(time.time())
    nonce = secrets.token_hex(16)
    uid_str = str(user_id) if user_id else "any"
    state_payload = f"{workspace_id}:{uid_str}:{timestamp}:{nonce}"
    key = settings.get_primary_encryption_key() or settings.TOKEN_ENCRYPTION_KEY or "fallback_key"
    sig = hmac.new(
        key=key.encode("utf-8"),
        msg=state_payload.encode("utf-8"),
        digestmod=hashlib.sha256
    ).hexdigest()[:16]
    return f"{state_payload}:{sig}"

def verify_oauth_state(
    state: str,
    workspace_id: uuid.UUID,
    user_id: Optional[uuid.UUID] = None,
    max_age_seconds: int = 900
) -> bool:
    try:
        parts = state.split(":")
        keys = settings.get_encryption_keys() or [settings.TOKEN_ENCRYPTION_KEY or "fallback_key"]

        # 5-part state: ws_id:user_id:timestamp:nonce:sig
        if len(parts) == 5:
            ws_id_str, u_id_str, ts_str, nonce, provided_sig = parts
            if ws_id_str != str(workspace_id):
                return False
            if user_id and u_id_str != "any" and u_id_str != str(user_id):
                return False
            ts = int(ts_str)
            now = int(time.time())
            if now - ts > max_age_seconds or ts > now + 300:
                return False
            state_payload = f"{ws_id_str}:{u_id_str}:{ts_str}:{nonce}"
            for k in keys:
                expected_sig = hmac.new(
                    key=k.encode("utf-8"),
                    msg=state_payload.encode("utf-8"),
                    digestmod=hashlib.sha256
                ).hexdigest()[:16]
                if hmac.compare_digest(provided_sig, expected_sig):
                    return True
            return False

        # Legacy 3-part state: ws_id:nonce:sig (backwards compatibility)
        elif len(parts) == 3:
            ws_id_str, nonce, provided_sig = parts
            if ws_id_str != str(workspace_id):
                return False
            state_payload = f"{ws_id_str}:{nonce}"
            for k in keys:
                expected_sig = hmac.new(
                    key=k.encode("utf-8"),
                    msg=state_payload.encode("utf-8"),
                    digestmod=hashlib.sha256
                ).hexdigest()[:16]
                if hmac.compare_digest(provided_sig, expected_sig):
                    return True
            return False

        return False
    except Exception:
        return False

@router.get("/oauth/connect-url")
async def get_connect_url(
    redirect_uri: Optional[str] = None,
    user: User = Depends(get_current_user),
    workspace: Workspace = Depends(require_workspace_owner)
):
    """
    Returns Meta OAuth dialog URL with CSRF state containing cryptographically signed,
    time-limited (15m) workspace and user binding. Rejects unauthorized redirect destinations.
    """
    if redirect_uri and not _is_allowed_redirect_uri(redirect_uri):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid redirect_uri destination."
        )
    state = generate_oauth_state(workspace.id, user.id)
    url = MetaOAuth.get_authorization_url(state=state, redirect_uri=redirect_uri)
    return {"authorization_url": url, "state": state}

@router.post("/oauth/callback", response_model=InstagramAccountOut)
async def handle_oauth_callback(
    data: ConnectAccountRequest,
    user: User = Depends(get_current_user),
    workspace: Workspace = Depends(require_workspace_owner),
    db: AsyncSession = Depends(get_db)
):
    """
    Exchanges Meta authorization code for token, exchanges for 60-day long-lived token,
    queries Meta Graph API for connected Instagram Business Account details,
    and upserts InstagramAccount record with encrypted token and expiration date.
    """
    # 0. Validate redirect_uri destination if supplied
    if data.redirect_uri and not _is_allowed_redirect_uri(data.redirect_uri):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid redirect_uri destination."
        )

    # 1. Verify CSRF OAuth state (bound to workspace and user with 15m expiration)
    if not data.state or not verify_oauth_state(data.state, workspace.id, user.id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or missing OAuth state parameter (CSRF protection failed)."
        )

    # 2. Check and record OAuth state replay cache (single-use token)
    state_hash = hashlib.sha256(data.state.encode("utf-8")).hexdigest()
    if not await replay_cache.check_and_record(state_hash, ttl_seconds=900, namespace="oauth_state"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="OAuth state parameter has already been used or expired."
        )

    try:
        token_data = await MetaOAuth.exchange_code_for_token(data.code, data.redirect_uri)
        access_token = token_data["access_token"]
        long_lived = await MetaOAuth.exchange_for_long_lived_token(access_token)
        access_token = long_lived["access_token"]
        expires_in = long_lived.get("expires_in", 5184000)
        profile = await MetaOAuth.fetch_instagram_profile(access_token)
    except MetaOAuthError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    token_expires_at = datetime.now(timezone.utc) + timedelta(seconds=expires_in)
    ig_user_id = str(profile.get("user_id") or profile.get("id"))
    username = profile.get("username") or ig_user_id
    account_type = profile.get("account_type", "BUSINESS")
    follower_count = profile.get("followers_count") or 0
    profile_pic_url = profile.get("profile_picture_url")

    # 1. Enforce strict 1-to-1 mapping across the entire system:
    # An Instagram account (ig_user_id) can ONLY link to the initial Google account used for registration.
    stmt_global = select(InstagramAccount).where(
        InstagramAccount.ig_user_id == ig_user_id
    )
    res_global = await db.execute(stmt_global)
    existing_any = res_global.scalar_one_or_none()

    if existing_any and existing_any.workspace_id != workspace.id:
        # Retrieve original registering user's email for informative rejection or rebinding
        orig_user_stmt = (
            select(User.email)
            .join(WorkspaceMember, WorkspaceMember.user_id == User.id)
            .where(WorkspaceMember.workspace_id == existing_any.workspace_id)
            .limit(1)
        )
        orig_res = await db.execute(orig_user_stmt)
        orig_email = orig_res.scalar_one_or_none()

        if orig_email and orig_email.strip().lower() == user.email.strip().lower():
            # Same owner: gracefully rebind connection to the current active workspace
            logger.info(
                f"[INSTAGRAM] Rebinding Instagram account @{username} (ID {ig_user_id}) "
                f"from previous workspace {existing_any.workspace_id} to current workspace {workspace.id}"
            )
            existing_any.workspace_id = workspace.id
        else:
            email_hint = f" (linked to {orig_email[:3]}***@{orig_email.split('@')[-1]})" if orig_email else ""
            logger.warning(
                f"[SECURITY] Blocked link attempt: Instagram @{username} (ID {ig_user_id}) "
                f"is already registered with workspace {existing_any.workspace_id}, rejected workspace {workspace.id}"
            )
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    f"This Instagram account (@{username}) is already registered with another Comlina account{email_hint}. "
                    "An Instagram account can only be linked to the initial account used during registration. "
                    "Please sign in with your original account."
                )
            )

    encrypted_token = encrypt_token(access_token)
    account = existing_any
    now = datetime.now(timezone.utc)

    if account:
        # Update existing account for the same owner with latest real-time profile info and fresh tokens
        account.workspace_id = workspace.id
        account.user_id = user.id
        account.username = username
        account.account_type = account_type
        account.follower_count = follower_count
        account.access_token_encrypted = encrypted_token
        account.token_expires_at = token_expires_at
        account.profile_pic_url = profile_pic_url
        account.is_active = True
        account.auth_method = "META_INSTAGRAM_OAUTH"
        account.connection_status = "CONNECTED"
        account.last_validated_at = now
        account.last_refreshed_at = now
        account.last_error_code = None
        account.updated_at = now
    else:
        # Enforce workspace account limit
        stmt_count = select(func.count(InstagramAccount.id)).where(
            InstagramAccount.workspace_id == workspace.id,
            InstagramAccount.is_active == True
        )
        res_count = await db.execute(stmt_count)
        current_active = res_count.scalar() or 0
        if current_active >= workspace.max_accounts:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Workspace account limit reached ({workspace.max_accounts}). Upgrade plan to connect additional accounts."
            )

        account = InstagramAccount(
            workspace_id=workspace.id,
            user_id=user.id,
            ig_user_id=ig_user_id,
            username=username,
            account_type=account_type,
            follower_count=follower_count,
            profile_pic_url=profile_pic_url,
            access_token_encrypted=encrypted_token,
            token_expires_at=token_expires_at,
            is_active=True,
            auth_method="META_INSTAGRAM_OAUTH",
            connection_status="CONNECTED",
            last_validated_at=now,
            last_refreshed_at=now,
            last_error_code=None,
            connected_at=now,
            updated_at=now
        )
        db.add(account)

    await db.commit()
    await db.refresh(account)

    # Automatically install/subscribe webhook delivery on Meta for this Instagram account
    try:
        sub_res = await MetaOAuth.subscribe_app_to_account(access_token, ig_user_id)
        if sub_res.get("is_subscribed"):
            account.webhook_subscription_status = "SUBSCRIBED"
            account.webhook_subscribed_at = now
        else:
            account.webhook_subscription_status = "FAILED"
            account.last_error_code = sub_res.get("error_code")
        await db.commit()
        await db.refresh(account)
    except Exception as ex:
        logger.warning(f"Non-fatal error subscribing app to account {ig_user_id}: {ex}")

    return account

if settings.ENVIRONMENT == "development" and settings.ENABLE_DEV_ROUTES:
    @router.post("/connect-dev-account", response_model=InstagramAccountOut)
    async def connect_dev_account(
        user: User = Depends(get_current_user),
        workspace: Workspace = Depends(get_current_workspace),
        db: AsyncSession = Depends(get_db)
    ):
        """
        Instantly connects a verified Instagram Creator account in development mode.
        Allows testing full automation and conversation flows immediately without waiting for Meta console whitelisting.
        """
        dev_token = settings.INSTAGRAM_ACCESS_TOKEN or os.getenv("DEV_IG_ACCESS_TOKEN", "")
        if not dev_token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No dev access token configured. Set INSTAGRAM_ACCESS_TOKEN or DEV_IG_ACCESS_TOKEN in environment."
            )

        stmt = select(InstagramAccount).where(
            _get_owner_filter(workspace, user),
            InstagramAccount.is_active == True
        )
        res = await db.execute(stmt)
        existing = res.scalar_one_or_none()

        now = datetime.now(timezone.utc)
        user_id = user.id if (hasattr(user, "id") and user.id is not None) else None
        if existing:
            existing.access_token_encrypted = encrypt_token(dev_token)
            if user_id:
                existing.user_id = user_id
            existing.connection_status = "CONNECTED"
            existing.last_validated_at = now
            existing.last_refreshed_at = now
            existing.last_error_code = None
            await db.commit()
            await db.refresh(existing)
            return existing

        dev_ig_id = os.getenv("DEV_IG_USER_ID", "29500779709524479")
        account = InstagramAccount(
            workspace_id=workspace.id,
            user_id=user_id,
            ig_user_id=dev_ig_id,
            username=os.getenv("DEV_IG_USERNAME", "aiworkbench.lab"),
            account_type="MEDIA_CREATOR",
            follower_count=19,
            profile_pic_url="https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=150&auto=format&fit=crop&q=80",
            access_token_encrypted=encrypt_token(dev_token),
            token_expires_at=now + timedelta(days=60),
            is_active=True,
            auth_method="DEV_MOCK",
            connection_status="CONNECTED",
            last_validated_at=now,
            last_refreshed_at=now,
            last_error_code=None,
            connected_at=now,
            updated_at=now
        )
        db.add(account)
        await db.commit()
        await db.refresh(account)
        return account

@router.post("/accounts/{account_id}/refresh-token", response_model=InstagramAccountOut)
async def refresh_account_token(
    account_id: uuid.UUID,
    user: User = Depends(get_current_user),
    workspace: Workspace = Depends(get_current_workspace),
    db: AsyncSession = Depends(get_db)
):
    """
    Refreshes an Instagram account's long-lived access token and extends expiration.
    Enforces ownership by workspace OR user.
    """
    stmt = select(InstagramAccount).where(
        InstagramAccount.id == account_id,
        _get_owner_filter(workspace, user)
    )
    res = await db.execute(stmt)
    account = res.scalar_one_or_none()
    if not account:
        raise HTTPException(status_code=404, detail="Instagram account not found")

    now = datetime.now(timezone.utc)

    # 1. Check if token is already expired past recovery
    if account.token_expires_at:
        exp = account.token_expires_at
        if exp.tzinfo is None:
            exp = exp.replace(tzinfo=timezone.utc)
        if exp <= now:
            account.connection_status = "REAUTHORIZATION_REQUIRED"
            account.last_error_code = "TOKEN_EXPIRED"
            await db.commit()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Instagram token has already expired and cannot be refreshed. Please reconnect your account."
            )

    # 2. Check Meta 24-hour refresh rule:
    # Meta long-lived tokens cannot be refreshed if they are less than 24 hours old.
    # If refreshed or connected within 24h, return current account without error.
    last_ref = getattr(account, "last_refreshed_at", None) or getattr(account, "connected_at", None)
    if last_ref:
        if last_ref.tzinfo is None:
            last_ref = last_ref.replace(tzinfo=timezone.utc)
        if now - last_ref < timedelta(hours=24):
            logger.info(f"Account {account.id} token was refreshed or connected less than 24h ago; skipping Meta API call.")
            account.last_validated_at = now
            await db.commit()
            await db.refresh(account)
            return account

    try:
        current_token = decrypt_token(account.access_token_encrypted)
    except Exception as e:
        logger.error(f"Decryption failed for account {account.id}: {e}")
        account.connection_status = "REAUTHORIZATION_REQUIRED"
        account.last_error_code = "TOKEN_DECRYPTION_FAILED"
        await db.commit()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token decryption failed. Please reconnect your Instagram account."
        )

    try:
        refreshed_data = await MetaOAuth.refresh_long_lived_token(current_token)
    except MetaOAuthError as e:
        err_msg = str(e)
        logger.warning(f"MetaOAuthError during token refresh for account {account.id}: {err_msg}")
        if "24 hours" in err_msg.lower():
            account.last_refreshed_at = now
            account.last_validated_at = now
            await db.commit()
            await db.refresh(account)
            return account

        # Verify whether token is truly dead before marking REAUTHORIZATION_REQUIRED
        is_token_alive = False
        try:
            profile = await MetaOAuth.fetch_instagram_profile(current_token)
            if profile.get("id") or profile.get("user_id"):
                is_token_alive = True
        except Exception:
            is_token_alive = False

        if not is_token_alive and ("190" in err_msg or "expired" in err_msg.lower() or "revoked" in err_msg.lower()):
            account.connection_status = "REAUTHORIZATION_REQUIRED"
            account.last_error_code = "TOKEN_REVOKED"
            await db.commit()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Instagram session expired or revoked. Please reconnect: {err_msg}"
            )
        else:
            account.last_error_code = "REFRESH_FAILED"
            if is_token_alive:
                account.last_validated_at = now
            await db.commit()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Instagram token refresh failed: {err_msg}"
            )

    new_token = refreshed_data["access_token"]
    expires_in = refreshed_data.get("expires_in", 5184000)

    account.access_token_encrypted = encrypt_token(new_token)
    account.token_expires_at = now + timedelta(seconds=expires_in)
    account.is_active = True
    account.connection_status = "CONNECTED"
    account.last_refreshed_at = now
    account.last_validated_at = now
    account.last_error_code = None
    account.updated_at = now

    await db.commit()
    await db.refresh(account)

    try:
        sub_res = await MetaOAuth.subscribe_app_to_account(new_token, account.ig_user_id)
        if sub_res.get("is_subscribed"):
            account.webhook_subscription_status = "SUBSCRIBED"
            account.webhook_subscribed_at = now
            await db.commit()
            await db.refresh(account)
    except Exception as ex:
        logger.warning(f"Non-fatal error subscribing app to account {account.ig_user_id}: {ex}")

    return account

@router.post("/accounts/{account_id}/sync", response_model=InstagramAccountOut)
@router.post("/accounts/{account_id}/sync-profile", response_model=InstagramAccountOut)
async def sync_instagram_account_profile(
    account_id: uuid.UUID,
    user: User = Depends(get_current_user),
    workspace: Workspace = Depends(get_current_workspace),
    db: AsyncSession = Depends(get_db)
):
    """
    Fetches real-time profile data (followers, handle, profile picture) from Meta Graph API
    and updates the database.
    """
    stmt = select(InstagramAccount).where(
        InstagramAccount.id == account_id,
        _get_owner_filter(workspace, user)
    )
    res = await db.execute(stmt)
    account = res.scalar_one_or_none()
    if not account:
        raise HTTPException(status_code=404, detail="Instagram account not found")

    try:
        current_token = decrypt_token(account.access_token_encrypted)
    except Exception as e:
        logger.error(f"Decryption failed for account {account.id}: {e}")
        account.connection_status = "REAUTHORIZATION_REQUIRED"
        account.last_error_code = "TOKEN_DECRYPTION_FAILED"
        await db.commit()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token decryption failed. Please reconnect your Instagram account."
        )

    try:
        profile = await MetaOAuth.fetch_instagram_profile(current_token)
    except MetaOAuthError as e:
        err_msg = str(e)
        if "190" in err_msg or "expired" in err_msg.lower() or "invalid" in err_msg.lower():
            account.connection_status = "REAUTHORIZATION_REQUIRED"
            account.last_error_code = "TOKEN_REVOKED"
            await db.commit()
        raise HTTPException(status_code=400, detail=err_msg)

    now = datetime.now(timezone.utc)
    account.username = profile.get("username") or account.username
    followers = profile.get("followers_count")
    if followers is not None:
        try:
            account.follower_count = int(followers)
        except (ValueError, TypeError):
            pass
    if profile.get("profile_picture_url"):
        account.profile_pic_url = profile.get("profile_picture_url")
    account.last_validated_at = now
    account.connection_status = "CONNECTED"
    account.last_error_code = None
    account.updated_at = now

    await db.commit()
    await db.refresh(account)

    try:
        sub_res = await MetaOAuth.subscribe_app_to_account(current_token, account.ig_user_id)
        if sub_res.get("is_subscribed"):
            account.webhook_subscription_status = "SUBSCRIBED"
            account.webhook_subscribed_at = now
            await db.commit()
            await db.refresh(account)
    except Exception as ex:
        logger.warning(f"Non-fatal error subscribing app to account {account.ig_user_id}: {ex}")

    return account

@router.delete("/accounts/{account_id}", status_code=status.HTTP_204_NO_CONTENT)
async def disconnect_instagram_account(
    account_id: uuid.UUID,
    user: User = Depends(get_current_user),
    workspace: Workspace = Depends(get_current_workspace),
    db: AsyncSession = Depends(get_db)
):
    """
    Deactivates or disconnects an Instagram account from the workspace.
    Enforces ownership by workspace OR user.
    """
    stmt = select(InstagramAccount).where(
        InstagramAccount.id == account_id,
        _get_owner_filter(workspace, user)
    )
    res = await db.execute(stmt)
    account = res.scalar_one_or_none()
    if not account:
        raise HTTPException(status_code=404, detail="Instagram account not found")

    account.is_active = False
    account.connection_status = "DISCONNECTED"
    account.access_token_encrypted = ""
    account.last_error_code = None
    account.updated_at = datetime.now(timezone.utc)

    # Pause any active automations associated with this disconnected account
    stmt_pause = select(Automation).where(
        Automation.instagram_account_id == account.id,
        Automation.status == "ACTIVE"
    )
    active_autos = (await db.execute(stmt_pause)).scalars().all()
    for auto in active_autos:
        auto.status = "PAUSED"

    await db.commit()
    return None

@router.get(
    "/accounts/{account_id}/webhook-subscription",
    response_model=WebhookSubscriptionStatusOut
)
async def inspect_account_webhook_subscription(
    account_id: uuid.UUID,
    user: User = Depends(get_current_user),
    workspace: Workspace = Depends(get_current_workspace),
    db: AsyncSession = Depends(get_db)
):
    """
    Inspects account-level webhook subscription status from Meta Graph API (GET /{ig_user_id}/subscribed_apps).
    Workspace-authorized, never exposes access tokens or permits arbitrary account inspection.
    """
    stmt = select(InstagramAccount).where(
        InstagramAccount.id == account_id,
        _get_owner_filter(workspace, user)
    )
    res = await db.execute(stmt)
    account = res.scalar_one_or_none()
    if not account:
        raise HTTPException(status_code=404, detail="Instagram account not found")

    now = datetime.now(timezone.utc)
    try:
        current_token = decrypt_token(account.access_token_encrypted)
    except Exception as e:
        logger.error(f"Decryption failed for account {account.id}: {e}")
        account.connection_status = "REAUTHORIZATION_REQUIRED"
        account.last_error_code = "TOKEN_DECRYPTION_FAILED"
        account.webhook_subscription_status = "FAILED"
        await db.commit()
        return WebhookSubscriptionStatusOut(
            account_id=account.id,
            ig_user_id=account.ig_user_id,
            username=account.username,
            is_subscribed=False,
            subscribed_fields=[],
            status="TOKEN_EXPIRED",
            requires_reconnect=True,
            can_retry=False,
            error_code="TOKEN_DECRYPTION_FAILED",
            error_message="Token decryption failed. Please reconnect your Instagram account.",
            last_checked_at=now
        )

    res_meta = await MetaOAuth.check_app_subscription(current_token, account.ig_user_id)

    # Update account state based on verified status
    status_val = res_meta.get("status", "UNKNOWN")
    if status_val == "TOKEN_EXPIRED":
        account.connection_status = "REAUTHORIZATION_REQUIRED"
        account.last_error_code = "TOKEN_EXPIRED"
        account.webhook_subscription_status = "FAILED"
    elif status_val == "PERMISSION_DENIED":
        account.connection_status = "REAUTHORIZATION_REQUIRED"
        account.last_error_code = "PERMISSION_DENIED"
        account.webhook_subscription_status = "FAILED"
    elif res_meta.get("is_subscribed"):
        account.webhook_subscription_status = "SUBSCRIBED"
        account.webhook_subscribed_at = now
        account.last_error_code = None
    elif status_val == "NOT_SUBSCRIBED":
        account.webhook_subscription_status = "NOT_SUBSCRIBED"

    account.last_validated_at = now
    await db.commit()

    return WebhookSubscriptionStatusOut(
        account_id=account.id,
        ig_user_id=account.ig_user_id,
        username=account.username,
        is_subscribed=res_meta.get("is_subscribed", False),
        subscribed_fields=res_meta.get("subscribed_fields", []),
        status=status_val,
        requires_reconnect=res_meta.get("requires_reconnect", False),
        can_retry=res_meta.get("can_retry", True),
        error_code=res_meta.get("error_code"),
        error_message=res_meta.get("error_message"),
        last_checked_at=now
    )

@router.post(
    "/accounts/{account_id}/webhook-subscription",
    response_model=WebhookSubscriptionStatusOut
)
@router.post(
    "/accounts/{account_id}/webhook-subscription/retry",
    response_model=WebhookSubscriptionStatusOut
)
@router.post(
    "/accounts/{account_id}/retry-webhook-subscription",
    response_model=WebhookSubscriptionStatusOut
)
async def retry_account_webhook_subscription(
    account_id: uuid.UUID,
    user: User = Depends(get_current_user),
    workspace: Workspace = Depends(get_current_workspace),
    db: AsyncSession = Depends(get_db)
):
    """
    Retries/re-asserts account-level webhook subscription via POST /{ig_user_id}/subscribed_apps.
    Idempotent, workspace-authorized, avoids forcing full reconnect unless Meta requires reauthorization.
    """
    stmt = select(InstagramAccount).where(
        InstagramAccount.id == account_id,
        _get_owner_filter(workspace, user)
    )
    res = await db.execute(stmt)
    account = res.scalar_one_or_none()
    if not account:
        raise HTTPException(status_code=404, detail="Instagram account not found")

    now = datetime.now(timezone.utc)
    try:
        current_token = decrypt_token(account.access_token_encrypted)
    except Exception as e:
        logger.error(f"Decryption failed for account {account.id}: {e}")
        account.connection_status = "REAUTHORIZATION_REQUIRED"
        account.last_error_code = "TOKEN_DECRYPTION_FAILED"
        account.webhook_subscription_status = "FAILED"
        await db.commit()
        return WebhookSubscriptionStatusOut(
            account_id=account.id,
            ig_user_id=account.ig_user_id,
            username=account.username,
            is_subscribed=False,
            subscribed_fields=[],
            status="TOKEN_EXPIRED",
            requires_reconnect=True,
            can_retry=False,
            error_code="TOKEN_DECRYPTION_FAILED",
            error_message="Token decryption failed. Please reconnect your Instagram account.",
            last_checked_at=now
        )

    res_meta = await MetaOAuth.subscribe_app_to_account(current_token, account.ig_user_id)

    status_val = res_meta.get("status", "UNKNOWN")
    if res_meta.get("is_subscribed"):
        account.webhook_subscription_status = "SUBSCRIBED"
        account.webhook_subscribed_at = now
        account.connection_status = "CONNECTED"
        account.last_error_code = None
    elif status_val == "TOKEN_EXPIRED":
        account.connection_status = "REAUTHORIZATION_REQUIRED"
        account.last_error_code = "TOKEN_EXPIRED"
        account.webhook_subscription_status = "FAILED"
    elif status_val == "PERMISSION_DENIED":
        account.connection_status = "REAUTHORIZATION_REQUIRED"
        account.last_error_code = "PERMISSION_DENIED"
        account.webhook_subscription_status = "FAILED"
    else:
        account.webhook_subscription_status = "FAILED"
        account.last_error_code = res_meta.get("error_code")

    account.last_validated_at = now
    await db.commit()

    return WebhookSubscriptionStatusOut(
        account_id=account.id,
        ig_user_id=account.ig_user_id,
        username=account.username,
        is_subscribed=res_meta.get("is_subscribed", False),
        subscribed_fields=res_meta.get("subscribed_fields", []),
        status=status_val,
        requires_reconnect=res_meta.get("requires_reconnect", False),
        can_retry=res_meta.get("can_retry", True),
        error_code=res_meta.get("error_code"),
        error_message=res_meta.get("error_message"),
        last_checked_at=now
    )

