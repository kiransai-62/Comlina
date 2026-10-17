# server/app/services/automation_service.py
import uuid
from datetime import datetime
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func
from fastapi import HTTPException, status
from app.models import Automation, AutomationVersion, InstagramAccount, Workspace
from app.schemas import AutomationCreate, AutomationUpdate
from app.services.plan_service import PlanService

class AutomationService:
    @staticmethod
    async def list_automations(
        db: AsyncSession,
        workspace_id: uuid.UUID,
        limit: int = 50,
        offset: int = 0
    ) -> List[Automation]:
        stmt = (
            select(Automation)
            .where(Automation.workspace_id == workspace_id)
            .order_by(Automation.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        res = await db.execute(stmt)
        return list(res.scalars().all())

    @staticmethod
    async def get_automation(db: AsyncSession, workspace_id: uuid.UUID, automation_id: uuid.UUID) -> Optional[Automation]:
        stmt = select(Automation).where(
            Automation.workspace_id == workspace_id,
            Automation.id == automation_id
        )
        res = await db.execute(stmt)
        return res.scalar_one_or_none()

    @staticmethod
    async def create_automation(
        db: AsyncSession,
        workspace_id: uuid.UUID,
        data: AutomationCreate,
        max_automations: int = 10
    ) -> Automation:
        # 1. Broken Object Level Authorization (BOLA) Check:
        # Ensure target Instagram account belongs to caller's workspace
        stmt_acc = select(InstagramAccount).where(
            InstagramAccount.id == data.instagram_account_id,
            InstagramAccount.workspace_id == workspace_id,
            InstagramAccount.is_active == True
        )
        res_acc = await db.execute(stmt_acc)
        account = res_acc.scalar_one_or_none()
        if not account:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Instagram account not found or does not belong to this workspace."
            )

        # 2. Plan Quota Authorization Check:
        stmt_count = select(func.count(Automation.id)).where(Automation.workspace_id == workspace_id)
        res_count = await db.execute(stmt_count)
        current_count = res_count.scalar() or 0
        if current_count >= max_automations:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Automation limit reached ({max_automations}). Upgrade your plan to create more automations."
            )

        # 3. Plan-Based Feature Validation:
        flow_dict = data.flow_definition.model_dump()
        stmt_ws = select(Workspace).where(Workspace.id == workspace_id)
        res_ws = await db.execute(stmt_ws)
        workspace = res_ws.scalar_one_or_none()
        if workspace:
            is_valid, error_msg = PlanService.validate_automation_features(workspace, flow_dict)
            if not is_valid:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=error_msg
                )

            # Check post quota if specific post is targeted
            trigger = flow_dict.get("trigger", {})
            media_id = (
                trigger.get("selectedPostId")
                or trigger.get("postId")
                or trigger.get("post_id")
            )
            if media_id and str(media_id).strip().lower() not in ("all", "", "none"):
                quota_ok, quota_err = await PlanService.check_and_register_post_quota(
                    workspace, str(media_id).strip(), db, data.instagram_account_id
                )
                if not quota_ok:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=quota_err
                    )

        automation = Automation(
            workspace_id=workspace_id,
            instagram_account_id=data.instagram_account_id,
            name=data.name,
            description=data.description,
            status="DRAFT",
            trigger_type=data.trigger_type,
            flow_definition=flow_dict,
            version=1
        )
        db.add(automation)
        await db.commit()
        await db.refresh(automation)
        return automation

    @staticmethod
    async def update_automation(
        db: AsyncSession,
        workspace_id: uuid.UUID,
        automation_id: uuid.UUID,
        data: AutomationUpdate
    ) -> Automation:
        automation = await AutomationService.get_automation(db, workspace_id, automation_id)
        if not automation:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Automation not found")

        stmt_ws = select(Workspace).where(Workspace.id == workspace_id)
        res_ws = await db.execute(stmt_ws)
        workspace = res_ws.scalar_one_or_none()

        if data.flow_definition is not None and workspace:
            flow_dict = data.flow_definition.model_dump()
            is_valid, error_msg = PlanService.validate_automation_features(workspace, flow_dict)
            if not is_valid:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=error_msg)

            trigger = flow_dict.get("trigger", {})
            media_id = (
                trigger.get("selectedPostId")
                or trigger.get("postId")
                or trigger.get("post_id")
            )
            if media_id and str(media_id).strip().lower() not in ("all", "", "none"):
                quota_ok, quota_err = await PlanService.check_and_register_post_quota(
                    workspace, str(media_id).strip(), db, automation.instagram_account_id
                )
                if not quota_ok:
                    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=quota_err)

            automation.flow_definition = flow_dict

        if data.name is not None:
            automation.name = data.name
        if data.description is not None:
            automation.description = data.description
        if data.status is not None:
            automation.status = data.status

        await db.commit()
        await db.refresh(automation)
        return automation

    @staticmethod
    async def publish_automation(
        db: AsyncSession,
        workspace_id: uuid.UUID,
        automation_id: uuid.UUID,
        published_by: Optional[uuid.UUID] = None
    ) -> Automation:
        automation = await AutomationService.get_automation(db, workspace_id, automation_id)
        if not automation:
            raise ValueError("Automation not found")

        # Increment version and create immutable snapshot in automation_versions
        new_version = automation.version + 1
        automation.version = new_version
        automation.status = "ACTIVE"
        automation.published_at = datetime.utcnow()

        snapshot = AutomationVersion(
            automation_id=automation.id,
            workspace_id=workspace_id,
            version=new_version,
            trigger_type=automation.trigger_type,
            flow_definition=automation.flow_definition,
            published_by=published_by,
            published_at=datetime.utcnow()
        )
        db.add(snapshot)
        await db.commit()
        await db.refresh(automation)
        return automation

    @staticmethod
    async def delete_automation(db: AsyncSession, workspace_id: uuid.UUID, automation_id: uuid.UUID) -> bool:
        stmt = delete(Automation).where(
            Automation.workspace_id == workspace_id,
            Automation.id == automation_id
        )
        res = await db.execute(stmt)
        await db.commit()
        return res.rowcount > 0
