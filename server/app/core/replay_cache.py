# server/app/core/replay_cache.py
"""
Replay prevention cache for security-sensitive operations (OAuth states, signed_requests, webhooks).
Supports distributed Redis backend with atomic SET NX EX, and thread-safe in-memory fallback.
"""
import sys
import time
import logging
import threading
from typing import Optional, Dict, Any
from app.core.config import settings

logger = logging.getLogger("replay_cache")


class ReplayCache:
    def __init__(self):
        self._redis = None
        self._redis_checked = False
        self._redis_available = False
        # key -> expiration_timestamp
        self._memory_cache: Dict[str, float] = {}
        self._lock = threading.Lock()

    def set_redis_client(self, client: Any) -> None:
        """Inject or mock Redis client (useful for unit tests)."""
        self._redis = client
        self._redis_checked = True
        self._redis_available = client is not None

    def reset(self) -> None:
        """Clears in-memory cache and resets state."""
        with self._lock:
            self._memory_cache.clear()
            self._redis = None
            self._redis_checked = False
            self._redis_available = False

    async def _get_redis(self) -> Optional[Any]:
        if self._redis is not None:
            return self._redis

        if self._redis_checked and not self._redis_available:
            return None

        # Guard against accidental external network calls during pytest runs
        if "pytest" in sys.modules:
            self._redis_checked = True
            self._redis_available = False
            return None

        try:
            import redis.asyncio as aioredis
            client = aioredis.from_url(
                settings.REDIS_URL,
                decode_responses=True,
                socket_connect_timeout=0.5,
                socket_timeout=0.5
            )
            await client.ping()
            self._redis = client
            self._redis_available = True
            self._redis_checked = True
            return self._redis
        except Exception as e:
            logger.warning(f"Redis unavailable for replay cache ({e}); using in-memory cache.")
            self._redis_available = False
            self._redis_checked = True
            return None

    def _cleanup_memory_cache(self, now: float) -> None:
        """Prune expired entries from in-memory cache."""
        expired_keys = [k for k, exp in self._memory_cache.items() if exp <= now]
        for k in expired_keys:
            self._memory_cache.pop(k, None)

    def check_and_record_sync(self, key: str, ttl_seconds: int = 900, namespace: str = "replay") -> bool:
        """
        Synchronously checks if a key is fresh (not seen) and records it.
        Returns True if fresh (recorded successfully).
        Returns False if already seen (replayed).
        """
        full_key = f"{namespace}:{key}"
        now = time.time()
        with self._lock:
            self._cleanup_memory_cache(now)
            if full_key in self._memory_cache:
                if self._memory_cache[full_key] > now:
                    return False
            self._memory_cache[full_key] = now + ttl_seconds
            return True

    async def check_and_record(self, key: str, ttl_seconds: int = 900, namespace: str = "replay") -> bool:
        """
        Asynchronously checks if a key is fresh (not seen) and records it.
        Uses Redis atomic SET NX EX if available, otherwise falls back to memory cache.
        Returns True if fresh (recorded successfully).
        Returns False if already seen (replayed).
        """
        full_key = f"{namespace}:{key}"
        redis_client = await self._get_redis()
        if redis_client:
            try:
                # Atomic SET key value EX ttl NX
                # Returns True if key was set, None/False if key already existed
                res = await redis_client.set(full_key, "1", ex=ttl_seconds, nx=True)
                return bool(res)
            except Exception as e:
                logger.warning(f"Redis SET NX failed in replay cache ({e}), falling back to memory.")
                if settings.FAIL_CLOSED_ON_REDIS_DOWN and settings.ENVIRONMENT == "production":
                    return False

        # Fallback to in-memory cache
        return self.check_and_record_sync(key, ttl_seconds=ttl_seconds, namespace=namespace)


# Global singleton instance
replay_cache = ReplayCache()
