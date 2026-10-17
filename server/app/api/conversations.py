# server/app/api/conversations.py
import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.api.deps import get_current_workspace
from app.models import Workspace
from app.schemas import ConversationOut, MessageOut, MessageCreate
from app.services.conversation_service import ConversationService

router = APIRouter(prefix="/conversations", tags=["Conversations"])

@router.get("", response_model=List[ConversationOut])
async def list_conversations(
    account_id: Optional[uuid.UUID] = None,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    workspace: Workspace = Depends(get_current_workspace),
    db: AsyncSession = Depends(get_db)
):
    return await ConversationService.list_conversations(
        db, workspace.id, account_id, limit=limit, offset=offset
    )

@router.get("/{conversation_id}/messages", response_model=List[MessageOut])
async def get_conversation_messages(
    conversation_id: uuid.UUID,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    workspace: Workspace = Depends(get_current_workspace),
    db: AsyncSession = Depends(get_db)
):
    return await ConversationService.get_messages(
        db, workspace.id, conversation_id, limit=limit, offset=offset
    )

@router.post("/{conversation_id}/messages", response_model=MessageOut, status_code=201)
async def send_conversation_message(
    conversation_id: uuid.UUID,
    data: MessageCreate,
    workspace: Workspace = Depends(get_current_workspace),
    db: AsyncSession = Depends(get_db)
):
    text = data.text.strip()
    if not text:
        raise HTTPException(status_code=422, detail="Message text cannot be empty.")
    return await ConversationService.send_message(db, workspace.id, conversation_id, text, data.media_url)
