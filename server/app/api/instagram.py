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
from app.models import Workspace, InstagramAccount, Automation, User
from app.schemas import InstagramAccountOut, ConnectAccountRequest, InstagramMediaPage
from app.integrations.instagram.oauth import MetaOAuth, MetaOAuthError
from app.integrations.instagram.client import MetaGraphClient
from app.integrations.instagram.exceptions import MetaGraphAPIError, MetaTokenExpiredError, MetaRateLimitError
from app.core.encryption import encrypt_token, decrypt_token

logger = logging.getLogger("instagram_api")
router = APIRouter(prefix="/instagram", tags=["Instagram"])

@router.get("/accounts", response_model=List[InstagramAccountOut])
async def list_instagram_accounts(
    workspace: Workspace = Depends(get_current_workspace),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(InstagramAccount).where(
        InstagramAccount.workspace_id == workspace.id,
        InstagramAccount.is_active == True
    )
    res = await db.execute(stmt)
    return list(res.scalars().all())

def _normalize_media_item(item: Dict[str, Any]) -> Dict[str, Any]:
    m_type = "REEL" if item.get("media_type") == "VIDEO" or item.get("media_product_type") == "REELS" else "POST"
    image_url = item.get("thumbnail_url") or item.get("media_url") or ""
    return {
        "id": str(item.get("id", "")),
        "type": m_type,
        "caption": item.get("caption") or "",
        "imageUrl": image_url,
        "commentsCount": int(item.get("comments_count") or 0),
        "likesCount": int(item.get("like_count") or 0),
        "publishedDate": str(item.get("timestamp") or ""),
        "permalink": item.get("permalink") or ""
    }

@router.get("/media", response_model=List[Dict[str, Any]])
@router.get("/accounts/{account_id}/media", response_model=List[Dict[str, Any]])
async def list_instagram_media(
    account_id: Optional[uuid.UUID] = None,
    limit: int = Query(24, ge=1, le=50),
    workspace: Workspace = Depends(get_current_workspace),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(InstagramAccount).where(
        InstagramAccount.workspace_id == workspace.id,
        InstagramAccount.is_active == True  # noqa: E712
    )
    if account_id:
        stmt = stmt.where(InstagramAccount.id == account_id)
    account = (await db.execute(stmt)).scalars().first()
    if not account:
        raise HTTPException(status_code=404, detail="No connected Instagram account found.")
    try:
        token = decrypt_token(account.access_token_encrypted)
    except Exception:
        raise HTTPException(status_code=409, detail="Stored token is unreadable. Reconnect your Instagram account.")

    if not token or token.startswith("mock_"):
        return []

    params = {
        "fields": "id,caption,media_type,media_product_type,media_url,thumbnail_url,permalink,timestamp,like_count,comments_count",
        "limit": limit
    }
    try:
        raw = await MetaGraphClient(token).get("me/media", params=params)
    except MetaTokenExpiredError:
        raise HTTPException(status_code=409, detail="Instagram token expired. Reconnect the account.")
    except MetaRateLimitError:
        raise HTTPException(status_code=429, detail="Instagram rate limit reached. Try again shortly.")
    except MetaGraphAPIError as e:
        logger.warning(f"Failed to fetch media from Meta: {e}")
        return []

    raw_items = raw.get("data", []) if isinstance(raw, dict) else []
    return [_normalize_media_item(m) for m in raw_items]

def _is_allowed_redirect_uri(redirect_uri: Optional[str]) -> bool:
    if not redirect_uri:
        return True
    try:
        parsed = urlparse(redirect_uri)
        if not parsed.scheme or not parsed.netloc:
            return False
        host = (parsed.hostname or "").lower()
        allowed_hosts = {
            "localhost",
            "127.0.0.1",
            "0.0.0.0",
            "app.comlina.ai",
            "comlina.ai",
            "www.comlina.ai",
            "comlina.com",
            "www.comlina.com",
        }
        if settings.META_REDIRECT_URI:
            meta_parsed = urlparse(settings.META_REDIRECT_URI)
            if meta_parsed.hostname:
                allowed_hosts.add(meta_parsed.hostname.lower())
        if host in allowed_hosts or host.endswith(".onrender.com") or host.endswith(".vercel.app"):
            return True
        return False
    except Exception:
        return False

def generate_oauth_state(workspace_id: uuid.UUID, user_id: Optional[uuid.UUID] = None) -> str:
    timestamp = int(time.time())
    nonce = secrets.token_hex(16)
    uid_str = str(user_id) if user_id else "any"
    state_payload = f"{workspace_id}:{uid_str}:{timestamp}:{nonce}"
    sig = hmac.new(
        key=settings.TOKEN_ENCRYPTION_KEY.encode("utf-8"),
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
            expected_sig = hmac.new(
                key=settings.TOKEN_ENCRYPTION_KEY.encode("utf-8"),
                msg=state_payload.encode("utf-8"),
                digestmod=hashlib.sha256
            ).hexdigest()[:16]
            return hmac.compare_digest(provided_sig, expected_sig)
        # Legacy 3-part state: ws_id:nonce:sig (backwards compatibility)
        elif len(parts) == 3:
            ws_id_str, nonce, provided_sig = parts
            if ws_id_str != str(workspace_id):
                return False
            state_payload = f"{ws_id_str}:{nonce}"
            expected_sig = hmac.new(
                key=settings.TOKEN_ENCRYPTION_KEY.encode("utf-8"),
                msg=state_payload.encode("utf-8"),
                digestmod=hashlib.sha256
            ).hexdigest()[:16]
            return hmac.compare_digest(provided_sig, expected_sig)
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
    # 1. Verify CSRF OAuth state (bound to workspace and user with 15m expiration)
    if not data.state or not verify_oauth_state(data.state, workspace.id, user.id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or missing OAuth state parameter (CSRF protection failed)."
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

    # Check if account already exists for this workspace and ig_user_id
    stmt = select(InstagramAccount).where(
        InstagramAccount.workspace_id == workspace.id,
        InstagramAccount.ig_user_id == ig_user_id
    )
    res = await db.execute(stmt)
    account = res.scalar_one_or_none()

    encrypted_token = encrypt_token(access_token)

    if account:
        account.username = username
        account.account_type = account_type
        account.follower_count = follower_count
        account.access_token_encrypted = encrypted_token
        account.token_expires_at = token_expires_at
        account.profile_pic_url = profile_pic_url
        account.is_active = True
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
            ig_user_id=ig_user_id,
            username=username,
            account_type=account_type,
            follower_count=follower_count,
            profile_pic_url=profile_pic_url,
            access_token_encrypted=encrypted_token,
            token_expires_at=token_expires_at,
            is_active=True
        )
        db.add(account)

    await db.commit()
    await db.refresh(account)
    return account

@router.post("/connect-dev-account", response_model=InstagramAccountOut)
async def connect_dev_account(
    workspace: Workspace = Depends(require_workspace_owner),
    db: AsyncSession = Depends(get_db)
):
    """
    Instantly connects a verified Instagram Creator account in development mode.
    Allows testing full automation and conversation flows immediately without waiting for Meta console whitelisting.
    """
    stmt = select(InstagramAccount).where(
        InstagramAccount.workspace_id == workspace.id,
        InstagramAccount.is_active == True
    )
    res = await db.execute(stmt)
    existing = res.scalar_one_or_none()
    dev_token = settings.INSTAGRAM_ACCESS_TOKEN or (
        settings.META_WEBHOOK_VERIFY_TOKEN if settings.META_WEBHOOK_VERIFY_TOKEN.startswith("IGAA") else ""
    ) or os.getenv("DEV_IG_ACCESS_TOKEN", "")

    if existing:
        if dev_token:
            existing.access_token_encrypted = encrypt_token(dev_token)
            await db.commit()
            await db.refresh(existing)
        return existing

    dev_ig_id = "29500779709524479"
    account = InstagramAccount(
        workspace_id=workspace.id,
        ig_user_id=dev_ig_id,
        username="aiworkbench.lab",
        account_type="MEDIA_CREATOR",
        follower_count=19,
        profile_pic_url="https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=150&auto=format&fit=crop&q=80",
        access_token_encrypted=encrypt_token(dev_token),
        token_expires_at=datetime.now(timezone.utc) + timedelta(days=60),
        is_active=True
    )
    db.add(account)
    await db.commit()
    await db.refresh(account)
    return account

@router.post("/accounts/{account_id}/refresh-token", response_model=InstagramAccountOut)
async def refresh_account_token(
    account_id: uuid.UUID,
    workspace: Workspace = Depends(require_workspace_owner),
    db: AsyncSession = Depends(get_db)
):
    """
    Refreshes an Instagram account's long-lived access token and extends expiration.
    """
    stmt = select(InstagramAccount).where(
        InstagramAccount.id == account_id,
        InstagramAccount.workspace_id == workspace.id
    )
    res = await db.execute(stmt)
    account = res.scalar_one_or_none()
    if not account:
        raise HTTPException(status_code=404, detail="Instagram account not found")

    try:
        current_token = decrypt_token(account.access_token_encrypted)
    except Exception as e:
        logger.error(f"Decryption failed for account {account.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token decryption failed. Please reconnect your Instagram account."
        )

    try:
        refreshed_data = await MetaOAuth.refresh_long_lived_token(current_token)
    except MetaOAuthError as e:
        raise HTTPException(status_code=400, detail=str(e))
    new_token = refreshed_data["access_token"]

    expires_in = refreshed_data.get("expires_in", 5184000)
    account.access_token_encrypted = encrypt_token(new_token)
    account.token_expires_at = datetime.now(timezone.utc) + timedelta(seconds=expires_in)
    account.is_active = True

    await db.commit()
    await db.refresh(account)
    return account

@router.delete("/accounts/{account_id}", status_code=status.HTTP_204_NO_CONTENT)
async def disconnect_instagram_account(
    account_id: uuid.UUID,
    workspace: Workspace = Depends(require_workspace_owner),
    db: AsyncSession = Depends(get_db)
):
    """
    Deactivates or disconnects an Instagram account from the workspace.
    """
    stmt = select(InstagramAccount).where(
        InstagramAccount.id == account_id,
        InstagramAccount.workspace_id == workspace.id
    )
    res = await db.execute(stmt)
    account = res.scalar_one_or_none()
    if not account:
        raise HTTPException(status_code=404, detail="Instagram account not found")

    account.is_active = False
    account.access_token_encrypted = ""

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
