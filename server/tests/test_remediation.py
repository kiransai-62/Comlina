import unittest
import uuid
from app.integrations.instagram.oauth import IG_SCOPES, MetaOAuth
from app.integrations.instagram.client import MetaGraphClient
from worker.app.integrations.instagram.client import MetaGraphClient as WorkerMetaGraphClient
from app.api.instagram import _normalize_media_item
from app.schemas import MessageCreate, ConversationOut
from app.core.database import resolve_database_url, SQLITE_DEV_URL
from worker.app.core.database import resolve_database_url as worker_resolve_database_url
from worker.app.main import WorkerSettings
from worker.app.jobs.refresh_tokens import refresh_expiring_tokens_job

class TestRemediation(unittest.IsolatedAsyncioTestCase):
    def test_meta_oauth_scopes(self):
        # Must include content_publish, basic, manage_messages, manage_comments
        self.assertIn("instagram_business_basic", IG_SCOPES)
        self.assertIn("instagram_business_manage_messages", IG_SCOPES)
        self.assertIn("instagram_business_manage_comments", IG_SCOPES)
        self.assertIn("instagram_business_content_publish", IG_SCOPES)

    def test_meta_graph_client_base_url_instagram(self):
        # Default Instagram token
        client = MetaGraphClient("IGQVJ...")
        self.assertTrue(client.base_url.startswith("https://graph.instagram.com/"))

        # Meta long-lived tokens from Instagram Login (often prefixed with EAA) must default to graph.instagram.com
        eaa_client = MetaGraphClient("EAAB...")
        self.assertTrue(eaa_client.base_url.startswith("https://graph.instagram.com/"))

        # Explicit custom base_url is honored
        fb_client = MetaGraphClient("EAAB...", base_url="https://graph.facebook.com/v21.0")
        self.assertTrue(fb_client.base_url.startswith("https://graph.facebook.com/"))

    def test_worker_meta_graph_client_base_url(self):
        client = WorkerMetaGraphClient("IGQVJ...")
        self.assertTrue(client.base_url.startswith("https://graph.instagram.com/"))

        eaa_client = WorkerMetaGraphClient("EAAB...")
        self.assertTrue(eaa_client.base_url.startswith("https://graph.instagram.com/"))

        fb_client = WorkerMetaGraphClient("EAAB...", base_url="https://graph.facebook.com/v21.0")
        self.assertTrue(fb_client.base_url.startswith("https://graph.facebook.com/"))

    def test_database_url_resolution(self):
        pg_url = "postgresql+asyncpg://postgres:postgres@localhost:5432/comlina"
        # When PostgreSQL is unreachable in dev, resolves to SQLite
        res_server = resolve_database_url(pg_url, "development")
        self.assertTrue(res_server.startswith("sqlite+aiosqlite:///"))

        res_worker = worker_resolve_database_url(pg_url, "development")
        self.assertTrue(res_worker.startswith("sqlite+aiosqlite:///"))

        # In production, never falls back
        prod_res = resolve_database_url(pg_url, "production")
        self.assertEqual(prod_res, pg_url)

    def test_normalize_media_item(self):
        raw = {
            "id": "1790012345678",
            "caption": "Test post caption",
            "media_type": "VIDEO",
            "media_product_type": "REELS",
            "media_url": "https://cdn.example.com/video.mp4",
            "thumbnail_url": "https://cdn.example.com/thumb.jpg",
            "permalink": "https://instagr.am/p/12345",
            "timestamp": "2026-10-15T12:00:00+0000",
            "like_count": 42,
            "comments_count": 7
        }
        item = _normalize_media_item(raw)
        self.assertEqual(item["id"], "1790012345678")
        self.assertEqual(item["type"], "REEL")
        self.assertEqual(item["caption"], "Test post caption")
        self.assertEqual(item["imageUrl"], "https://cdn.example.com/thumb.jpg")
        self.assertEqual(item["likesCount"], 42)
        self.assertEqual(item["commentsCount"], 7)
        self.assertEqual(item["permalink"], "https://instagr.am/p/12345")

    def test_message_create_schema(self):
        msg = MessageCreate(text="Hello world!", media_url="https://example.com/image.jpg")
        self.assertEqual(msg.text, "Hello world!")
        self.assertEqual(msg.media_url, "https://example.com/image.jpg")

    def test_conversation_out_enriched_schema(self):
        from datetime import datetime, timezone
        conv = ConversationOut(
            id=uuid.uuid4(),
            contact_id=uuid.uuid4(),
            status="OPEN",
            last_message_at=datetime.now(timezone.utc),
            unread_count=0,
            contact_username="alice",
            name="Alice Walker",
            followers=150,
            followed_you=True,
            tags=["vip", "lead"],
            notes="Interested in coaching",
            first_seen=datetime.now(timezone.utc)
        )
        self.assertEqual(conv.contact_username, "alice")
        self.assertEqual(conv.name, "Alice Walker")
        self.assertTrue(conv.followed_you)
        self.assertEqual(conv.tags, ["vip", "lead"])

    def test_worker_settings_functions(self):
        func_names = [f.__name__ for f in WorkerSettings.functions]
        self.assertIn("refresh_expiring_tokens_job", func_names)

    async def test_analytics_summary_keys(self):
        from app.services.analytics_service import AnalyticsService
        from app.core.database import AsyncSessionLocal
        test_ws_id = uuid.uuid4()
        async with AsyncSessionLocal() as session:
            summary = await AnalyticsService.get_dashboard_summary(session, test_ws_id)
            self.assertIn("workspace_id", summary)
            self.assertIn("total_automations", summary)
            self.assertIn("active_automations", summary)
            self.assertIn("total_leads", summary)
            self.assertIn("converted_leads", summary)
            self.assertIn("conversion_rate_pct", summary)
            self.assertIn("stats_comments", summary)
            self.assertIn("stats_dms_sent", summary)
            self.assertIn("stats_clicks", summary)
            self.assertIn("delivery_health", summary)
            self.assertIn("queue_latency", summary)
            self.assertIn("total_comments", summary)
            self.assertIn("total_dms", summary)
            self.assertIn("total_contacts", summary)
            self.assertIn("daily_stats", summary)
            self.assertEqual(len(summary["daily_stats"]), 7)
            self.assertEqual(summary["daily_stats"][0]["day"], "Mon")
            self.assertEqual(summary["daily_stats"][6]["day"], "Sun")
            for day_stat in summary["daily_stats"]:
                self.assertIn("count", day_stat)
                self.assertIn("pct", day_stat)
                self.assertIn("date", day_stat)

    async def test_webhook_idempotent_insert_sqlite(self):
        from app.api.webhooks import _insert_webhook_event_idempotent
        from app.core.database import AsyncSessionLocal
        provider_id = f"test_evt_{uuid.uuid4().hex}"
        async with AsyncSessionLocal() as session:
            id1 = await _insert_webhook_event_idempotent(
                session, None, None, provider_id, "COMMENT", {"test": 1}
            )
            self.assertIsNotNone(id1)
            await session.commit()

            id2 = await _insert_webhook_event_idempotent(
                session, None, None, provider_id, "COMMENT", {"test": 1}
            )
            self.assertIsNone(id2)

if __name__ == "__main__":
    unittest.main()
