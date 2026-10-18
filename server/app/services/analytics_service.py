# server/app/services/analytics_service.py
import uuid
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, case
from app.models import AnalyticsEvent, Automation, Contact, WebhookEvent, Message, PostUsage


def _normalize_dt(dt: Optional[datetime]) -> Optional[datetime]:
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


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

        # Automation table cumulative stats
        stmt_stats = select(
            func.sum(Automation.stats_comments),
            func.sum(Automation.stats_dms_sent),
            func.sum(Automation.stats_clicks)
        ).where(Automation.workspace_id == workspace_id)
        auto_comments, auto_dms, auto_clicks = (await db.execute(stmt_stats)).first() or (0, 0, 0)

        # Real message counts from Message table (outgoing DMs delivered by bot or connected account)
        stmt_real_dms = select(func.count(Message.id)).where(
            Message.workspace_id == workspace_id,
            Message.sender_type.in_(["BOT", "INSTAGRAM_ACCOUNT"])
        )
        res_real_dms = await db.execute(stmt_real_dms)
        real_dms_count = res_real_dms.scalar() or 0

        # Real post usage DMs
        stmt_post_usage = select(func.sum(PostUsage.dms_delivered_count)).where(
            PostUsage.workspace_id == workspace_id
        )
        res_post_usage = await db.execute(stmt_post_usage)
        post_usage_dms = res_post_usage.scalar() or 0

        # Real comment webhook events processed
        stmt_comment_events = select(func.count(WebhookEvent.id)).where(
            WebhookEvent.workspace_id == workspace_id,
            WebhookEvent.event_type.in_(["COMMENT", "COMMENTS", "FEED"])
        )
        res_comment_events = await db.execute(stmt_comment_events)
        comment_events_count = res_comment_events.scalar() or 0

        # Final authoritative totals
        total_dms = max(int(auto_dms or 0), int(real_dms_count or 0), int(post_usage_dms or 0))
        total_comments = max(int(auto_comments or 0), int(comment_events_count or 0))
        total_clicks = int(auto_clicks or 0)

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

        # ── Authoritative 7-Day Weekly Breakdown ──
        # Current week Monday -> Sunday
        now = datetime.now(timezone.utc)
        monday = (now - timedelta(days=now.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)
        seven_days_ago = (now - timedelta(days=6)).replace(hour=0, minute=0, second=0, microsecond=0)
        start_period = min(monday, seven_days_ago)

        stmt_period_msgs = select(Message.created_at).where(
            Message.workspace_id == workspace_id,
            Message.sender_type.in_(["BOT", "INSTAGRAM_ACCOUNT"]),
            Message.created_at >= start_period
        )
        res_period_msgs = await db.execute(stmt_period_msgs)
        msg_timestamps = [_normalize_dt(r[0]) for r in res_period_msgs.all() if r[0]]

        stmt_period_cmts = select(WebhookEvent.received_at).where(
            WebhookEvent.workspace_id == workspace_id,
            WebhookEvent.event_type.in_(["COMMENT", "COMMENTS", "FEED"]),
            WebhookEvent.received_at >= start_period
        )
        res_period_cmts = await db.execute(stmt_period_cmts)
        cmt_timestamps = [_normalize_dt(r[0]) for r in res_period_cmts.all() if r[0]]

        stmt_period_analytics = select(AnalyticsEvent.created_at).where(
            AnalyticsEvent.workspace_id == workspace_id,
            AnalyticsEvent.created_at >= start_period
        )
        res_period_analytics = await db.execute(stmt_period_analytics)
        analytics_timestamps = [_normalize_dt(r[0]) for r in res_period_analytics.all() if r[0]]

        # Construct 7 days (Mon -> Sun of current week)
        daily_stats: List[Dict[str, Any]] = []
        for i in range(7):
            d_start = monday + timedelta(days=i)
            d_end = d_start + timedelta(days=1)
            
            # Count in range [d_start, d_end)
            d_dms = sum(1 for t in msg_timestamps if t and d_start <= t < d_end)
            d_cmts = sum(1 for t in cmt_timestamps if t and d_start <= t < d_end)
            d_anlt = sum(1 for t in analytics_timestamps if t and d_start <= t < d_end)

            day_total = d_dms + d_cmts + d_anlt
            daily_stats.append({
                "day": d_start.strftime("%a"),
                "date": d_start.strftime("%Y-%m-%d"),
                "dms": d_dms,
                "comments": d_cmts,
                "count": day_total,
                "pct": 0
            })

        max_day_count = max((item["count"] for item in daily_stats), default=0)
        if max_day_count > 0:
            for item in daily_stats:
                item["pct"] = round((item["count"] / max_day_count) * 100)
        else:
            for item in daily_stats:
                item["pct"] = 0

        return {
            "workspace_id": str(workspace_id),
            "total_automations": total_automations,
            "active_automations": active_automations,
            "total_leads": total_leads,
            "converted_leads": converted_leads,
            "conversion_rate_pct": round(converted_leads / total_leads * 100, 1) if total_leads else 0.0,
            "stats_comments": total_comments,
            "stats_dms_sent": total_dms,
            "stats_clicks": total_clicks,
            "delivery_health": delivery_health,
            "queue_latency": queue_latency,
            "daily_stats": daily_stats,
            # Legacy keys
            "total_comments": total_comments,
            "total_dms": total_dms,
            "total_contacts": total_leads,
        }

