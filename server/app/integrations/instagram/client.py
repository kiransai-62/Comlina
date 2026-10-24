# server/app/integrations/instagram/client.py
import asyncio
import logging
import httpx
from typing import Dict, Any, Optional
from app.core.config import settings
from app.core.logging import redact_string
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
    Permanent errors (e.g. 190 token expired, 100 invalid param, 10/200 permission)
    are never retried indiscriminately.
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
                    raise MetaGraphAPIError(
                        f"Network transport error connecting to Meta: {exc}",
                        code=503,
                        http_status=503,
                        error_type="TransportError",
                        is_transient=True,
                    ) from exc
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
                # Only retry transient errors (codes 1/2 or transient 5xx server errors).
                # Never retry permanent failures (invalid params, permissions, comment expired).
                if exc.is_transient and attempt < MAX_RETRIES:
                    logger.warning(
                        f"Meta transient error (code {exc.code}, status {exc.http_status}) on attempt {attempt}/{MAX_RETRIES}. Retrying in {backoff}s..."
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
        except Exception as json_err:
            raw_preview = redact_string(resp.text[:300] if resp.text else "")
            is_transient = resp.status_code in (500, 502, 503, 504)
            raise MetaGraphAPIError(
                message=f"Invalid JSON returned from Meta (HTTP {resp.status_code}): {raw_preview}",
                code=resp.status_code,
                http_status=resp.status_code,
                error_type="MalformedResponse",
                is_transient=is_transient,
            ) from json_err

        if isinstance(data, dict) and "error" in data:
            err = data["error"] if isinstance(data["error"], dict) else {}
            code = err.get("code", 0)
            subcode = err.get("error_subcode", 0)
            msg = err.get("message", "Unknown Meta Graph API error")
            err_type = err.get("type")
            fbtrace_id = err.get("fbtrace_id")
            meta_transient = err.get("is_transient")

            # Determine transient flag
            if isinstance(meta_transient, bool):
                is_transient = meta_transient
            elif code in (4, 17, 32, 613) or resp.status_code == 429:
                is_transient = True
            elif code in (1, 2) or (resp.status_code >= 500 and code not in (10, 100, 190, 200)):
                is_transient = True
            elif code in (10, 100, 190, 200, 298) or subcode == 2018001 or resp.status_code in (400, 401, 403, 404, 422):
                is_transient = False
            else:
                is_transient = False

            if code in (4, 17, 32, 613) or resp.status_code == 429:
                raise MetaRateLimitError(
                    message=f"Meta Graph API Rate Limit: {msg}",
                    code=code,
                    error_subcode=subcode,
                    http_status=resp.status_code,
                    error_type=err_type,
                    is_transient=True,
                    fbtrace_id=fbtrace_id,
                )
            elif code == 190:
                raise MetaTokenExpiredError(
                    message=f"Meta Graph Token Expired: {msg}",
                    code=code,
                    error_subcode=subcode,
                    http_status=resp.status_code,
                    error_type=err_type,
                    is_transient=False,
                    fbtrace_id=fbtrace_id,
                )
            else:
                raise MetaGraphAPIError(
                    message=f"Meta Graph Error ({code}): {msg}",
                    code=code,
                    error_subcode=subcode,
                    http_status=resp.status_code,
                    error_type=err_type,
                    is_transient=is_transient,
                    fbtrace_id=fbtrace_id,
                )

        if resp.status_code >= 400:
            is_transient = resp.status_code in (429, 500, 502, 503, 504)
            raise MetaGraphAPIError(
                message=f"Meta Graph API HTTP Error {resp.status_code}",
                code=resp.status_code,
                http_status=resp.status_code,
                error_type="HTTPError",
                is_transient=is_transient,
            )

        return data
