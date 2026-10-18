# server/app/jobs/refresh_tokens.py
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
    now = datetime.now(timezone.utc)
    cutoff = now + timedelta(days=REFRESH_WINDOW_DAYS)

    async with get_db_session() as session:
        accounts = (await session.execute(select(InstagramAccount).where(
            InstagramAccount.is_active == True,  # noqa: E712
            InstagramAccount.token_expires_at.is_not(None),
            InstagramAccount.token_expires_at <= cutoff))).scalars().all()

        async with httpx.AsyncClient(timeout=15.0) as client:
            for account in accounts:
                summary["checked"] += 1
                curr_now = datetime.now(timezone.utc)

                # Check if token is already expired
                if account.token_expires_at:
                    exp = account.token_expires_at
                    if exp.tzinfo is None:
                        exp = exp.replace(tzinfo=timezone.utc)
                    if exp <= curr_now:
                        account.connection_status = "REAUTHORIZATION_REQUIRED"
                        account.last_error_code = "TOKEN_EXPIRED"
                        summary["deactivated"] += 1
                        continue

                # Check Meta 24-hour refresh rule
                last_ref = getattr(account, "last_refreshed_at", None) or getattr(account, "connected_at", None)
                if last_ref:
                    if last_ref.tzinfo is None:
                        last_ref = last_ref.replace(tzinfo=timezone.utc)
                    if curr_now - last_ref < timedelta(hours=24):
                        logger.info("Account %s token refreshed or connected less than 24h ago; skipping.", account.id)
                        continue

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
                    account.token_expires_at = curr_now + timedelta(seconds=body.get("expires_in", 5184000))
                    account.last_refreshed_at = curr_now
                    account.last_validated_at = curr_now
                    account.connection_status = "CONNECTED"
                    account.last_error_code = None
                    summary["refreshed"] += 1
                elif "24 hours" in str(body).lower():
                    account.last_refreshed_at = curr_now
                    account.last_validated_at = curr_now
                elif (body.get("error") or {}).get("code") == 190 or "expired" in str(body).lower():
                    # Sanity check with profile fetch before revoking connection
                    is_token_alive = False
                    try:
                        p_resp = await client.get(
                            "https://graph.instagram.com/me",
                            params={"access_token": token, "fields": "id,username"}
                        )
                        p_body = p_resp.json()
                        if p_resp.status_code == 200 and (p_body.get("id") or p_body.get("username")):
                            is_token_alive = True
                    except Exception:
                        is_token_alive = False

                    if is_token_alive:
                        logger.info("Token refresh returned code 190, but profile check verified token is active for %s. Not revoking.", account.id)
                        account.last_validated_at = curr_now
                        continue

                    account.connection_status = "REAUTHORIZATION_REQUIRED"
                    account.last_error_code = "TOKEN_REVOKED"
                    summary["deactivated"] += 1
                else:
                    account.last_error_code = "REFRESH_FAILED"
                    summary["failed"] += 1
                    logger.warning("Refresh rejected for %s: %s", account.id, body)

        await session.commit()

    logger.info("Token refresh run completed: %s", summary)
    return summary
