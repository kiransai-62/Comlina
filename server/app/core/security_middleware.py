import re
import time
import uuid
import hashlib
import logging
from typing import Dict, Tuple, Optional
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response, JSONResponse

from app.core.config import settings
from app.core.rate_limiter import (
    rate_limiter,
    RateLimitUnavailableError,
    is_sensitive_path,
    get_route_tag,
    get_limits_for_route,
)

logger = logging.getLogger("security")

# Maximum allowed payload size: 2MB (2 * 1024 * 1024 bytes)
MAX_CONTENT_LENGTH = 2 * 1024 * 1024

# Path traversal and injection threat signatures
INJECTION_REGEX = re.compile(
    r"(\.\.[\/\\]|%2e%2e[\/\\])|"                         # Path traversal
    r"(<script\b[^>]*>)|"                                  # XSS script tags
    r"(\b(javascript:|vbscript:|data:text\/html))|"        # Malicious protocol handlers
    r"(\b(union(\s+all)?\s+select|waitfor\s+delay|benchmark\s*\(|drop\s+table)\b)", # SQLi signatures
    re.IGNORECASE
)

# Automated scanner and bot user agents
BOT_REGEX = re.compile(
    r"\b(sqlmap|nikto|dirbuster|gobuster|wpscan|masscan|zgrab|nmap|burpsuite|acunetix|havij)\b",
    re.IGNORECASE
)

def get_client_ip(request: Request) -> str:
    """
    Extract real client IP securely respecting settings.TRUSTED_PROXY_COUNT.
    If TRUSTED_PROXY_COUNT <= 0, proxy headers (X-Forwarded-For, X-Real-IP, CF-Connecting-IP)
    are untrusted and client.host is returned directly to prevent client IP spoofing.
    If TRUSTED_PROXY_COUNT > 0, the IP at index [-TRUSTED_PROXY_COUNT] in X-Forwarded-For
    is used as the verified client IP.
    """
    trusted_count = getattr(settings, "TRUSTED_PROXY_COUNT", 0)

    if trusted_count <= 0:
        return request.client.host if request.client else "127.0.0.1"

    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        parts = [p.strip() for p in forwarded.split(",") if p.strip()]
        if len(parts) >= trusted_count:
            return parts[-trusted_count]
        elif parts:
            return parts[0]

    real_ip = request.headers.get("x-real-ip")
    if real_ip:
        return real_ip.strip()

    cf_ip = request.headers.get("cf-connecting-ip")
    if cf_ip:
        return cf_ip.strip()

    return request.client.host if request.client else "127.0.0.1"


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Injects OWASP recommended security headers and request-id correlation on every response."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        request_id = request.headers.get("x-request-id") or str(uuid.uuid4())
        request.state.request_id = request_id
        client_ip = get_client_ip(request)
        workspace_id = request.headers.get("x-workspace-id")

        from app.core.logging import set_log_context, clear_log_context
        set_log_context(request_id=request_id, client_ip=client_ip, workspace_id=workspace_id)

        try:
            response = await call_next(request)
        except Exception as exc:
            logger.error(
                f"[SECURITY UNHANDLED EXCEPTION] RequestId={request_id} Path={request.url.path} Error={exc}",
                exc_info=True
            )
            response = JSONResponse(
                status_code=500,
                content={
                    "error": "Internal Server Error",
                    "message": "An unexpected error occurred. Please try again later.",
                    "request_id": request_id
                }
            )
        finally:
            clear_log_context()

        response.headers["x-request-id"] = request_id
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=(), usb=()"
        if settings.ENVIRONMENT == "production":
            response.headers["Strict-Transport-Security"] = "max-age=63072000; includeSubDomains; preload"
        response.headers["Content-Security-Policy"] = "default-src 'none'; frame-ancestors 'none'"
        response.headers["Cross-Origin-Opener-Policy"] = "same-origin"
        response.headers["Cross-Origin-Resource-Policy"] = "cross-origin"

        # Prevent browser and proxy caching of sensitive API data
        if "cache-control" not in response.headers:
            response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"

        return response


