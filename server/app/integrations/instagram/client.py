# server/app/integrations/instagram/client.py
import asyncio
import logging
import httpx
from typing import Dict, Any, Optional
from app.core.config import settings
from app.integrations.instagram.exceptions import (
    MetaGraphAPIError, MetaRateLimitError, MetaTokenExpiredError
)

logger = logging.getLogger("meta_graph_client")

MAX_RETRIES = 3
INITIAL_BACKOFF = 1.0  # seconds
BACKOFF_FACTOR = 2.0

class MetaGraphClient:
    """
    Isolated client for Meta Graph API.
    Version is dynamically injected from settings.META_GRAPH_API_VERSION.
    Includes automated retries with exponential backoff for transient network issues
    and Meta rate limits (error codes 4, 17, 32, 613).
    """
    def __init__(self, access_token: str, base_url: Optional[str] = None):
        self.access_token = access_token
        self.version = settings.META_GRAPH_API_VERSION
        if base_url:
            self.base_url = base_url.rstrip("/")
        else:
            # Comlina uses Instagram Login for Business (instagram.com/oauth/authorize).
            # Long-lived tokens (even when prefixed with EAA) must query graph.instagram.com.
            self.base_url = f"https://graph.instagram.com/{self.version}"

    async def _execute_with_retry(self, method: str, url: str, **kwargs) -> Dict[str, Any]:
        attempt = 0
        backoff = INITIAL_BACKOFF

        while True:
            attempt += 1
            try:
                async with httpx.AsyncClient(timeout=15.0) as client:
                    if method == "GET":
                        resp = await client.get(url, **kwargs)
                    elif method == "POST":
                        resp = await client.post(url, **kwargs)
                    elif method == "DELETE":
                        resp = await client.delete(url, **kwargs)
                    else:
                        raise ValueError(f"Unsupported HTTP method: {method}")

                    return self._handle_response(resp)

            except (httpx.TransportError, httpx.TimeoutException) as exc:
                if attempt >= MAX_RETRIES:
                    logger.error(f"Meta Graph API connection failed after {attempt} attempts: {exc}")
                    raise MetaGraphAPIError(f"Network transport error connecting to Meta: {exc}", 503) from exc
                logger.warning(
                    f"Meta Graph API connection error (attempt {attempt}/{MAX_RETRIES}): {exc}. Retrying in {backoff}s..."
                )
                await asyncio.sleep(backoff)
                backoff *= BACKOFF_FACTOR

            except MetaRateLimitError as exc:
                if attempt >= MAX_RETRIES:
                    logger.error(f"Meta Graph API rate limit exceeded after {attempt} attempts: {exc}")
                    raise
                logger.warning(
                    f"Meta Graph API rate limited (attempt {attempt}/{MAX_RETRIES}): {exc}. Retrying in {backoff}s..."
                )
                await asyncio.sleep(backoff)
                backoff *= BACKOFF_FACTOR

            except MetaTokenExpiredError:
                # Never retry expired tokens - must fail immediately to trigger re-auth/refresh
                raise

            except MetaGraphAPIError as exc:
                # If Meta returns a transient 5xx server error or transient error code 1 or 2
                if (exc.code in (1, 2) or exc.code >= 500) and attempt < MAX_RETRIES:
                    logger.warning(
                        f"Meta transient server error (code {exc.code}) on attempt {attempt}/{MAX_RETRIES}. Retrying in {backoff}s..."
                    )
                    await asyncio.sleep(backoff)
                    backoff *= BACKOFF_FACTOR
                else:
                    raise

    async def get(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        params = params or {}
        params["access_token"] = self.access_token
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        return await self._execute_with_retry("GET", url, params=params)

    async def post(self, endpoint: str, json_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        json_data = json_data or {}
        params = {"access_token": self.access_token}
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        return await self._execute_with_retry("POST", url, params=params, json=json_data)

    def _handle_response(self, resp: httpx.Response) -> Dict[str, Any]:
        try:
            data = resp.json()
        except Exception:
            raise MetaGraphAPIError(f"Invalid JSON returned from Meta: {resp.text}", resp.status_code)

        if "error" in data:
            err = data["error"]
            code = err.get("code", 0)
            subcode = err.get("error_subcode", 0)
            msg = err.get("message", "Unknown Meta Graph API error")

            if code in (4, 17, 32, 613):
                raise MetaRateLimitError(f"Meta Graph API Rate Limit: {msg}", code, subcode)
            elif code == 190:
                raise MetaTokenExpiredError(f"Meta Graph Token Expired: {msg}", code, subcode)
            else:
                raise MetaGraphAPIError(f"Meta Graph Error ({code}): {msg}", code, subcode)

        return data
