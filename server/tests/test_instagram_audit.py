# server/tests/test_instagram_audit.py
import time
import unittest
import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

from app.api.instagram import (
    _is_allowed_redirect_uri,
    disconnect_instagram_account,
    generate_oauth_state,
    verify_oauth_state,
)
from app.integrations.instagram.oauth import IG_AUTHORIZE_URL, MetaOAuth
from app.integrations.instagram.webhooks import InstagramWebhookParser
from app.models import Automation, InstagramAccount, Workspace


class TestInstagramAudit(unittest.IsolatedAsyncioTestCase):
    def test_canonical_oauth_authorize_url(self):
        """
        Verify OAuth authorize URL uses canonical Meta Instagram URL
        https://www.instagram.com/oauth/authorize per current official Meta documentation.
        """
        self.assertEqual(IG_AUTHORIZE_URL, "https://www.instagram.com/oauth/authorize")
        url = MetaOAuth.get_authorization_url(state="test_state_123")
        self.assertTrue(url.startswith("https://www.instagram.com/oauth/authorize?"))
        self.assertIn("client_id=", url)
        self.assertIn("state=test_state_123", url)
        self.assertIn("scope=instagram_business_basic", url)

    def test_oauth_state_generation_and_verification(self):
        """
        Verify signed OAuth state generation binds workspace_id, user_id, timestamp, and HMAC signature.
        """
        ws_id = uuid.uuid4()
        user_id = uuid.uuid4()
        state = generate_oauth_state(ws_id, user_id)

        # Structure must be ws_id:user_id:timestamp:nonce:sig
        parts = state.split(":")
        self.assertEqual(len(parts), 5)
        self.assertEqual(parts[0], str(ws_id))
        self.assertEqual(parts[1], str(user_id))

        # Successful verification
        self.assertTrue(verify_oauth_state(state, ws_id, user_id))

    def test_oauth_state_expired(self):
        """
        Verify OAuth state rejects expired states (>900 seconds / 15 minutes TTL).
        """
        ws_id = uuid.uuid4()
        user_id = uuid.uuid4()
        # Generate state, then tamper timestamp to 20 minutes ago
        state = generate_oauth_state(ws_id, user_id)
        parts = state.split(":")
        old_ts = str(int(time.time()) - 1200)  # 20 min ago
        # Recalculate HMAC with expired timestamp
        from app.core.config import settings
        import hmac, hashlib
        tampered_payload = f"{parts[0]}:{parts[1]}:{old_ts}:{parts[3]}"
        tampered_sig = hmac.new(
            key=settings.TOKEN_ENCRYPTION_KEY.encode("utf-8"),
            msg=tampered_payload.encode("utf-8"),
            digestmod=hashlib.sha256
        ).hexdigest()[:16]
        expired_state = f"{tampered_payload}:{tampered_sig}"

        self.assertFalse(verify_oauth_state(expired_state, ws_id, user_id, max_age_seconds=900))

    def test_oauth_state_mismatched_user_or_workspace(self):
        """
        Verify OAuth state is rejected if workspace or user does not match.
        """
        ws_id = uuid.uuid4()
        user_id = uuid.uuid4()
        different_ws = uuid.uuid4()
        different_user = uuid.uuid4()

        state = generate_oauth_state(ws_id, user_id)

        self.assertFalse(verify_oauth_state(state, different_ws, user_id))
        self.assertFalse(verify_oauth_state(state, ws_id, different_user))

    def test_oauth_state_tampered_signature(self):
        """
        Verify OAuth state is rejected if signature is tampered.
        """
        ws_id = uuid.uuid4()
        user_id = uuid.uuid4()
        state = generate_oauth_state(ws_id, user_id)
        tampered_state = state[:-4] + "ffff"

        self.assertFalse(verify_oauth_state(tampered_state, ws_id, user_id))

    def test_oauth_state_legacy_three_part_support(self):
        """
        Verify backward compatibility for legacy 3-part states (ws:nonce:sig).
        """
        ws_id = uuid.uuid4()
        from app.core.config import settings
        import hmac, hashlib
        nonce = "legacy_nonce_123"
        payload = f"{ws_id}:{nonce}"
        sig = hmac.new(
            key=settings.TOKEN_ENCRYPTION_KEY.encode("utf-8"),
            msg=payload.encode("utf-8"),
            digestmod=hashlib.sha256
        ).hexdigest()[:16]
        legacy_state = f"{payload}:{sig}"

        self.assertTrue(verify_oauth_state(legacy_state, ws_id))
        self.assertFalse(verify_oauth_state(legacy_state, uuid.uuid4()))

    def test_redirect_uri_allowlist_validation(self):
        """
        Verify redirect_uri validation blocks open redirects and allows approved domains.
        """
        self.assertTrue(_is_allowed_redirect_uri(None))
        self.assertTrue(_is_allowed_redirect_uri("http://localhost:3000/connect/instagram/callback"))
        self.assertTrue(_is_allowed_redirect_uri("http://127.0.0.1:3000/oauth/callback"))
        self.assertTrue(_is_allowed_redirect_uri("https://app.comlina.ai/auth/callback"))
        self.assertTrue(_is_allowed_redirect_uri("https://comlina.com/api/callback"))
        self.assertTrue(_is_allowed_redirect_uri("https://comlina.onrender.com/connect/instagram"))
        self.assertTrue(_is_allowed_redirect_uri("https://my-app.vercel.app/connect/instagram"))

        # Malicious domains must be rejected
        self.assertFalse(_is_allowed_redirect_uri("https://attacker.evil.com/callback"))
        self.assertFalse(_is_allowed_redirect_uri("javascript:alert(1)"))
        self.assertFalse(_is_allowed_redirect_uri("http://evil-localhost:3000"))

    def test_webhook_parser_self_comment_filter(self):
        """
        Verify InstagramWebhookParser filters out comments authored by the business account itself
        to prevent recursive comment trigger loops.
        """
        business_id = "178414000111"
        follower_id = "998877665544"

        # Webhook payload with one self-comment from the creator and one comment from a follower
        payload = {
            "entry": [
                {
                    "id": business_id,
                    "time": 1718000000,
                    "changes": [
                        {
                            "field": "comments",
                            "value": {
                                "id": "comment_self_1",
                                "from": {"id": business_id, "username": "creator_self"},
                                "text": "Thanks for checking out my post!",
                                "media": {"id": "media_post_100"}
                            }
                        },
                        {
                            "field": "comments",
                            "value": {
                                "id": "comment_follower_1",
                                "from": {"id": follower_id, "username": "follower_john"},
                                "text": "Send me the link!",
                                "media": {"id": "media_post_100"}
                            }
                        }
                    ]
                }
            ]
        }

        events = InstagramWebhookParser.extract_events(payload)
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["comment_id"], "comment_follower_1")
        self.assertEqual(events[0]["sender_id"], follower_id)
        self.assertEqual(events[0]["sender_username"], "follower_john")

    def test_webhook_parser_echo_messaging_filter(self):
        """
        Verify InstagramWebhookParser filters out echo direct messages sent by the business page.
        """
        business_id = "178414000111"
        payload = {
            "entry": [
                {
                    "id": business_id,
                    "messaging": [
                        {
                            "sender": {"id": business_id},
                            "recipient": {"id": "follower_123"},
                            "message": {
                                "mid": "mid_echo_1",
                                "text": "Our automated reply",
                                "is_echo": True
                            }
                        },
                        {
                            "sender": {"id": "follower_123"},
                            "recipient": {"id": business_id},
                            "message": {
                                "mid": "mid_user_1",
                                "text": "Hello I have a question",
                                "is_echo": False
                            }
                        }
                    ]
                }
            ]
        }

        events = InstagramWebhookParser.extract_events(payload)
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["provider_event_id"], "mid_user_1")
        self.assertEqual(events[0]["event_type"], "MESSAGING")

    async def test_disconnect_instagram_account_cleans_token_and_pauses_automations(self):
        """
        Verify disconnect_instagram_account wipes access token and transitions active automations to PAUSED.
        """
        ws_id = uuid.uuid4()
        acc_id = uuid.uuid4()
        workspace = Workspace(id=ws_id, name="Test WS")
        account = InstagramAccount(
            id=acc_id,
            workspace_id=ws_id,
            ig_user_id="178414000999",
            username="test_creator",
            access_token_encrypted="encrypted_secret_token",
            is_active=True
        )
        auto1 = Automation(
            id=uuid.uuid4(),
            workspace_id=ws_id,
            instagram_account_id=acc_id,
            name="Auto 1",
            status="ACTIVE",
            trigger_type="COMMENT"
        )
        auto2 = Automation(
            id=uuid.uuid4(),
            workspace_id=ws_id,
            instagram_account_id=acc_id,
            name="Auto 2",
            status="ACTIVE",
            trigger_type="COMMENT"
        )

        mock_db = AsyncMock()
        # Mock executing query for account then automations
        acc_result = MagicMock()
        acc_result.scalar_one_or_none.return_value = account

        auto_result = MagicMock()
        auto_result.scalars.return_value.all.return_value = [auto1, auto2]

        mock_db.execute.side_effect = [acc_result, auto_result]

        await disconnect_instagram_account(
            account_id=acc_id,
            workspace=workspace,
            db=mock_db
        )

        self.assertFalse(account.is_active)
        self.assertEqual(account.access_token_encrypted, "")
        self.assertEqual(auto1.status, "PAUSED")
        self.assertEqual(auto2.status, "PAUSED")
        mock_db.commit.assert_awaited_once()

    async def test_strict_one_to_one_mapping_blocks_duplicate_instagram_registration(self):
        """
        Verify strict 1-to-1 mapping: An Instagram account cannot be linked to a second workspace/email.
        If a user attempts to connect an already-linked Instagram account ID, HTTP 409 Conflict is raised.
        """
        from fastapi import HTTPException
        from app.api.instagram import handle_oauth_callback
        from app.schemas import ConnectAccountRequest
        from app.models import User

        ws_initial = Workspace(id=uuid.uuid4(), name="Initial WS", max_accounts=5)
        ws_second = Workspace(id=uuid.uuid4(), name="Second WS", max_accounts=5)
        user_second = User(id=uuid.uuid4(), email="new_user@example.com", full_name="New User")

        existing_acc = InstagramAccount(
            id=uuid.uuid4(),
            workspace_id=ws_initial.id,
            ig_user_id="17841499999999",
            username="locked_brand",
            access_token_encrypted="encrypted_tok",
            is_active=True
        )

        mock_db = AsyncMock()
        # Mock global account search finding existing_acc in initial workspace
        acc_result = MagicMock()
        acc_result.scalar_one_or_none.return_value = existing_acc

        # Mock original user lookup
        user_result = MagicMock()
        user_result.scalar_one_or_none.return_value = "original_owner@example.com"

        mock_db.execute.side_effect = [acc_result, user_result]

        req = ConnectAccountRequest(
            code="test_code_123",
            state=generate_oauth_state(ws_second.id, user_second.id),
            redirect_uri="http://localhost:3000/connect/instagram"
        )

        with patch("app.integrations.instagram.oauth.MetaOAuth.exchange_code_for_token", new_callable=AsyncMock) as mock_exchange, \
             patch("app.integrations.instagram.oauth.MetaOAuth.exchange_for_long_lived_token", new_callable=AsyncMock) as mock_long, \
             patch("app.integrations.instagram.oauth.MetaOAuth.fetch_instagram_profile", new_callable=AsyncMock) as mock_profile:

            mock_exchange.return_value = {"access_token": "short_tok"}
            mock_long.return_value = {"access_token": "long_tok", "expires_in": 5184000}
            mock_profile.return_value = {
                "id": "17841499999999",
                "user_id": "17841499999999",
                "username": "locked_brand",
                "account_type": "BUSINESS",
                "followers_count": 50000
            }

            with self.assertRaises(HTTPException) as ctx:
                await handle_oauth_callback(
                    data=req,
                    user=user_second,
                    workspace=ws_second,
                    db=mock_db
                )

            self.assertEqual(ctx.exception.status_code, 409)
            self.assertIn("already registered", ctx.exception.detail)
            self.assertIn("@locked_brand", ctx.exception.detail)

    async def test_real_time_profile_sync(self):
        """
        Verify sync_instagram_account_profile fetches live metrics from Meta and updates the database.
        """
        from app.api.instagram import sync_instagram_account_profile
        from app.core.encryption import encrypt_token

        ws_id = uuid.uuid4()
        workspace = Workspace(id=ws_id, name="Test WS")
        acc_id = uuid.uuid4()
        account = InstagramAccount(
            id=acc_id,
            workspace_id=ws_id,
            ig_user_id="178414000123",
            username="old_handle",
            follower_count=100,
            access_token_encrypted=encrypt_token("EAAG_valid_token"),
            is_active=True
        )

        mock_db = AsyncMock()
        res_mock = MagicMock()
        res_mock.scalar_one_or_none.return_value = account
        mock_db.execute.return_value = res_mock

        with patch("app.integrations.instagram.oauth.MetaOAuth.fetch_instagram_profile", new_callable=AsyncMock) as mock_profile:
            mock_profile.return_value = {
                "username": "new_updated_handle",
                "account_type": "BUSINESS",
                "followers_count": 25400,
                "profile_picture_url": "https://cdn.instagram.com/pic.jpg"
            }

            updated = await sync_instagram_account_profile(
                account_id=acc_id,
                workspace=workspace,
                db=mock_db
            )

            self.assertEqual(updated.username, "new_updated_handle")
            self.assertEqual(updated.follower_count, 25400)
            self.assertEqual(updated.profile_pic_url, "https://cdn.instagram.com/pic.jpg")
            mock_db.commit.assert_awaited_once()


if __name__ == "__main__":
    unittest.main()

