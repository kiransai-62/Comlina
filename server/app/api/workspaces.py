# server/app/api/workspaces.py
import uuid
from typing import List, Optional
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.api.deps import get_current_user, get_current_workspace
from app.models import User, Workspace, WorkspaceMember
from app.schemas import WorkspaceOut, WorkspaceCreate

router = APIRouter(prefix="/workspaces", tags=["Workspaces"])

class WorkspaceUpdate(BaseModel):
    name: Optional[str] = None

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
    # Verify user is OWNER or ADMIN of this workspace
    stmt = select(WorkspaceMember).where(
        WorkspaceMember.workspace_id == workspace.id,
        WorkspaceMember.user_id == user.id,
        WorkspaceMember.role.in_(["OWNER", "ADMIN"]),
    )
    res = await db.execute(stmt)
    if not res.scalars().first():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only workspace owners or admins can update workspace settings",
        )

    if body.name is not None and body.name.strip():
        workspace.name = body.name.strip()
        await db.commit()
        await db.refresh(workspace)

    return workspace

