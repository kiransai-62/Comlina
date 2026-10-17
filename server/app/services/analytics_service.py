# server/app/services/analytics_service.py
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, case
from app.models import AnalyticsEvent, Automation, Contact, WebhookEvent

class AnalyticsService:
    @staticmethod
    async def get_dashboard_summary(db: AsyncSession, workspace_id: uuid.UUID) -> Dict[str, Any]:
        # Count total automations
        stmt_auto = select(func.count(Automation.id)).where(Automation.workspace_id == workspace_id)
        res_auto = await db.execute(stmt_auto)
        total_automations = res_auto.scalar() or 0

        # Count active automations
        stmt_active = select(func.count(Automation.id)).where(
            Automation.workspace_id == workspace_id,
            Automation.status == "ACTIVE"
        )
        res_active = await db.execute(stmt_active)
        active_automations = res_active.scalar() or 0

        # Count contacts
        stmt_contacts = select(
            func.count(Contact.id),
            func.sum(case((Contact.is_converted == True, 1), else_=0))  # noqa: E712
        ).where(Contact.workspace_id == workspace_id)
        total_leads, converted_leads = (await db.execute(stmt_contacts)).first() or (0, 0)
        total_leads = total_leads or 0
        converted_leads = int(converted_leads or 0)

        stmt_stats = select(
            func.sum(Automation.stats_comments),
            func.sum(Automation.stats_dms_sent),
            func.sum(Automation.stats_clicks)
        ).where(Automation.workspace_id == workspace_id)
        comments, dms, clicks = (await db.execute(stmt_stats)).first() or (0, 0, 0)

        # Delivery health & Queue latency from WebhookEvent
        stmt_events = select(
            func.count(WebhookEvent.id),
            func.sum(case((WebhookEvent.status == "PROCESSED", 1), else_=0))
        ).where(WebhookEvent.workspace_id == workspace_id)
        total_events, processed_events = (await db.execute(stmt_events)).first() or (0, 0)
        total_events = total_events or 0
        processed_events = int(processed_events or 0)
        delivery_health = round((processed_events / total_events) * 100, 1) if total_events > 0 else 100.0

        stmt_lat = select(WebhookEvent.received_at, WebhookEvent.processed_at).where(
            WebhookEvent.workspace_id == workspace_id,
            WebhookEvent.status == "PROCESSED",
            WebhookEvent.processed_at.is_not(None)
        ).order_by(WebhookEvent.received_at.desc()).limit(20)
        res_lat = await db.execute(stmt_lat)
        latencies = []
        for recv, proc in res_lat.all():
            if recv and proc:
                delta = (proc - recv).total_seconds()
                if delta >= 0:
                    latencies.append(delta)
        queue_latency = round(sum(latencies) / len(latencies), 2) if latencies else None

        return {
            "workspace_id": str(workspace_id),
            "total_automations": total_automations,
            "active_automations": active_automations,
            "total_leads": total_leads,
            "converted_leads": converted_leads,
            "conversion_rate_pct": round(converted_leads / total_leads * 100, 1) if total_leads else 0.0,
            "stats_comments": int(comments or 0),
            "stats_dms_sent": int(dms or 0),
            "stats_clicks": int(clicks or 0),
            "delivery_health": delivery_health,
            "queue_latency": queue_latency,
            # Legacy keys
            "total_comments": int(comments or 0),
            "total_dms": int(dms or 0),
            "total_contacts": total_leads,
        }
