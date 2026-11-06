"""In-memory stand-ins for external services in tests."""

from typing import cast

from redis.asyncio import Redis
from redis.exceptions import ConnectionError as RedisConnectionError


class FakeRedis:
    """The few Redis commands the app uses. TTLs are stored, not counted down."""

    def __init__(self) -> None:
        self.values: dict[str, str] = {}
        self.ttls: dict[str, int] = {}

    async def get(self, key: str) -> str | None:
        return self.values.get(key)

    async def incr(self, key: str) -> int:
        value = int(self.values.get(key, "0")) + 1
        self.values[key] = str(value)
        return value

    async def expire(self, key: str, seconds: int) -> bool:
        self.ttls[key] = seconds
        return key in self.values

    async def ttl(self, key: str) -> int:
        return self.ttls.get(key, -1)

    async def delete(self, *keys: str) -> int:
        removed = 0
        for key in keys:
            removed += self.values.pop(key, None) is not None
            self.ttls.pop(key, None)
        return removed


class BrokenRedis:
    """Every command fails, like a Redis server that is down."""

    def __getattr__(self, _name: str) -> object:
        async def fail(*_args: object, **_kwargs: object) -> None:
            raise RedisConnectionError("Redis is down")

        return fail


def as_redis(fake: FakeRedis | BrokenRedis) -> Redis:
    return cast(Redis, fake)
