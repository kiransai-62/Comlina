# server/app/api/auth.py
import uuid
import hashlib
import os
import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Response, Request
from pydantic import BaseModel, EmailStr
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import jwt as pyjwt

from app.api.deps import get_current_user, get_current_workspace, get_db
from app.core.config import settings
from app.models import User, Workspace, WorkspaceMember

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["Auth"])


# ---------- Cookie Management ----------

def set_auth_cookies(response: Response, access_token: str, refresh_token: Optional[str] = None) -> None:
    """Sets secure, HttpOnly session and refresh cookies."""
    is_prod = settings.ENVIRONMENT != "development"
    # SameSite=None allows cross-subdomain credentials (e.g. comlina.onrender.com -> comlina-api.onrender.com)
    samesite = "none" if is_prod else "lax"
    secure = True if is_prod else False

    response.set_cookie(
        key="comlina_token",
        value=access_token,
        httponly=True,
        secure=secure,
        samesite=samesite,
        max_age=7 * 24 * 3600,  # 7 days
        path="/",
    )
    if refresh_token:
        response.set_cookie(
            key="comlina_refresh_token",
            value=refresh_token,
            httponly=True,
            secure=secure,
            samesite=samesite,
            max_age=30 * 24 * 3600,  # 30 days
            path="/",
        )


def clear_auth_cookies(response: Response) -> None:
    """Clears all session and refresh cookies."""
    is_prod = settings.ENVIRONMENT != "development"
    samesite = "none" if is_prod else "lax"
    secure = True if is_prod else False
    response.delete_cookie(key="comlina_token", path="/", samesite=samesite, secure=secure)
    response.delete_cookie(key="comlina_refresh_token", path="/", samesite=samesite, secure=secure)


# ---------- Schemas ----------

class SignupRequest(BaseModel):
    email: str
    password: str
    full_name: Optional[str] = None


class LoginRequest(BaseModel):
    email: str
    password: str


class RefreshRequest(BaseModel):
    refresh_token: Optional[str] = None


class TokenRefreshResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class AuthResponse(BaseModel):
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "bearer"
    user: Dict[str, Any]
    workspace: Optional[Dict[str, Any]] = None


# ---------- Password Utilities ----------

def _hash_password(password: str, salt: Optional[bytes] = None) -> tuple[str, str]:
    """Hash password with PBKDF2-HMAC-SHA256. Returns (hash_hex, salt_hex)."""
    if salt is None:
        salt = os.urandom(32)
    pw_hash = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100_000)
    return pw_hash.hex(), salt.hex()


def _verify_password(password: str, stored_hash: str, stored_salt: str) -> bool:
    """Verify password against stored PBKDF2 hash."""
    salt = bytes.fromhex(stored_salt)
    pw_hash = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100_000)
    return pw_hash.hex() == stored_hash


# ---------- JWT Utilities ----------

def create_backend_jwt(user_id: str, email: str, token_type: str = "access") -> str:
    """Issue a signed HS256 JWT for backend-authenticated users."""
    now = datetime.now(timezone.utc)
    if token_type == "refresh":
        exp = now + timedelta(days=30)
    else:
        exp = now + timedelta(days=7)  # 7-day stable access token

    payload = {
        "sub": user_id,
        "email": email,
        "iss": "comlina-backend",
        "aud": "authenticated",
        "iat": now,
        "exp": exp,
        "token_type": token_type,
        "role": "authenticated",
    }
    return pyjwt.encode(payload, settings.BACKEND_JWT_SECRET, algorithm="HS256")


# ---------- Helper: provision default workspace ----------

async def _ensure_default_workspace(user: User, db: AsyncSession) -> Optional[Workspace]:
    """Return user's first workspace, creating a default if none exists."""
    stmt = (
        select(Workspace)
        .join(WorkspaceMember, Workspace.id == WorkspaceMember.workspace_id)
        .where(WorkspaceMember.user_id == user.id)
        .limit(1)
    )
    res = await db.execute(stmt)
    workspace = res.scalars().first()

    if not workspace:
        workspace = Workspace(
            name="My Workspace",
            slug=f"workspace-{str(user.id)[:8]}",
        )
        db.add(workspace)
        await db.flush()
        member = WorkspaceMember(
            workspace_id=workspace.id,
            user_id=user.id,
            role="OWNER",
        )
        db.add(member)
        await db.commit()
        await db.refresh(workspace)

    return workspace


# ---------- Endpoints ----------

