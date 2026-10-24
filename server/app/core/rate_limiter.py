# server/app/core/rate_limiter.py
"""
Atomic Redis-backed multi-tenant rate limiter with trusted proxy support.
Provides per-IP, per-user, and per-workspace rate limiting keys with Retry-After calculation.
Fails closed for sensitive operations (Auth, OAuth, Messaging) when Redis is unreachable.
"""

import time
import logging
from typing import Optional, Tuple, Dict, Any
from app.core.config import settings

logger = logging.getLogger("rate_limiter")

# Atomic Lua script for Redis rate limiting.
# INCR key -> if first request, set TTL to window.
# Returns {allowed (1 or 0), retry_after_seconds}
LUA_RATE_LIMIT = """
local key = KEYS[1]
local limit = tonumber(ARGV[1])
local window = tonumber(ARGV[2])

local current = redis.call('INCR', key)
if current == 1 then
    redis.call('EXPIRE', key, window)
end
local ttl = redis.call('TTL', key)
if ttl < 0 then
    redis.call('EXPIRE', key, window)
    ttl = window
end

if current > limit then
    return {0, ttl}
else
    return {1, ttl}
end
"""


class RateLimitUnavailableError(Exception):
    """Raised when rate limiter fails closed due to Redis unavailability on sensitive paths."""
    pass


class RateLimiter:
    def __init__(self):
        self._redis = None
        self._redis_checked = False
        self._redis_available = False
        self._memory_cache: Dict[str, Tuple[int, float, int]] = {}  # key -> (count, window_start, window_seconds)

    def set_redis_client(self, client: Any) -> None:
        """Inject or mock Redis client (useful for unit tests)."""
        self._redis = client
        self._redis_checked = True
        self._redis_available = client is not None

    def reset_in_memory_cache(self) -> None:
        """Clears in-memory fallback cache."""
        self._memory_cache.clear()

    async def _get_redis(self) -> Optional[Any]:
        if self._redis is not None:
            return self._redis

        if self._redis_checked and not self._redis_available:
            return None

        try:
            import redis.asyncio as aioredis
            self._redis = aioredis.from_url(
                settings.REDIS_URL,
                decode_responses=True,
                socket_connect_timeout=0.5,
                socket_timeout=0.5,
            )
            # Quick health check
            await self._redis.ping()
            self._redis_available = True
            self._redis_checked = True
            return self._redis
        except Exception as e:
            logger.warning(f"Could not connect to Redis at {settings.REDIS_URL}: {e}")
            self._redis = None
            self._redis_available = False
            self._redis_checked = True
            return None

    def _check_memory_fallback(self, key: str, limit: int, window: int) -> Tuple[bool, int]:
        """In-memory sliding window fallback for non-sensitive operations or local dev."""
        now = time.time()
        # Clean expired keys
        stale = [k for k, v in self._memory_cache.items() if now - v[1] > v[2]]
        for k in stale:
            self._memory_cache.pop(k, None)

        if key not in self._memory_cache:
            self._memory_cache[key] = (1, now, window)
            return True, window

        count, start_time, win_size = self._memory_cache[key]
        if now - start_time > win_size:
            self._memory_cache[key] = (1, now, window)
            return True, window

        if count >= limit:
            retry_after = max(1, int(win_size - (now - start_time)))
            return False, retry_after

        self._memory_cache[key] = (count + 1, start_time, win_size)
        return True, max(1, int(win_size - (now - start_time)))

    async def check_rate_limit(
        self,
        key: str,
        limit: int,
        window_seconds: int,
        fail_closed: bool = False
    ) -> Tuple[bool, int]:
        """
        Atomically increments and checks the rate limit for `key`.
        Returns (is_allowed: bool, retry_after_seconds: int).
        If Redis is unreachable:
            - If fail_closed=True: raises RateLimitUnavailableError
            - If fail_closed=False: falls back to in-memory rate limiter
        """
        redis_client = await self._get_redis()

        if redis_client is not None:
            try:
                # Execute atomic Lua script
                result = await redis_client.eval(
                    LUA_RATE_LIMIT,
                    1,
                    key,
                    str(limit),
                    str(window_seconds)
                )
                allowed = bool(result[0] == 1)
                ttl = int(result[1]) if len(result) > 1 else window_seconds
                return allowed, max(1, ttl)
            except Exception as e:
                logger.error(f"Redis error during rate limit check for {key}: {e}")
                self._redis_available = False
                if fail_closed:
                    raise RateLimitUnavailableError(f"Rate limiting backend error for sensitive operation: {e}")
                return self._check_memory_fallback(key, limit, window_seconds)

        # Redis is not available
        if fail_closed:
            raise RateLimitUnavailableError("Rate limiting backend unavailable for sensitive operation.")

        return self._check_memory_fallback(key, limit, window_seconds)

    async def check_ip(
        self,
        ip: str,
        route_tag: str,
        limit: int,
        window: int,
        fail_closed: bool = False
    ) -> Tuple[bool, int]:
        key = f"ratelimit:ip:{ip}:{route_tag}"
        return await self.check_rate_limit(key, limit, window, fail_closed=fail_closed)

    async def check_user(
        self,
        user_id: str,
        route_tag: str,
        limit: int,
        window: int,
        fail_closed: bool = False
    ) -> Tuple[bool, int]:
        key = f"ratelimit:user:{user_id}:{route_tag}"
        return await self.check_rate_limit(key, limit, window, fail_closed=fail_closed)

    async def check_workspace(
        self,
        workspace_id: str,
        route_tag: str,
        limit: int,
        window: int,
        fail_closed: bool = False
    ) -> Tuple[bool, int]:
        key = f"ratelimit:workspace:{workspace_id}:{route_tag}"
        return await self.check_rate_limit(key, limit, window, fail_closed=fail_closed)


# Global singleton instance
rate_limiter = RateLimiter()


def is_sensitive_path(path: str) -> bool:
    """
    Identifies endpoints that require fail-closed protection against brute-force or abuse:
    - Authentication (login, signup, refresh, reset)
    - OAuth flows (connect-url, callback)
    - Messaging & Webhook event simulation
    """
    clean = path.lower().rstrip("/")
    if clean.startswith("/api/auth") or clean.startswith("/auth"):
        return True
    if "/oauth" in clean:
        return True
    if "/messages" in clean or "/simulate" in clean:
        return True
    return False


def get_route_tag(path: str) -> str:
    clean = path.lower().rstrip("/")
    if clean.startswith("/api/auth") or clean.startswith("/auth"):
        return "auth"
    if "/oauth" in clean:
        return "oauth"
    if "/webhooks" in clean:
        return "webhooks"
    if "/messages" in clean:
        return "messaging"
    return "general"


def get_limits_for_route(path: str) -> Tuple[int, int]:
    """Returns (max_requests, window_seconds) based on endpoint sensitivity."""
    clean = path.lower().rstrip("/")
    if clean.startswith("/api/auth") or clean.startswith("/auth"):
        # Auth brute force protection: 10 req / 60s per IP
        return 10, 60
    if "/oauth" in clean:
        # OAuth endpoint abuse protection: 20 req / 60s per IP
        return 20, 60
    if "/webhooks" in clean:
        # High burst webhook ingress from Meta: 300 req / 10s per IP
        return 300, 10
    if "/messages" in clean:
        # Messaging rate limit: 60 req / 60s per IP
        return 60, 60
    # General API endpoints: 120 req / 10s per IP
    return 120, 10
