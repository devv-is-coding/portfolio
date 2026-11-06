from typing import Annotated

from fastapi import Depends
from redis.asyncio import Redis

from app.core.config import get_settings

# Creating the client doesn't connect; the first command does.
redis_client = Redis.from_url(get_settings().redis_url, decode_responses=True)


async def get_redis() -> Redis:
    return redis_client


RedisDep = Annotated[Redis, Depends(get_redis)]
