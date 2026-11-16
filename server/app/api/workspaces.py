# server/app/api/workspaces.py
import uuid
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from app.core.database import get_db
from app.api.deps import get_current_user, get_current_workspace
from app.models import User, Workspace, WorkspaceMember
from app.schemas import WorkspaceOut, WorkspaceCreate

router = APIRouter(prefix="/workspaces", tags=["Workspaces"])

class WorkspaceUpdate(BaseModel):
    name: Optional[str] = None

class WorkspaceSettingsUpdate(BaseModel):
    name: Optional[str] = None
    notification_lead: Optional[bool] = None
    notification_token: Optional[bool] = None
    notification_digest: Optional[bool] = None
    notification_rate: Optional[bool] = None
    follow_check: Optional[bool] = None
    public_reply: Optional[bool] = None
    stop_duplicate: Optional[bool] = None
    timezone: Optional[str] = None
    language: Optional[str] = None
    settings: Optional[Dict[str, Any]] = None

async def _verify_workspace_role(db: AsyncSession, workspace_id: uuid.UUID, user_id: uuid.UUID, required_roles: List[str]):
    stmt = select(WorkspaceMember).where(
        WorkspaceMember.workspace_id == workspace_id,
        WorkspaceMember.user_id == user_id,
        WorkspaceMember.role.in_(required_roles),
    )
    res = await db.execute(stmt)
    member = res.scalars().first()
    if not member:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Action requires one of the following roles: {', '.join(required_roles)}",
        )
    return member

@router.get("", response_model=List[WorkspaceOut])
async def list_user_workspaces(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = (
        select(Workspace)
        .join(WorkspaceMember, Workspace.id == WorkspaceMember.workspace_id)
        .where(WorkspaceMember.user_id == user.id)
    )
    res = await db.execute(stmt)
    return list(res.scalars().all())

@router.get("/current", response_model=WorkspaceOut)
async def get_active_workspace(
    workspace: Workspace = Depends(get_current_workspace)
):
    return workspace

@router.patch("/current", response_model=WorkspaceOut)
async def update_active_workspace(
    body: WorkspaceUpdate,
    workspace: Workspace = Depends(get_current_workspace),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _verify_workspace_role(db, workspace.id, user.id, ["OWNER", "ADMIN"])

    if body.name is not None and body.name.strip():
        workspace.name = body.name.strip()
        await db.commit()
        await db.refresh(workspace)

    return workspace

async def _apply_workspace_settings_update(target_ws: Workspace, body: WorkspaceSettingsUpdate, user: User, db: AsyncSession):
    await _verify_workspace_role(db, target_ws.id, user.id, ["OWNER", "ADMIN"])

    current_settings = dict(target_ws.settings) if isinstance(target_ws.settings, dict) else {}

    if body.name is not None and body.name.strip():
        target_ws.name = body.name.strip()

    update_fields = [
        "notification_lead", "notification_token", "notification_digest", "notification_rate",
        "follow_check", "public_reply", "stop_duplicate", "timezone", "language"
    ]
    for field in update_fields:
        val = getattr(body, field, None)
        if val is not None:
            current_settings[field] = val

    if body.settings and isinstance(body.settings, dict):
        current_settings.update(body.settings)

    target_ws.settings = current_settings
    await db.commit()
    await db.refresh(target_ws)

    return {
        "success": True,
        "workspace_id": str(target_ws.id),
        "name": target_ws.name,
        "settings": target_ws.settings
    }

async def _perform_workspace_deletion(target_ws: Workspace, user: User, db: AsyncSession):
    await _verify_workspace_role(db, target_ws.id, user.id, ["OWNER"])
    await db.delete(target_ws)
    await db.commit()
    return {
        "success": True,
        "message": f"Workspace '{target_ws.name}' and all associated automations, contacts, and accounts were permanently deleted."
    }

@router.patch("/current/settings")
async def update_current_workspace_settings(
    body: WorkspaceSettingsUpdate,
    current_ws: Workspace = Depends(get_current_workspace),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await _apply_workspace_settings_update(current_ws, body, user, db)

@router.patch("/{workspace_id}/settings")
async def update_workspace_by_id_settings(
    workspace_id: uuid.UUID,
    body: WorkspaceSettingsUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    ws_res = await db.execute(select(Workspace).where(Workspace.id == workspace_id))
    target_ws = ws_res.scalar_one_or_none()
    if not target_ws:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workspace not found")
    return await _apply_workspace_settings_update(target_ws, body, user, db)

@router.delete("/current", status_code=status.HTTP_200_OK)
async def delete_current_workspace(
    current_ws: Workspace = Depends(get_current_workspace),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await _perform_workspace_deletion(current_ws, user, db)

@router.delete("/{workspace_id}", status_code=status.HTTP_200_OK)
async def delete_workspace_by_id(
    workspace_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    ws_res = await db.execute(select(Workspace).where(Workspace.id == workspace_id))
    target_ws = ws_res.scalar_one_or_none()
    if not target_ws:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workspace not found")
    return await _perform_workspace_deletion(target_ws, user, db)