@router.post("/signup", response_model=AuthResponse)
async def signup(
    body: SignupRequest,
    response: Response,
    db: AsyncSession = Depends(get_db)
):
    """
    Register a new user with email + password.
    Returns a signed JWT and the provisioned default workspace.
    Sets secure HttpOnly session cookies.
    """
    email = body.email.strip().lower()
    password = body.password

    if len(password) < 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 6 characters",
        )

    # Check if user already exists
    existing = await db.execute(select(User).where(User.email == email))
    if existing.scalars().first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists. Please sign in.",
        )

    # Hash password
    pw_hash, pw_salt = _hash_password(password)

    # Create user
    user_id = uuid.uuid4()
    full_name = (body.full_name or "").strip() or email.split("@")[0]
    user = User(
        id=user_id,
        email=email,
        full_name=full_name,
    )
    # F13 fix: store the password hash in the dedicated `password_hash` column.
    # Legacy code stored it in `timezone` (format: "pbkdf2:<salt>:<hash>"); new accounts
    # use the canonical column so that profile PATCH operations cannot destroy auth material.
    user.password_hash = f"pbkdf2:{pw_salt}:{pw_hash}"

    db.add(user)
    await db.flush()

    # Provision default workspace
    workspace = await _ensure_default_workspace(user, db)
    await db.commit()

    # Issue JWT access & refresh tokens
    token = create_backend_jwt(str(user_id), email, token_type="access")
    refresh_token = create_backend_jwt(str(user_id), email, token_type="refresh")

    # Set secure persistent cookies
    set_auth_cookies(response, token, refresh_token)

    logger.info(f"[AUTH] New user registered: {email} ({user_id})")

    ws_data = None
    if workspace:
        ws_data = {
            "id": str(workspace.id),
            "name": workspace.name,
            "slug": workspace.slug,
        }

    return AuthResponse(
        access_token=token,
        refresh_token=refresh_token,
        user={
            "id": str(user_id),
            "email": email,
            "full_name": full_name,
        },
        workspace=ws_data,
    )


@router.post("/login", response_model=AuthResponse)
async def login(
    body: LoginRequest,
    response: Response,
    db: AsyncSession = Depends(get_db)
):
    """
    Authenticate with email + password against the backend user store.
    Returns a signed JWT and the user's workspace.
    Sets secure HttpOnly session cookies.
    """
    email = body.email.strip().lower()
    password = body.password

    res = await db.execute(select(User).where(User.email == email))
    user = res.scalars().first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    # Verify password.
    # New accounts store the hash in `user.password_hash`.
    # Legacy accounts (created before F13 fix) have it in `user.timezone` ("pbkdf2:<salt>:<hash>").
    # Accept either location; on first successful legacy login, migrate the hash in-place.
    raw_hash_str = None
    if hasattr(user, "password_hash") and user.password_hash and user.password_hash.startswith("pbkdf2:"):
        raw_hash_str = user.password_hash
    elif (user.timezone or "").startswith("pbkdf2:"):
        raw_hash_str = user.timezone  # legacy storage

    if not raw_hash_str:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    parts = raw_hash_str.split(":", 2)
    if len(parts) != 3:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    _, stored_salt, stored_hash = parts
    if not _verify_password(password, stored_hash, stored_salt):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    # Opportunistic migration: if the hash lived in `timezone`, move it to `password_hash`
    # so subsequent profile updates can no longer destroy it.
    if hasattr(user, "password_hash") and not (user.password_hash or "").startswith("pbkdf2:"):
        user.password_hash = raw_hash_str
        # Clear the timezone field only if it still holds the hash (leave user-set timezones)
        if (user.timezone or "").startswith("pbkdf2:"):
            user.timezone = "UTC"
        await db.flush()

    # Provision workspace if needed
    workspace = await _ensure_default_workspace(user, db)

    token = create_backend_jwt(str(user.id), email, token_type="access")
    refresh_token = create_backend_jwt(str(user.id), email, token_type="refresh")

    # Set secure persistent cookies
    set_auth_cookies(response, token, refresh_token)

    logger.info(f"[AUTH] User logged in: {email}")

    ws_data = None
    if workspace:
        ws_data = {
            "id": str(workspace.id),
            "name": workspace.name,
            "slug": workspace.slug,
        }

    return AuthResponse(
        access_token=token,
        refresh_token=refresh_token,
        user={
            "id": str(user.id),
            "email": user.email,
            "full_name": user.full_name,
        },
        workspace=ws_data,
    )