class PayloadSizeLimitMiddleware(BaseHTTPMiddleware):
    """Rejects request bodies larger than 2MB to protect against payload flood & memory exhaustion DoS."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        content_length = request.headers.get("content-length")
        if content_length:
            try:
                length = int(content_length)
                if length > MAX_CONTENT_LENGTH:
                    client_ip = get_client_ip(request)
                    logger.warning(
                        f"[SECURITY BLOCKED: PAYLOAD_TOO_LARGE] IP={client_ip} Length={length} MaxAllowed={MAX_CONTENT_LENGTH}"
                    )
                    return JSONResponse(
                        status_code=413,
                        content={
                            "error": "Payload Too Large",
                            "message": f"Request body exceeds maximum allowed size of {MAX_CONTENT_LENGTH // (1024*1024)}MB."
                        }
                    )
            except ValueError:
                pass

        return await call_next(request)


class AttackFilterMiddleware(BaseHTTPMiddleware):
    """Scans URL path, query params, and User-Agent for known injection signatures and attack tools."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        client_ip = get_client_ip(request)
        user_agent = request.headers.get("user-agent", "")
        raw_query = request.url.query

        # Check for automated attack tooling
        if user_agent and BOT_REGEX.search(user_agent):
            logger.warning(f"[SECURITY BLOCKED: ATTACK_BOT] IP={client_ip} UA={user_agent} Path={request.url.path}")
            return JSONResponse(
                status_code=403,
                content={
                    "error": "Forbidden",
                    "message": "Automated security scanning tools are prohibited."
                }
            )

        # Check for injection attacks in query parameters or URL path
        if (raw_query and INJECTION_REGEX.search(raw_query)) or INJECTION_REGEX.search(request.url.path):
            logger.warning(f"[SECURITY BLOCKED: INJECTION_SIGNATURE] IP={client_ip} Query={raw_query} Path={request.url.path}")
            return JSONResponse(
                status_code=400,
                content={
                    "error": "Bad Request",
                    "message": "Malicious payload signature detected in request URL."
                }
            )

        return await call_next(request)


class ApiRateLimitMiddleware(BaseHTTPMiddleware):
    """
    Multi-tenant rate limiting middleware using atomic Redis backend with trusted proxy support.
    Enforces per-IP, per-user, and per-workspace rate limits with 429 Retry-After headers.
    Fails closed on sensitive routes (auth, oauth, messaging) when Redis is down.
    """

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        path = request.url.path

        # Exempt health check endpoints
        if path.endswith("/health") or path == "/health":
            return await call_next(request)

        client_ip = get_client_ip(request)
        is_sensitive = is_sensitive_path(path)
        fail_closed = is_sensitive and (
            settings.ENVIRONMENT == "production" or getattr(settings, "FAIL_CLOSED_ON_REDIS_DOWN", False)
        )

        try:
            tag = get_route_tag(path)
            limit, window = get_limits_for_route(path)

            # 1. Per-IP rate limit check
            allowed, retry_after = await rate_limiter.check_ip(
                ip=client_ip,
                route_tag=tag,
                limit=limit,
                window=window,
                fail_closed=fail_closed
            )
            if not allowed:
                logger.warning(f"[SECURITY BLOCKED: RATE_LIMIT_IP] IP={client_ip} Path={path}")
                return JSONResponse(
                    status_code=429,
                    content={
                        "error": "Too Many Requests",
                        "message": "API rate limit exceeded. Please wait before retrying.",
                        "retry_after_seconds": retry_after
                    },
                    headers={"Retry-After": str(retry_after)}
                )

            # 2. Per-Workspace rate limit check if X-Workspace-ID header is present
            ws_id = request.headers.get("x-workspace-id")
            if ws_id:
                ws_allowed, ws_retry = await rate_limiter.check_workspace(
                    workspace_id=ws_id,
                    route_tag=tag,
                    limit=200,
                    window=60,
                    fail_closed=fail_closed
                )
                if not ws_allowed:
                    logger.warning(f"[SECURITY BLOCKED: RATE_LIMIT_WORKSPACE] WS={ws_id} Path={path}")
                    return JSONResponse(
                        status_code=429,
                        content={
                            "error": "Too Many Requests",
                            "message": "Workspace rate limit exceeded. Please wait before retrying.",
                            "retry_after_seconds": ws_retry
                        },
                        headers={"Retry-After": str(ws_retry)}
                    )

            # 3. Per-User rate limit check if Authorization Bearer token is present
            auth_header = request.headers.get("authorization")
            if auth_header and auth_header.startswith("Bearer "):
                token = auth_header.split(" ", 1)[1].strip()
                user_key = hashlib.sha256(token.encode("utf-8")).hexdigest()[:16]
                user_allowed, user_retry = await rate_limiter.check_user(
                    user_id=user_key,
                    route_tag=tag,
                    limit=120,
                    window=60,
                    fail_closed=fail_closed
                )
                if not user_allowed:
                    logger.warning(f"[SECURITY BLOCKED: RATE_LIMIT_USER] UserKey={user_key} Path={path}")
                    return JSONResponse(
                        status_code=429,
                        content={
                            "error": "Too Many Requests",
                            "message": "User rate limit exceeded. Please wait before retrying.",
                            "retry_after_seconds": user_retry
                        },
                        headers={"Retry-After": str(user_retry)}
                    )

        except RateLimitUnavailableError:
            logger.error(f"[SECURITY FAIL_CLOSED] Rate limiter unavailable for sensitive route: {path}")
            return JSONResponse(
                status_code=503,
                content={
                    "error": "Service Unavailable",
                    "message": "Security rate limiting service is temporarily unavailable. Request blocked."
                },
                headers={"Retry-After": "5"}
            )

        return await call_next(request)
