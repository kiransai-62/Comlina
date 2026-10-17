# server/app/api/automations.py
import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.api.deps import get_current_workspace, get_current_user
from app.models import Workspace, User
from app.schemas import AutomationOut, AutomationCreate, AutomationUpdate
from app.services.automation_service import AutomationService

router = APIRouter(prefix="/automations", tags=["Automations"])

@router.get("", response_model=List[AutomationOut])
async def list_automations(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    workspace: Workspace = Depends(get_current_workspace),
    db: AsyncSession = Depends(get_db)
):
    return await AutomationService.list_automations(db, workspace.id, limit=limit, offset=offset)

@router.post("", response_model=AutomationOut, status_code=status.HTTP_201_CREATED)
async def create_automation(
    data: AutomationCreate,
    workspace: Workspace = Depends(get_current_workspace),
    db: AsyncSession = Depends(get_db)
):
    return await AutomationService.create_automation(
        db=db,
        workspace_id=workspace.id,
        data=data,
        max_automations=workspace.max_automations
    )

@router.get("/{automation_id}", response_model=AutomationOut)
async def get_automation(
    automation_id: uuid.UUID,
    workspace: Workspace = Depends(get_current_workspace),
    db: AsyncSession = Depends(get_db)
):
    automation = await AutomationService.get_automation(db, workspace.id, automation_id)
    if not automation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Automation not found")
    return automation

@router.put("/{automation_id}", response_model=AutomationOut)
async def update_automation(
    automation_id: uuid.UUID,
    data: AutomationUpdate,
    workspace: Workspace = Depends(get_current_workspace),
    db: AsyncSession = Depends(get_db)
):
    return await AutomationService.update_automation(db, workspace.id, automation_id, data)

@router.post("/{automation_id}/publish", response_model=AutomationOut)
async def publish_automation(
    automation_id: uuid.UUID,
    workspace: Workspace = Depends(get_current_workspace),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    try:
        return await AutomationService.publish_automation(db, workspace.id, automation_id, user.id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

@router.delete("/{automation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_automation(
    automation_id: uuid.UUID,
    workspace: Workspace = Depends(get_current_workspace),
    db: AsyncSession = Depends(get_db)
):
    success = await AutomationService.delete_automation(db, workspace.id, automation_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Automation not found")
    return None