@router.post("/refresh", response_model=TokenRefreshResponse)
async def refresh_token_endpoint(
    request: Request,
    response: Response,
    body: Optional[RefreshRequest] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Refreshes an expired or active access token using a valid backend refresh token.
    Accepts refresh token from request body or HttpOnly cookie.
    Rotates tokens and updates session cookies.
    """
    token = None
    if body and body.refresh_token:
        token = body.refresh_token.strip()
    if not token:
        token = request.cookies.get("comlina_refresh_token")

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        payload = pyjwt.decode(
            token,
            settings.BACKEND_JWT_SECRET,
            algorithms=["HS256"],
            options={"verify_aud": False},
        )
    except pyjwt.ExpiredSignatureError:
        clear_auth_cookies(response)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token has expired. Please sign in again.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except pyjwt.PyJWTError:
        clear_auth_cookies(response)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if payload.get("iss") != "comlina-backend" or payload.get("token_type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token type",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id_str = payload.get("sub")
    email = payload.get("email")
    if not user_id_str or not email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        user_uuid = uuid.UUID(user_id_str)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user ID in token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Verify user exists and is active
    stmt = select(User).where(User.id == user_uuid)
    res = await db.execute(stmt)
    user = res.scalars().first()
    if not user:
        stmt_email = select(User).where(User.email == email)
        res_email = await db.execute(stmt_email)
        user = res_email.scalars().first()
        if not user:
            clear_auth_cookies(response)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User account no longer exists",
                headers={"WWW-Authenticate": "Bearer"},
            )

    new_access = create_backend_jwt(str(user.id), user.email, token_type="access")
    new_refresh = create_backend_jwt(str(user.id), user.email, token_type="refresh")

    # Rotate cookies atomically
    set_auth_cookies(response, new_access, new_refresh)

    return TokenRefreshResponse(
        access_token=new_access,
        refresh_token=new_refresh,
        token_type="bearer",
    )


@router.post("/logout")
async def logout(response: Response):
    """Sign out user and clear session cookies."""
    clear_auth_cookies(response)
    return {"status": "ok", "message": "Signed out successfully"}


@router.get("/me")
async def get_current_profile(
    response: Response,
    user: User = Depends(get_current_user),
    workspace: Workspace = Depends(get_current_workspace),
) -> Dict[str, Any]:
    """
    Returns the authenticated user's profile and active workspace.
    Used by AuthGuard to bootstrap the frontend session and refresh cookies.
    """
    access_token = create_backend_jwt(str(user.id), user.email, token_type="access")
    refresh_token = create_backend_jwt(str(user.id), user.email, token_type="refresh")
    set_auth_cookies(response, access_token, refresh_token)

    return {
        "id": str(user.id),
        "email": user.email,
        "full_name": user.full_name,
        "avatar_url": user.avatar_url,
        "timezone": user.timezone if not (user.timezone or "").startswith("pbkdf2:") else None,
        "workspace": {
            "id": str(workspace.id),
            "name": workspace.name,
            "slug": workspace.slug,
            "plan_tier": workspace.plan_tier or "FREE",
            "plan_status": workspace.plan_status or "ACTIVE",
            "max_automations": workspace.max_automations,
            "max_accounts": workspace.max_accounts,
        },
        "session": {
            "access_token": access_token,
            "refresh_token": refresh_token,
        },
        "access_token": access_token,
        "refresh_token": refresh_token,
    }


class ProfileUpdateRequest(BaseModel):
    full_name: Optional[str] = None
    avatar_url: Optional[str] = None
    timezone: Optional[str] = None
    phone: Optional[str] = None


@router.patch("/profile")
async def update_current_profile(
    body: ProfileUpdateRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """
    Updates the authenticated user's profile details (full_name, timezone, avatar_url).
    """
    if body.full_name is not None:
        user.full_name = body.full_name.strip()
    if body.timezone is not None:
        # F13 guard: the `timezone` column was previously (mis)used to store the PBKDF2
        # password hash for legacy accounts. Never let a profile update overwrite it.
        new_tz = body.timezone.strip()
        if new_tz.startswith("pbkdf2:"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid timezone value.",
            )
        # Only write the new timezone if the current value is NOT holding a legacy hash.
        # Accounts that have been migrated (password_hash set) can freely update timezone.
        current_tz = user.timezone or ""
        if not current_tz.startswith("pbkdf2:"):
            user.timezone = new_tz
        # else: leave the legacy hash in place; the next login will migrate it.
    if body.avatar_url is not None:
        user.avatar_url = body.avatar_url.strip()

    await db.commit()
    await db.refresh(user)

    return {
        "id": str(user.id),
        "email": user.email,
        "full_name": user.full_name,
        "avatar_url": user.avatar_url,
        "timezone": user.timezone if not (user.timezone or "").startswith("pbkdf2:") else None,
        "phone": body.phone,
    }


