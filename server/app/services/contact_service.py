# server/app/services/contact_service.py
import uuid
import io
import csv
from typing import Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from app.models import Contact
from app.schemas import ContactCreate

class ContactService:
    @staticmethod
    async def list_contacts(
        db: AsyncSession,
        workspace_id: uuid.UUID,
        tag: Optional[str] = None,
        follower_status: Optional[str] = None,
        is_converted: Optional[bool] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Contact]:
        stmt = select(Contact).where(Contact.workspace_id == workspace_id)
        if follower_status:
            stmt = stmt.where(Contact.follower_status == follower_status)
        if is_converted is not None:
            stmt = stmt.where(Contact.is_converted == is_converted)

        stmt = stmt.order_by(Contact.last_interaction_at.desc())

        if tag:
            res = await db.execute(stmt)
            contacts = [c for c in res.scalars().all() if tag in (c.tags or [])]
            return contacts[offset:offset + limit]

        stmt = stmt.limit(limit).offset(offset)
        res = await db.execute(stmt)
        return list(res.scalars().all())

    @staticmethod
    async def create_or_update_contact(
        db: AsyncSession,
        workspace_id: uuid.UUID,
        instagram_account_id: uuid.UUID,
        ig_user_id: str,
        username: str,
        follower_status: str = "UNKNOWN",
        tag: Optional[str] = None
    ) -> Contact:
        stmt = select(Contact).where(
            Contact.workspace_id == workspace_id,
            Contact.instagram_account_id == instagram_account_id,
            Contact.ig_user_id == ig_user_id
        )
        res = await db.execute(stmt)
        contact = res.scalar_one_or_none()

        if contact:
            contact.username = username
            if follower_status != "UNKNOWN":
                contact.follower_status = follower_status
            contact.interaction_count += 1
            if tag and tag not in (contact.tags or []):
                contact.tags = list(contact.tags or []) + [tag]
        else:
            contact = Contact(
                workspace_id=workspace_id,
                instagram_account_id=instagram_account_id,
                ig_user_id=ig_user_id,
                username=username,
                follower_status=follower_status,
                tags=[tag] if tag else ["lead"]
            )
            db.add(contact)

        await db.commit()
        await db.refresh(contact)
        return contact

    @staticmethod
    def _sanitize_csv_cell(value: Any) -> Any:
        if value is None:
            return ""
        s = str(value)
        # Prevent CSV formula injection (OWASP: CWE-1236)
        if s.startswith(("=", "+", "-", "@", "\t", "\r", "%")):
            return f"'{s}"
        return s

    @staticmethod
    def export_contacts_csv(contacts: List[Contact]) -> str:
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["ID", "Username", "Full Name", "Email", "Follower Status", "Converted", "Interactions", "Tags"])
        for c in contacts:
            tags_str = ", ".join(c.tags or [])
            row = [
                ContactService._sanitize_csv_cell(c.id),
                ContactService._sanitize_csv_cell(c.username),
                ContactService._sanitize_csv_cell(c.full_name or ""),
                ContactService._sanitize_csv_cell(c.email or ""),
                ContactService._sanitize_csv_cell(c.follower_status),
                c.is_converted,
                c.interaction_count,
                ContactService._sanitize_csv_cell(tags_str)
            ]
            writer.writerow(row)
        return output.getvalue()
