# server/app/services/conversation_service.py
import uuid
from typing import List, Optional
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException, status
from app.models import Conversation, Message, Contact, InstagramAccount
from app.core.encryption import decrypt_token
from app.integrations.instagram.client import MetaGraphClient
from app.integrations.instagram.messaging import InstagramMessaging
from app.integrations.instagram.exceptions import MetaGraphAPIError, MetaTokenExpiredError, MetaRateLimitError

class ConversationService:
    @staticmethod
    async def list_conversations(
        db: AsyncSession,
        workspace_id: uuid.UUID,
        instagram_account_id: Optional[uuid.UUID] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Conversation]:
        stmt = (
            select(Conversation, Contact)
            .outerjoin(Contact, (Contact.id == Conversation.contact_id) & (Contact.workspace_id == workspace_id))
            .where(Conversation.workspace_id == workspace_id)
        )
        if instagram_account_id:
            stmt = stmt.where(Conversation.instagram_account_id == instagram_account_id)
        stmt = stmt.order_by(Conversation.last_message_at.desc()).limit(limit).offset(offset)
        res = await db.execute(stmt)
        rows = res.all()
        results = []
        for conv, contact in rows:
            if contact:
                conv.contact_username = contact.username
                conv.name = contact.full_name or contact.username
                conv.followers = None
                conv.followed_you = (contact.follower_status == "FOLLOWING")
                conv.tags = contact.tags or []
                conv.notes = contact.notes
                conv.first_seen = contact.created_at
            results.append(conv)
        return results

    @staticmethod
    async def get_messages(
        db: AsyncSession,
        workspace_id: uuid.UUID,
        conversation_id: uuid.UUID,
        limit: int = 50,
        offset: int = 0
    ) -> List[Message]:
        # Enforce multi-tenant conversation ownership verification
        stmt_conv = select(Conversation).where(
            Conversation.id == conversation_id,
            Conversation.workspace_id == workspace_id
        )
        res_conv = await db.execute(stmt_conv)
        conversation = res_conv.scalar_one_or_none()
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found in this workspace."
            )

        stmt = (
            select(Message)
            .where(
                Message.workspace_id == workspace_id,
                Message.conversation_id == conversation_id
            )
            .order_by(Message.created_at.asc())
            .limit(limit)
            .offset(offset)
        )
        res = await db.execute(stmt)
        return list(res.scalars().all())

    @staticmethod
    async def send_message(
        db: AsyncSession,
        workspace_id: uuid.UUID,
        conversation_id: uuid.UUID,
        text: str,
        media_url: Optional[str] = None
    ) -> Message:
        conversation = (await db.execute(select(Conversation).where(
            Conversation.id == conversation_id, Conversation.workspace_id == workspace_id))).scalar_one_or_none()
        if not conversation:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Conversation not found in this workspace.")
        account = (await db.execute(select(InstagramAccount).where(
            InstagramAccount.id == conversation.instagram_account_id,
            InstagramAccount.workspace_id == workspace_id,
            InstagramAccount.is_active == True))).scalar_one_or_none()  # noqa: E712
        contact = (await db.execute(select(Contact).where(
            Contact.id == conversation.contact_id, Contact.workspace_id == workspace_id))).scalar_one_or_none()
        if not account or not contact:
            raise HTTPException(status.HTTP_409_CONFLICT, "Instagram account or contact is no longer available.")

        # 24-hour customer service window validation
        if contact.last_interaction_at:
            last_dt = contact.last_interaction_at
            now_dt = datetime.now(timezone.utc) if last_dt.tzinfo is not None else datetime.utcnow()
            if (now_dt - last_dt).total_seconds() > 24 * 3600:
                raise HTTPException(
                    status.HTTP_422_UNPROCESSABLE_ENTITY,
                    "This person can't be messaged right now (outside Instagram's 24-hour messaging window)."
                )

        try:
            token = decrypt_token(account.access_token_encrypted)
        except Exception:
            raise HTTPException(status.HTTP_409_CONFLICT, "Stored token is unreadable. Reconnect the Instagram account.")

        result = {}
        if token and not token.startswith("mock_"):
            try:
                messaging = InstagramMessaging(MetaGraphClient(token))
                result = await messaging.send_direct_message(contact.ig_user_id, text)
            except MetaTokenExpiredError:
                raise HTTPException(status.HTTP_409_CONFLICT, "Instagram token expired. Reconnect the account.")
            except MetaRateLimitError:
                raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS, "Instagram rate limit reached. Try again shortly.")
            except MetaGraphAPIError as e:
                if getattr(e, "code", 0) in (10, 551):
                    raise HTTPException(
                        status.HTTP_422_UNPROCESSABLE_ENTITY,
                        "This person can't be messaged right now (outside Instagram's 24-hour messaging window)."
                    )
                raise HTTPException(status.HTTP_502_BAD_GATEWAY, f"Instagram rejected the message: {e}")

        message_id = result.get("message_id") if isinstance(result, dict) else None
        message = Message(
            workspace_id=workspace_id,
            conversation_id=conversation.id,
            sender_type="INSTAGRAM_ACCOUNT",
            text=text,
            media_url=media_url,
            meta_message_id=message_id
        )
        db.add(message)
        conversation.last_message_text = text
        conversation.last_message_at = datetime.utcnow()
        conversation.unread_count = 0
        conversation.status = "REPLIED"
        await db.commit()
        await db.refresh(message)
        return message
