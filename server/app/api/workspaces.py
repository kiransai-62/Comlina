# server/app/api/workspaces.py
import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.api.deps import get_current_user, get_current_workspace
from app.models import User, Workspace, WorkspaceMember
from app.schemas import WorkspaceOut, WorkspaceCreate

router = APIRouter(prefix="/workspaces", tags=["Workspaces"])

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
