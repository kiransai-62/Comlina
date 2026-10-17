import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict

import httpx
from sqlalchemy import select

from app.core.database import get_db_session
from app.core.encryption import decrypt_token, encrypt_token
from app.models import InstagramAccount

logger = logging.getLogger("refresh_tokens")
REFRESH_URL = "https://graph.instagram.com/refresh_access_token"
REFRESH_WINDOW_DAYS = 7


async def refresh_expiring_tokens_job(ctx: Dict[str, Any]) -> Dict[str, int]:
    summary = {"checked": 0, "refreshed": 0, "deactivated": 0, "failed": 0}
    cutoff = datetime.now(timezone.utc) + timedelta(days=REFRESH_WINDOW_DAYS)
    async with get_db_session() as session:
        accounts = (await session.execute(select(InstagramAccount).where(
            InstagramAccount.is_active == True,  # noqa: E712
            InstagramAccount.token_expires_at.is_not(None),
            InstagramAccount.token_expires_at <= cutoff))).scalars().all()
        async with httpx.AsyncClient(timeout=15.0) as client:
            for account in accounts:
                summary["checked"] += 1
                try:
                    token = decrypt_token(account.access_token_encrypted)
                    resp = await client.get(REFRESH_URL, params={"grant_type": "ig_refresh_token", "access_token": token})
                    body = resp.json()
                except Exception as e:
                    summary["failed"] += 1
                    logger.error("Token refresh error for %s: %s", account.id, e)
                    continue
                if resp.status_code == 200 and body.get("access_token"):
                    account.access_token_encrypted = encrypt_token(body["access_token"])
                    account.token_expires_at = datetime.now(timezone.utc) + timedelta(seconds=body.get("expires_in", 5184000))
                    summary["refreshed"] += 1
                elif (body.get("error") or {}).get("code") == 190:
                    account.is_active = False
                    summary["deactivated"] += 1
                else:
                    summary["failed"] += 1
                    logger.warning("Refresh rejected for %s: %s", account.id, body)
    logger.info("Token refresh run: %s", summary)
    return summary
