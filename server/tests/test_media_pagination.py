# server/tests/test_media_pagination.py
import uuid
import pytest
from unittest.mock import AsyncMock, patch
from sqlalchemy import select

from app.core.database import init_db, get_db_session
from app.core.encryption import encrypt_token
from app.models import Workspace, InstagramAccount, User
from app.api.instagram import _normalize_media_item, list_instagram_media
from app.integrations.instagram.exceptions import MetaTokenExpiredError, MetaRateLimitError, MetaGraphAPIError
from fastapi import HTTPException

@pytest.fixture(autouse=True)
async def setup_db():
    await init_db()

@pytest.mark.asyncio
async def test_normalize_media_item_missing_fields():
    """
    Verify missing fields are never fabricated:
    - Missing likesCount/commentsCount are None (not forced to 0).
    - Missing caption returns empty string.
    - Media product type REELS maps to REEL.
    """
    raw_reel = {
        "id": "180123456789",
        "media_type": "VIDEO",
        "media_product_type": "REELS",
        "media_url": "https://cdn.example.com/reel.mp4",
        "thumbnail_url": "https://cdn.example.com/reel_thumb.jpg",
        "timestamp": "2026-10-18T10:00:00+0000",
        # like_count and comments_count intentionally absent
    }
    item = _normalize_media_item(raw_reel)
    assert item["id"] == "180123456789"
    assert item["type"] == "REEL"
    assert item["likesCount"] is None
    assert item["commentsCount"] is None
    assert item["caption"] == ""
    assert item["imageUrl"] == "https://cdn.example.com/reel_thumb.jpg"

    raw_post_with_counts = {
        "id": "180999888777",
        "media_type": "IMAGE",
        "caption": "Real photo caption! 📸",
        "media_url": "https://cdn.example.com/photo.jpg",
        "timestamp": "2026-10-18T11:00:00+0000",
        "like_count": 150,
        "comments_count": 12,
        "permalink": "https://instagram.com/p/abc123"
    }
    item2 = _normalize_media_item(raw_post_with_counts)
    assert item2["id"] == "180999888777"
    assert item2["type"] == "POST"
    assert item2["likesCount"] == 150
    assert item2["commentsCount"] == 12
    assert item2["caption"] == "Real photo caption! 📸"

