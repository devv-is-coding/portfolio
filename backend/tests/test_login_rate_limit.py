import pytest

from app.core.config import Settings
from app.services.login_rate_limit import LoginRateLimiter
from tests.fakes import BrokenRedis, FakeRedis, as_redis

pytestmark = pytest.mark.anyio

SETTINGS = Settings(_env_file=None, login_max_attempts=3, login_window_seconds=600)
IP = "203.0.113.7"


async def test_blocks_an_ip_after_the_allowed_failures() -> None:
    limiter = LoginRateLimiter(as_redis(FakeRedis()), SETTINGS)

    for _ in range(3):
        assert await limiter.retry_after(IP) is None
        await limiter.record_failure(IP)

    assert await limiter.retry_after(IP) == 600
    assert await limiter.retry_after("198.51.100.1") is None


async def test_successful_login_resets_the_count() -> None:
    limiter = LoginRateLimiter(as_redis(FakeRedis()), SETTINGS)
    for _ in range(3):
        await limiter.record_failure(IP)

    await limiter.reset(IP)

    assert await limiter.retry_after(IP) is None


async def test_redis_outage_allows_logins() -> None:
    limiter = LoginRateLimiter(as_redis(BrokenRedis()), SETTINGS)

    await limiter.record_failure(IP)
    await limiter.reset(IP)

    assert await limiter.retry_after(IP) is None
