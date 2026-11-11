"""Fixed-window limits per client IP, counted in Redis.

Keyed by IP: for logins, limiting by email would let anyone lock the admin out by
failing logins with the admin's address. If Redis is down the request is allowed
(fail open) and a warning is logged, so a Redis outage never locks anyone out.
"""

import logging

from redis.asyncio import Redis
from redis.exceptions import RedisError

from app.core.config import Settings

logger = logging.getLogger(__name__)


class RateLimiter:
    """At most `max_hits` hits per key within `window_seconds` (from the first hit)."""

    def __init__(self, redis: Redis, *, name: str, max_hits: int, window_seconds: int) -> None:
        self._redis = redis
        self._name = name
        self._max_hits = max_hits
        self._window_seconds = window_seconds

    def _key(self, client_ip: str) -> str:
        return f"{self._name}:{client_ip}"

    async def retry_after(self, client_ip: str) -> int | None:
        """Seconds until this IP may try again, or None when it isn't blocked."""
        key = self._key(client_ip)
        try:
            hits = await self._redis.get(key)
            if hits is None or int(hits) < self._max_hits:
                return None
            ttl = await self._redis.ttl(key)
        except RedisError:
            logger.warning("Rate limit %s skipped: Redis unavailable", self._name, exc_info=True)
            return None
        return max(int(ttl), 1)

    async def hit(self, client_ip: str) -> None:
        key = self._key(client_ip)
        try:
            hits = await self._redis.incr(key)
            if hits == 1:
                await self._redis.expire(key, self._window_seconds)
        except RedisError:
            logger.warning(
                "Rate limit %s not counted: Redis unavailable", self._name, exc_info=True
            )

    async def reset(self, client_ip: str) -> None:
        try:
            await self._redis.delete(self._key(client_ip))
        except RedisError:
            logger.warning("Rate limit %s not reset: Redis unavailable", self._name, exc_info=True)


def login_rate_limiter(redis: Redis, settings: Settings) -> RateLimiter:
    """Failed logins (successful ones reset the count)."""
    return RateLimiter(
        redis,
        name="auth:login-failures",
        max_hits=settings.login_max_attempts,
        window_seconds=settings.login_window_seconds,
    )


def contact_rate_limiter(redis: Redis, settings: Settings) -> RateLimiter:
    """Contact form messages."""
    return RateLimiter(
        redis,
        name="contact:messages",
        max_hits=settings.contact_max_messages,
        window_seconds=settings.contact_window_seconds,
    )
