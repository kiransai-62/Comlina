# server/app/api/deps.py
import asyncio
import uuid
import logging
from typing import Optional
from fastapi import Depends, HTTPException, Header, status
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from sqlalchemy import select
from app.core.database import get_db
from app.core.security import security_bearer, decode_supabase_jwt
from app.models import User, Workspace, WorkspaceMember

logger = logging.getLogger(__name__)

# Concurrency lock to prevent race conditions during first-login user/workspace provisioning.
# When React Query fires 4+ parallel API calls on first dashboard load, all of them
# would simultaneously try to INSERT the same user/workspace rows, causing IntegrityError
# (UNIQUE constraint) and MultipleResultsFound crashes.
_provision_lock = asyncio.Lock()

async def get_current_user(
    auth_header: Optional[HTTPAuthorizationCredentials] = Depends(security_bearer),
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    Authenticates request via Supabase Auth JWT or backend-issued JWT.
    Resolves or initializes user record in Comlina database.
    Uses asyncio.Lock + IntegrityError recovery to handle concurrent first-login requests.
    """
    if not auth_header or not auth_header.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token = auth_header.credentials
    token_data = decode_supabase_jwt(token)
    user_id_str = token_data.get("sub")
    if not user_id_str:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token: missing subject claim",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        user_uuid = uuid.UUID(user_id_str)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user ID format in token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    email = token_data.get("email") or f"{user_uuid}@comlina.ai"
    user_meta = token_data.get("user_metadata") or {}
    full_name = user_meta.get("full_name") or user_meta.get("name") or email.split("@")[0]
    avatar_url = user_meta.get("avatar_url") or user_meta.get("picture")

    # First try a fast non-locked lookup by UUID or by verified Email
    stmt = select(User).where(User.id == user_uuid)
    res = await db.execute(stmt)
    user = res.scalars().first()

    if not user and email:
        stmt_email = select(User).where(User.email == email.strip().lower())
        res_email = await db.execute(stmt_email)
        user = res_email.scalars().first()

    if user:
        # Save and update any changed details from the login token
        updated = False
        if email and user.email != email.strip().lower():
            user.email = email.strip().lower()
            updated = True
        if full_name and user.full_name != full_name and not (user.timezone and user.timezone.startswith("pbkdf2:")):
            user.full_name = full_name
            updated = True
        if avatar_url and user.avatar_url != avatar_url:
            user.avatar_url = avatar_url
            updated = True
        if updated:
            await db.commit()
            await db.refresh(user)
        return user

    # User doesn't exist yet — acquire lock to safely provision
    async with _provision_lock:
        # Re-check after acquiring lock (another request may have created the user)
        res = await db.execute(select(User).where(User.id == user_uuid))
        user = res.scalars().first()
        if not user and email:
            res_email = await db.execute(select(User).where(User.email == email.strip().lower()))
            user = res_email.scalars().first()
        if user:
            return user

        user = User(
            id=user_uuid,
            email=email.strip().lower(),
            full_name=full_name,
            avatar_url=avatar_url
        )
        db.add(user)

        try:
            await db.commit()
            await db.refresh(user)
        except IntegrityError:
            await db.rollback()
            logger.info(f"[AUTH] IntegrityError during user creation for {user_uuid}, recovering...")
            res = await db.execute(select(User).where(User.id == user_uuid))
            user = res.scalars().first()
            if not user and email:
                res_email = await db.execute(select(User).where(User.email == email.strip().lower()))
                user = res_email.scalars().first()
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to provision user account",
                )

    return user

async def get_current_workspace(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    x_workspace_id: Optional[str] = Header(None, alias="X-Workspace-ID")
) -> Workspace:
    """
    Strict multi-tenant security dependency.
    Resolves the active workspace ONLY if user has verified membership in it.
    Uses asyncio.Lock + IntegrityError recovery for concurrent default workspace creation.
    """
    stmt = (
        select(Workspace)
        .join(WorkspaceMember, Workspace.id == WorkspaceMember.workspace_id)
        .where(WorkspaceMember.user_id == user.id)
    )

    if x_workspace_id:
        try:
            target_ws_id = uuid.UUID(x_workspace_id)
            stmt = stmt.where(Workspace.id == target_ws_id)
        except ValueError:
            pass

    res = await db.execute(stmt)
    workspace = res.scalars().first()

    if workspace:
        return workspace

    # No matching workspace found — try to find any workspace for this user
    stmt_first = (
        select(Workspace)
        .join(WorkspaceMember, Workspace.id == WorkspaceMember.workspace_id)
        .where(WorkspaceMember.user_id == user.id)
        .limit(1)
    )
    res_first = await db.execute(stmt_first)
    workspace = res_first.scalars().first()

    if workspace:
        return workspace

    # No workspace at all — create default with lock to prevent duplicates
    async with _provision_lock:
        # Re-check after lock
        res_recheck = await db.execute(stmt_first)
        workspace = res_recheck.scalars().first()
        if workspace:
            return workspace

        workspace = Workspace(
            name="My Workspace",
            slug=f"workspace-{str(user.id)[:8]}"
        )
        db.add(workspace)
        await db.flush()

        member = WorkspaceMember(
            workspace_id=workspace.id,
            user_id=user.id,
            role="OWNER"
        )
        db.add(member)

        try:
            await db.commit()
            await db.refresh(workspace)
        except IntegrityError:
            await db.rollback()
            logger.info(f"[AUTH] IntegrityError during workspace creation for user {user.id}, recovering...")
            res_recover = await db.execute(stmt_first)
            workspace = res_recover.scalars().first()
            if not workspace:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to provision default workspace",
                )

    return workspace

async def require_workspace_owner(
    user: User = Depends(get_current_user),
    workspace: Workspace = Depends(get_current_workspace),
    db: AsyncSession = Depends(get_db)
) -> Workspace:
    """
    Role-based access control dependency: requires user to have OWNER role in the workspace.
    """
    stmt = select(WorkspaceMember.role).where(
        WorkspaceMember.workspace_id == workspace.id,
        WorkspaceMember.user_id == user.id
    )
    res = await db.execute(stmt)
    role = res.scalar_one_or_none()
    if role != "OWNER":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: This operation requires workspace OWNER role"
        )
    return workspace
