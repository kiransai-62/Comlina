# server/app/core/security_middleware.py
import re
import time
import uuid
import logging
from typing import Dict, Tuple
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response, JSONResponse

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

# In-memory sliding window rate limiter
# Key: client_ip -> (request_count, window_start_timestamp)
rate_limit_cache: Dict[str, Tuple[int, float]] = {}
_last_cache_cleanup: float = time.time()

def _cleanup_rate_limit_cache(now: float, ttl: float = 60.0):
    global _last_cache_cleanup
    if now - _last_cache_cleanup > 30.0 or len(rate_limit_cache) > 2000:
        stale_keys = [k for k, v in rate_limit_cache.items() if now - v[1] > ttl]
        for k in stale_keys:
            rate_limit_cache.pop(k, None)
        _last_cache_cleanup = now

def get_client_ip(request: Request) -> str:
    """
    Extract real client IP securely.
    Prioritizes headers populated by trusted reverse proxies (X-Real-IP, CF-Connecting-IP)
    over X-Forwarded-For to prevent client spoofing.
    """
    real_ip = request.headers.get("x-real-ip")
    if real_ip:
        return real_ip.strip()

    cf_ip = request.headers.get("cf-connecting-ip")
    if cf_ip:
        return cf_ip.strip()

    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        parts = [p.strip() for p in forwarded.split(",") if p.strip()]
        if parts:
            # Use rightmost IP added by proxy, avoiding client-prepended spoofed entries
            return parts[-1]

    return request.client.host if request.client else "127.0.0.1"


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Injects OWASP recommended security headers and request-id correlation on every response."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        request_id = request.headers.get("x-request-id") or str(uuid.uuid4())
        request.state.request_id = request_id

        response = await call_next(request)

        response.headers["x-request-id"] = request_id
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=(), usb=()"
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
    """Sliding-window IP rate limiter to protect backend endpoints against brute force and DoS."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        path = request.url.path

        # Exempt health check endpoints
        if path.endswith("/health") or path == "/health":
            return await call_next(request)

        client_ip = get_client_ip(request)
        now = time.time()
        _cleanup_rate_limit_cache(now)
        window_seconds = 10.0

        # Webhook endpoint permits higher burst from Meta servers (300 req / 10s)
        # General API endpoints permit 120 req / 10s
        limit = 300 if "/webhooks/" in path else 120

        count, window_start = rate_limit_cache.get(client_ip, (0, now))

        if now - window_start > window_seconds:
            # Window expired, reset
            rate_limit_cache[client_ip] = (1, now)
        else:
            if count >= limit:
                retry_after = int(window_seconds - (now - window_start)) + 1
                logger.warning(f"[SECURITY BLOCKED: RATE_LIMIT] IP={client_ip} Count={count} Path={path}")
                return JSONResponse(
                    status_code=429,
                    content={
                        "error": "Too Many Requests",
                        "message": "API rate limit exceeded. Please wait before retrying.",
                        "retry_after_seconds": retry_after
                    },
                    headers={"Retry-After": str(retry_after)}
                )
            rate_limit_cache[client_ip] = (count + 1, window_start)

        return await call_next(request)
