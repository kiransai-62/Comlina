# server/app/api/contacts.py
import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.api.deps import get_current_workspace
from app.models import Workspace
from app.schemas import ContactOut
from app.services.contact_service import ContactService

router = APIRouter(prefix="/contacts", tags=["Contacts"])

@router.get("", response_model=List[ContactOut])
async def list_contacts(
    tag: Optional[str] = Query(None, max_length=100),
    follower_status: Optional[str] = Query(None, max_length=50),
    is_converted: Optional[bool] = Query(None),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    workspace: Workspace = Depends(get_current_workspace),
    db: AsyncSession = Depends(get_db)
):
    return await ContactService.list_contacts(
        db=db,
        workspace_id=workspace.id,
        tag=tag,
        follower_status=follower_status,
        is_converted=is_converted,
        limit=limit,
        offset=offset
    )

@router.get("/export-csv")
async def export_contacts_csv(
    workspace: Workspace = Depends(get_current_workspace),
    db: AsyncSession = Depends(get_db)
):
    contacts = await ContactService.list_contacts(db, workspace.id)
    csv_content = ContactService.export_contacts_csv(contacts)
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=comlina_contacts.csv"}
    )
