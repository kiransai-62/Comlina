# server/app/services/automation_service.py
from datetime import datetime, timezone
import logging
import uuid
from typing import Any, Dict, List, Optional

from fastapi import HTTPException, status
from sqlalchemy import select, update, delete, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import log_event
from app.models import Automation, AutomationVersion, InstagramAccount, Workspace
from app.schemas import AutomationCreate, AutomationUpdate
from app.services.plan_service import PlanService

logger = logging.getLogger(__name__)


class AutomationService:
    @staticmethod
    def serialize_automation(auto: Automation) -> Dict[str, Any]:
        flow = dict(auto.flow_definition or {})
        trigger = dict(flow.get("trigger") or {})
        media_id = getattr(auto, "media_id", None) or trigger.get("media_id") or trigger.get("post_id") or "ALL"
        trigger_type = getattr(auto, "trigger_type", None) or trigger.get("trigger_type") or "SPECIFIC_WORDS"
        keywords = getattr(auto, "keywords", None)
        if keywords is None:
            keywords = trigger.get("keywords", [])
        follow_condition = getattr(auto, "follow_condition", None) or flow.get("follow_condition") or {"enabled": False}
        response_config = getattr(auto, "response_config", None) or {"actions": flow.get("actions", [])}
        is_active = bool(getattr(auto, "is_active", auto.status == "ACTIVE") and auto.status == "ACTIVE")

        return {
            "id": str(auto.id),
            "workspace_id": str(auto.workspace_id),
            "user_id": str(auto.user_id) if getattr(auto, "user_id", None) else None,
            "instagram_account_id": str(auto.instagram_account_id),
            "name": auto.name,
            "automation_name": auto.name,
            "media_id": str(media_id),
            "trigger_type": trigger_type,
            "match_mode": getattr(auto, "match_mode", None) or trigger.get("match_mode", "CONTAINS"),
            "keywords": keywords,
            "follow_condition": follow_condition,
            "response_config": response_config,
            "flow_definition": flow,
            "status": auto.status,
            "is_active": is_active,
            "version": auto.version,
            "stats_triggered": auto.stats_triggered or 0,
            "stats_dms_sent": auto.stats_dms_sent or 0,
            "stats_comments_replied": auto.stats_comments_replied or 0,
            "published_at": auto.published_at.isoformat() if auto.published_at else None,
            "created_at": auto.created_at.isoformat() if auto.created_at else None,
            "updated_at": auto.updated_at.isoformat() if getattr(auto, "updated_at", None) else None,
        }

    @classmethod
    def validate_and_normalize_payload(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        name = str(data.get("automation_name") or data.get("name") or "").strip()
        if not name:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Automation name is required.",
            )

        flow = dict(data.get("flow_definition") or {})
        trigger = dict(flow.get("trigger") or {})
        conditions = list(flow.get("conditions") or [])
        actions = list(flow.get("actions") or [])

        # 1. Media ID normalization
        media_id = str(
            data.get("media_id")
            or trigger.get("media_id")
            or trigger.get("post_id")
            or flow.get("selectedPostId")
            or "ALL"
        ).strip()
        if flow.get("postSelection") == "all" or not media_id:
            media_id = "ALL"

        # 2. Trigger Type normalization (SPECIFIC_WORDS vs ANY_WORD)
        raw_trigger = str(
            data.get("trigger_type")
            or trigger.get("trigger_type")
            or trigger.get("match_type")
            or trigger.get("type")
            or "SPECIFIC_WORDS"
        ).strip().upper()

        if raw_trigger in ("ANY_WORD", "ANY", "COMMENT_ANY", "ALL_COMMENTS"):
            trigger_type = "ANY_WORD"
        elif raw_trigger in ("SPECIFIC_WORDS", "COMMENT_KEYWORD", "KEYWORD", "KEYWORDS"):
            trigger_type = "SPECIFIC_WORDS"
        else:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Unsupported trigger_type '{raw_trigger}'. Must be SPECIFIC_WORDS or ANY_WORD.",
            )

        match_mode = str(
            data.get("match_mode")
            or trigger.get("match_mode")
            or "CONTAINS"
        ).strip().upper()
        if match_mode not in ("CONTAINS", "EXACT"):
            match_mode = "CONTAINS"

        # 3. Keywords validation
        raw_kw = data.get("keywords") if "keywords" in data else trigger.get("keywords", [])
        if isinstance(raw_kw, str):
            keywords = [k.strip() for k in raw_kw.split(",") if k.strip()]
        elif isinstance(raw_kw, list):
            keywords = [str(k).strip() for k in raw_kw if str(k).strip()]
        else:
            keywords = []

        if trigger_type == "SPECIFIC_WORDS" and not keywords:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="At least one non-empty keyword is required for SPECIFIC_WORDS trigger.",
            )

        # 4. Follow condition normalization
        follow_cond = dict(data.get("follow_condition") or flow.get("follow_condition") or {})
        if not follow_cond:
            for c in conditions:
                if c.get("type") in ("IS_FOLLOWER", "FOLLOW_CHECK", "FOLLOW_THE_PAGE"):
                    follow_cond = {
                        "enabled": bool(c.get("enabled", True)),
                        "mode": c.get("mode", "FOLLOW_TO_UNLOCK"),
                        "prompt_message": c.get("prompt_message")
                        or "Please follow our Instagram page first, then tap the button below to unlock your DM!",
                        "button_title": c.get("button_title") or "I'm Following ✅",
                    }
                    break

        follow_enabled = bool(follow_cond.get("enabled", False))
        follow_cond["enabled"] = follow_enabled
        if follow_enabled:
            follow_cond.setdefault(
                "prompt_message",
                "Please follow our Instagram page first, then tap the button below to receive your link!",
            )
            follow_cond.setdefault("button_title", "I'm Following ✅")
            if not any(c.get("type") in ("IS_FOLLOWER", "FOLLOW_CHECK") for c in conditions):
                conditions.append({
                    "type": "IS_FOLLOWER",
                    "enabled": True,
                    "prompt_message": follow_cond["prompt_message"],
                    "button_title": follow_cond["button_title"],
                })
        else:
            conditions = [
                c for c in conditions if c.get("type") not in ("IS_FOLLOWER", "FOLLOW_CHECK", "FOLLOW_THE_PAGE")
            ]

        # 5. Response / Actions normalization
        response_config = dict(data.get("response_config") or {})
        if not actions and response_config:
            if response_config.get("comment_reply") or response_config.get("public_reply_text"):
                actions.append({
                    "type": "REPLY_COMMENT",
                    "text": (response_config.get("comment_reply") or response_config.get("public_reply_text")).strip(),
                })
            if response_config.get("dm_text") or response_config.get("message"):
                actions.append({
                    "type": "SEND_DM",
                    "text": (response_config.get("dm_text") or response_config.get("message")).strip(),
                    "buttons": response_config.get("buttons") or [],
                })

        if not actions:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="At least one response action (SEND_DM or REPLY_COMMENT) must be configured.",
            )

        if not response_config:
            response_config = {"actions": actions}

        # Sync canonical flow_definition
        trigger.update({
            "type": "COMMENT_ANY" if trigger_type == "ANY_WORD" else "COMMENT_KEYWORD",
            "trigger_type": trigger_type,
            "match_mode": match_mode,
            "media_id": media_id,
            "post_id": None if media_id == "ALL" else media_id,
            "keywords": keywords,
            "case_sensitive": False,
        })
        flow["trigger"] = trigger
        flow["conditions"] = conditions
        flow["actions"] = actions
        flow["follow_condition"] = follow_cond

        is_active = data.get("is_active")
        raw_status = str(data.get("status") or "").upper()
        if is_active is False or raw_status in ("PAUSED", "DRAFT", "DISABLED"):
            final_is_active = False
            final_status = "PAUSED" if raw_status == "PAUSED" else "DRAFT"
        else:
            final_is_active = True
            final_status = "ACTIVE"

        return {
            "name": name,
            "media_id": media_id,
            "trigger_type": trigger_type,
            "match_mode": match_mode,
            "keywords": keywords,
            "follow_condition": follow_cond,
            "response_config": response_config,
            "flow_definition": flow,
            "is_active": final_is_active,
            "status": final_status,
        }

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

    @classmethod
    async def create_automation(
        cls,
        db: AsyncSession,
        workspace_id: uuid.UUID,
        user_id: Optional[uuid.UUID] = None,
        data: Any = None,
        max_automations: int = 10,
        correlation_id: Optional[str] = None,
    ) -> Automation:
        # Handle parameter shift if called as create_automation(db, workspace_id, data=...)
        if data is None and user_id is not None and not isinstance(user_id, uuid.UUID):
            data = user_id
            user_id = None

        if data is None:
            raise HTTPException(status_code=400, detail="Automation data is required.")

        # If data is schema model (from API route):
        if isinstance(data, AutomationCreate):
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

            stmt_count = select(func.count(Automation.id)).where(Automation.workspace_id == workspace_id)
            res_count = await db.execute(stmt_count)
            current_count = res_count.scalar() or 0
            if current_count >= max_automations:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Automation limit reached ({max_automations}). Upgrade your plan to create more automations."
                )

            flow_dict = data.flow_definition.model_dump()
            trigger = flow_dict.get("trigger", {}) if isinstance(flow_dict.get("trigger"), dict) else {}
            trigger_mode = flow_dict.get("triggerMode") or trigger.get("triggerMode")
            if trigger_mode is not None:
                trigger_mode_str = str(trigger_mode).strip().lower()
                if trigger_mode_str not in ("specific_keywords", "any_keyword"):
                    raise HTTPException(
                        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                        detail="Invalid triggerMode. Must be 'specific_keywords' or 'any_keyword'."
                    )

            stmt_ws = select(Workspace).where(Workspace.id == workspace_id)
            res_ws = await db.execute(stmt_ws)
            workspace = res_ws.scalar_one_or_none()
            if workspace:
                is_valid, error_msg = PlanService.validate_automation_features(workspace, flow_dict)
                if not is_valid:
                    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=error_msg)

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
                        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=quota_err)

            media_id_val = str(trigger.get("selectedPostId") or trigger.get("postId") or trigger.get("post_id") or "ALL")
            trig_type_val = str(data.trigger_type or "SPECIFIC_WORDS")
            match_mode_val = "CONTAINS"
            keywords_val = trigger.get("keywords") or []
            if isinstance(keywords_val, str):
                keywords_val = [k.strip() for k in keywords_val.split(",") if k.strip()]
            follow_cond_val = flow_dict.get("follow_condition") or {"enabled": False}

            automation = Automation(
                workspace_id=workspace_id,
                user_id=user_id,
                instagram_account_id=data.instagram_account_id,
                name=data.name,
                description=data.description,
                status="DRAFT",
                media_id=media_id_val,
                trigger_type=trig_type_val,
                match_mode=match_mode_val,
                keywords=keywords_val,
                follow_condition=follow_cond_val,
                response_config={"actions": flow_dict.get("actions", [])},
                flow_definition=flow_dict,
                is_active=False,
                version=1
            )
            db.add(automation)
            await db.commit()
            await db.refresh(automation)
            return automation

        # Otherwise data is Dict / normalized payload:
        data_dict = dict(data)
        ig_acc_raw = data_dict.get("instagram_account_id")
        if not ig_acc_raw:
            raise HTTPException(status_code=400, detail="instagram_account_id is required.")

        try:
            ig_acc_uuid = uuid.UUID(str(ig_acc_raw))
        except ValueError:
            raise HTTPException(status_code=400, detail="instagram_account_id must be a valid UUID.")

        acct = (
            await db.execute(
                select(InstagramAccount).where(
                    InstagramAccount.id == ig_acc_uuid,
                    InstagramAccount.workspace_id == workspace_id,
                )
            )
        ).scalar_one_or_none()
        if not acct:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Connected Instagram account not found in this workspace.",
            )

        normalized = cls.validate_and_normalize_payload(data_dict)

        existing = (
            await db.execute(
                select(Automation).where(
                    Automation.workspace_id == workspace_id,
                    Automation.instagram_account_id == acct.id,
                    Automation.name == normalized["name"],
                    Automation.media_id == normalized["media_id"],
                    Automation.trigger_type == normalized["trigger_type"],
                )
            )
        ).scalar_one_or_none()

        now = datetime.now(timezone.utc)
        if existing:
            existing.keywords = normalized["keywords"]
            existing.match_mode = normalized["match_mode"]
            existing.follow_condition = normalized["follow_condition"]
            existing.response_config = normalized["response_config"]
            existing.flow_definition = normalized["flow_definition"]
            existing.is_active = normalized["is_active"]
            existing.status = normalized["status"]
            existing.version = (existing.version or 1) + 1
            if normalized["is_active"]:
                existing.published_at = now
            await db.commit()
            await db.refresh(existing)
            log_event(
                logger,
                "DATABASE_UPDATE",
                status="SUCCESS_IDEMPOTENT",
                correlation_id=correlation_id,
                table="automations",
                automation_id=str(existing.id),
            )
            return existing

        automation = Automation(
            workspace_id=workspace_id,
            user_id=user_id,
            instagram_account_id=acct.id,
            name=normalized["name"],
            media_id=normalized["media_id"],
            trigger_type=normalized["trigger_type"],
            match_mode=normalized["match_mode"],
            keywords=normalized["keywords"],
            follow_condition=normalized["follow_condition"],
            response_config=normalized["response_config"],
            flow_definition=normalized["flow_definition"],
            status=normalized["status"],
            is_active=normalized["is_active"],
            version=1,
            published_at=now if normalized["is_active"] else None,
        )
        db.add(automation)
        await db.flush()

        db.add(
            AutomationVersion(
                automation_id=automation.id,
                workspace_id=workspace_id,
                version=1,
                flow_definition=normalized["flow_definition"],
                published_by=user_id,
            )
        )
        await db.commit()
        await db.refresh(automation)

        log_event(
            logger,
            "DATABASE_INSERT",
            status="SUCCESS",
            correlation_id=correlation_id,
            table="automations",
            automation_id=str(automation.id),
            media_id=automation.media_id,
            trigger_type=automation.trigger_type,
            is_active=automation.is_active,
        )
        return automation

    @classmethod
    async def update_automation(
        cls,
        db: AsyncSession,
        workspace_id: uuid.UUID,
        automation_id: uuid.UUID,
        data: Any,
        user_id: Optional[uuid.UUID] = None,
        correlation_id: Optional[str] = None,
    ) -> Automation:
        automation = await cls.get_automation(db, workspace_id, automation_id)
        if not automation:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Automation not found")

        # Case 1: Pydantic AutomationUpdate model (from existing API)
        if isinstance(data, AutomationUpdate):
            stmt_ws = select(Workspace).where(Workspace.id == workspace_id)
            res_ws = await db.execute(stmt_ws)
            workspace = res_ws.scalar_one_or_none()

            if data.flow_definition is not None and workspace:
                flow_dict = data.flow_definition.model_dump()
                trigger = flow_dict.get("trigger", {}) if isinstance(flow_dict.get("trigger"), dict) else {}
                trigger_mode = flow_dict.get("triggerMode") or trigger.get("triggerMode")
                if trigger_mode is not None:
                    trigger_mode_str = str(trigger_mode).strip().lower()
                    if trigger_mode_str not in ("specific_keywords", "any_keyword"):
                        raise HTTPException(
                            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                            detail="Invalid triggerMode. Must be 'specific_keywords' or 'any_keyword'."
                        )

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
                if media_id:
                    automation.media_id = str(media_id)

            if data.name is not None:
                automation.name = data.name
            if data.description is not None:
                automation.description = data.description
            if data.trigger_type is not None:
                automation.trigger_type = data.trigger_type
            if data.instagram_account_id is not None:
                stmt_ig = select(InstagramAccount).where(
                    InstagramAccount.id == data.instagram_account_id,
                    InstagramAccount.workspace_id == workspace_id
                )
                res_ig = await db.execute(stmt_ig)
                if not res_ig.scalar_one_or_none():
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="Instagram account not found or does not belong to this workspace"
                    )
                automation.instagram_account_id = data.instagram_account_id
            if data.status is not None:
                automation.status = data.status
                automation.is_active = data.status == "ACTIVE"
                if data.status == "ACTIVE" and not automation.published_at:
                    automation.published_at = datetime.now(timezone.utc)
                if isinstance(automation.flow_definition, dict):
                    flow_copy = dict(automation.flow_definition)
                    flow_copy["status"] = data.status
                    automation.flow_definition = flow_copy

            await db.commit()
            await db.refresh(automation)
            return automation

        # Case 2: Dict payload (Phase 3 API)
        data_dict = dict(data)
        if set(data_dict.keys()).issubset({"is_active", "status"}):
            if "is_active" in data_dict:
                automation.is_active = bool(data_dict["is_active"])
                automation.status = "ACTIVE" if automation.is_active else "PAUSED"
            elif "status" in data_dict:
                st = str(data_dict["status"]).upper()
                automation.status = st
                automation.is_active = st == "ACTIVE"
            if automation.is_active and not automation.published_at:
                automation.published_at = datetime.now(timezone.utc)
        else:
            merged = {
                "name": data_dict.get("automation_name") or data_dict.get("name") or automation.name,
                "media_id": data_dict.get("media_id", automation.media_id),
                "trigger_type": data_dict.get("trigger_type", automation.trigger_type),
                "match_mode": data_dict.get("match_mode", getattr(automation, "match_mode", "CONTAINS")),
                "keywords": data_dict.get("keywords", automation.keywords),
                "follow_condition": data_dict.get("follow_condition", automation.follow_condition),
                "response_config": data_dict.get("response_config", automation.response_config),
                "flow_definition": data_dict.get("flow_definition", automation.flow_definition),
                "is_active": data_dict.get("is_active", automation.is_active),
                "status": data_dict.get("status", automation.status),
            }
            normalized = cls.validate_and_normalize_payload(merged)
            automation.name = normalized["name"]
            automation.media_id = normalized["media_id"]
            automation.trigger_type = normalized["trigger_type"]
            automation.match_mode = normalized["match_mode"]
            automation.keywords = normalized["keywords"]
            automation.follow_condition = normalized["follow_condition"]
            automation.response_config = normalized["response_config"]
            automation.flow_definition = normalized["flow_definition"]
            automation.is_active = normalized["is_active"]
            automation.status = normalized["status"]
            automation.version = (automation.version or 1) + 1
            if automation.is_active:
                automation.published_at = datetime.now(timezone.utc)

        await db.commit()
        await db.refresh(automation)

        log_event(
            logger,
            "DATABASE_UPDATE",
            status="SUCCESS",
            correlation_id=correlation_id,
            table="automations",
            automation_id=str(automation.id),
            is_active=automation.is_active,
            automation_status=automation.status,
        )
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

        new_version = automation.version + 1
        automation.version = new_version
        automation.status = "ACTIVE"
        automation.is_active = True
        automation.published_at = datetime.now(timezone.utc)

        snapshot = AutomationVersion(
            automation_id=automation.id,
            workspace_id=workspace_id,
            version=new_version,
            trigger_type=automation.trigger_type,
            flow_definition=automation.flow_definition,
            published_by=published_by,
            published_at=datetime.now(timezone.utc)
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
