"""Failed-login limit per client IP, counted in Redis.

Keyed by IP, not by email: limiting by email would let anyone lock the admin out by
failing logins with the admin's address. If Redis is down, logins are allowed
(fail open) and a warning is logged, so a Redis outage never locks the admin out.
"""

import logging

from redis.asyncio import Redis
from redis.exceptions import RedisError

from app.core.config import Settings

logger = logging.getLogger(__name__)


class LoginRateLimiter:
    def __init__(self, redis: Redis, settings: Settings) -> None:
        self._redis = redis
        self._max_attempts = settings.login_max_attempts
        self._window_seconds = settings.login_window_seconds

    @staticmethod
    def _key(client_ip: str) -> str:
        return f"auth:login-failures:{client_ip}"

    async def retry_after(self, client_ip: str) -> int | None:
        """Seconds until this IP may try again, or None when it isn't blocked."""
        key = self._key(client_ip)
        try:
            failures = await self._redis.get(key)
            if failures is None or int(failures) < self._max_attempts:
                return None
            ttl = await self._redis.ttl(key)
        except RedisError:
            logger.warning("Login rate limit skipped: Redis unavailable", exc_info=True)
            return None
        return max(int(ttl), 1)

    async def record_failure(self, client_ip: str) -> None:
        key = self._key(client_ip)
        try:
            failures = await self._redis.incr(key)
            if failures == 1:
                await self._redis.expire(key, self._window_seconds)
        except RedisError:
            logger.warning("Login failure not counted: Redis unavailable", exc_info=True)

    async def reset(self, client_ip: str) -> None:
        try:
            await self._redis.delete(self._key(client_ip))
        except RedisError:
            logger.warning("Login failures not reset: Redis unavailable", exc_info=True)