@pytest.mark.asyncio
async def test_list_instagram_media_real_response_and_pagination():
    """
    Verify list_instagram_media retrieves real media, respects limit and after cursor,
    and returns next_cursor for pagination.
    """
    ws_id = uuid.uuid4()
    acc_id = uuid.uuid4()
    user_id = uuid.uuid4()

    async with get_db_session() as session:
        ws = Workspace(id=ws_id, name="Media WS", slug=f"mws-{uuid.uuid4().hex[:6]}")
        session.add(ws)

        acc = InstagramAccount(
            id=acc_id,
            workspace_id=ws_id,
            user_id=user_id,
            ig_user_id="ig_123456",
            username="real_creator",
            access_token_encrypted=encrypt_token("EAAB_valid_media_token"),
            is_active=True
        )
        session.add(acc)
        await session.commit()

    fake_user = User(id=user_id, email="creator@example.com")
    fake_ws = Workspace(id=ws_id, name="Media WS", slug="mws")

    mock_meta_response = {
        "data": [
            {
                "id": "post_101",
                "caption": "Post 1",
                "media_type": "IMAGE",
                "media_url": "https://cdn.example.com/p1.jpg",
                "timestamp": "2026-10-18T09:00:00+0000",
                "like_count": 5
            },
            {
                "id": "post_102",
                "caption": "Post 2 (duplicate)",
                "media_type": "IMAGE",
                "media_url": "https://cdn.example.com/p2.jpg",
                "timestamp": "2026-10-18T08:00:00+0000"
            },
            {
                "id": "post_101",  # Duplicate ID
                "caption": "Post 1 duplicate",
                "media_type": "IMAGE",
                "media_url": "https://cdn.example.com/p1.jpg"
            }
        ],
        "paging": {
            "cursors": {
                "after": "cursor_next_page_999"
            }
        }
    }

    async with get_db_session() as session:
        with patch("app.api.instagram.MetaGraphClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client_cls.return_value = mock_client
            mock_client.get = AsyncMock(return_value=mock_meta_response)

            res = await list_instagram_media(
                account_id=acc_id,
                limit=24,
                after=None,
                format=None,
                user=fake_user,
                workspace=fake_ws,
                db=session
            )

            assert "data" in res
            assert len(res["data"]) == 2  # Deduplicated post_101 and post_102
            assert res["next_cursor"] == "cursor_next_page_999"
            assert res["data"][0]["id"] == "post_101"
            assert res["data"][1]["id"] == "post_102"
            assert res["data"][0]["likesCount"] == 5
            assert res["data"][1]["likesCount"] is None

            # Verify call parameters
            endpoint_called = mock_client.get.call_args[0][0]
            params_called = mock_client.get.call_args[1]["params"]
            assert "fields" in params_called
            assert params_called["limit"] == 24

@pytest.mark.asyncio
async def test_list_instagram_media_account_ownership_isolation():
    """
    Verify account ownership isolation: a workspace cannot fetch media for an
    Instagram account belonging to a different workspace.
    """
    ws1_id = uuid.uuid4()
    ws2_id = uuid.uuid4()
    acc_id = uuid.uuid4()

    async with get_db_session() as session:
        ws1 = Workspace(id=ws1_id, name="WS 1", slug=f"ws1-{uuid.uuid4().hex[:6]}")
        ws2 = Workspace(id=ws2_id, name="WS 2", slug=f"ws2-{uuid.uuid4().hex[:6]}")
        session.add_all([ws1, ws2])

        acc = InstagramAccount(
            id=acc_id,
            workspace_id=ws1_id,  # Belongs to WS 1
            user_id=uuid.uuid4(),
            ig_user_id="ig_ws1_only",
            username="ws1_creator",
            access_token_encrypted=encrypt_token("EAAB_token"),
            is_active=True
        )
        session.add(acc)
        await session.commit()

    # User from WS 2 tries to fetch acc_id
    fake_user2 = User(id=uuid.uuid4(), email="other@example.com")
    fake_ws2 = Workspace(id=ws2_id, name="WS 2", slug="ws2")

    async with get_db_session() as session:
        with pytest.raises(HTTPException) as exc_info:
            await list_instagram_media(
                account_id=acc_id,
                limit=24,
                after=None,
                format=None,
                user=fake_user2,
                workspace=fake_ws2,
                db=session
            )
        assert exc_info.value.status_code == 404
        assert "No connected Instagram account found" in exc_info.value.detail

@pytest.mark.asyncio
async def test_list_instagram_media_token_expired_reauthorization():
    """
    Verify expired token sets account connection_status to REAUTHORIZATION_REQUIRED
    and raises 409 error prompting reconnection.
    """
    ws_id = uuid.uuid4()
    acc_id = uuid.uuid4()
    user_id = uuid.uuid4()

    async with get_db_session() as session:
        ws = Workspace(id=ws_id, name="Expired Token WS", slug=f"exp-{uuid.uuid4().hex[:6]}")
        session.add(ws)

        acc = InstagramAccount(
            id=acc_id,
            workspace_id=ws_id,
            user_id=user_id,
            ig_user_id="ig_exp_123",
            username="expired_creator",
            access_token_encrypted=encrypt_token("EAAB_expired_token"),
            is_active=True
        )
        session.add(acc)
        await session.commit()

    fake_user = User(id=user_id, email="exp@example.com")
    fake_ws = Workspace(id=ws_id, name="Expired Token WS", slug="exp")

    async with get_db_session() as session:
        with patch("app.api.instagram.MetaGraphClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client_cls.return_value = mock_client
            mock_client.get = AsyncMock(side_effect=MetaTokenExpiredError("Token expired"))

            with pytest.raises(HTTPException) as exc_info:
                await list_instagram_media(
                    account_id=acc_id,
                    limit=24,
                    user=fake_user,
                    workspace=fake_ws,
                    db=session
                )
            assert exc_info.value.status_code == 409
            assert "reconnect" in exc_info.value.detail.lower()

        # Check DB was updated with REAUTHORIZATION_REQUIRED
        updated_acc = (await session.execute(select(InstagramAccount).where(InstagramAccount.id == acc_id))).scalar_one()
        assert updated_acc.connection_status == "REAUTHORIZATION_REQUIRED"
        assert updated_acc.last_error_code == "TOKEN_EXPIRED"

@pytest.mark.asyncio
async def test_list_instagram_media_rate_limit_degradation():
    """
    Verify Meta rate limit raises 429 without inventing fake posts.
    """
    ws_id = uuid.uuid4()
    acc_id = uuid.uuid4()
    user_id = uuid.uuid4()

    async with get_db_session() as session:
        ws = Workspace(id=ws_id, name="Rate Limit WS", slug=f"rl-{uuid.uuid4().hex[:6]}")
        session.add(ws)

        acc = InstagramAccount(
            id=acc_id,
            workspace_id=ws_id,
            user_id=user_id,
            ig_user_id="ig_rl_123",
            username="rl_creator",
            access_token_encrypted=encrypt_token("EAAB_rl_token"),
            is_active=True
        )
        session.add(acc)
        await session.commit()

    fake_user = User(id=user_id, email="rl@example.com")
    fake_ws = Workspace(id=ws_id, name="Rate Limit WS", slug="rl")

    async with get_db_session() as session:
        with patch("app.api.instagram.MetaGraphClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client_cls.return_value = mock_client
            mock_client.get = AsyncMock(side_effect=MetaRateLimitError("Rate limit exceeded"))

            with pytest.raises(HTTPException) as exc_info:
                await list_instagram_media(
                    account_id=acc_id,
                    limit=24,
                    user=fake_user,
                    workspace=fake_ws,
                    db=session
                )
            assert exc_info.value.status_code == 429
            assert "rate limit" in exc_info.value.detail.lower()
