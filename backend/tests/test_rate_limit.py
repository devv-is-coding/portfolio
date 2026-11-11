import pytest

from app.services.rate_limit import RateLimiter, contact_rate_limiter, login_rate_limiter
from tests.fakes import BrokenRedis, FakeRedis, IsolatedSettings, as_redis

pytestmark = pytest.mark.anyio

SETTINGS = IsolatedSettings(login_max_attempts=3, login_window_seconds=600)
IP = "203.0.113.7"


async def test_blocks_an_ip_after_the_allowed_failures() -> None:
    limiter = login_rate_limiter(as_redis(FakeRedis()), SETTINGS)

    for _ in range(3):
        assert await limiter.retry_after(IP) is None
        await limiter.hit(IP)

    assert await limiter.retry_after(IP) == 600
    assert await limiter.retry_after("198.51.100.1") is None


async def test_successful_login_resets_the_count() -> None:
    limiter = login_rate_limiter(as_redis(FakeRedis()), SETTINGS)
    for _ in range(3):
        await limiter.hit(IP)

    await limiter.reset(IP)

    assert await limiter.retry_after(IP) is None


async def test_redis_outage_allows_logins() -> None:
    limiter = login_rate_limiter(as_redis(BrokenRedis()), SETTINGS)

    await limiter.hit(IP)
    await limiter.reset(IP)

    assert await limiter.retry_after(IP) is None


async def test_limiters_are_independent_per_name() -> None:
    redis = FakeRedis()
    login = login_rate_limiter(as_redis(redis), SETTINGS)
    contact = contact_rate_limiter(as_redis(redis), SETTINGS)
    for _ in range(3):
        await login.hit(IP)

    assert await login.retry_after(IP) == 600
    assert await contact.retry_after(IP) is None
    assert set(redis.values) == {f"auth:login-failures:{IP}"}


async def test_custom_limiter_counts_hits_in_its_window() -> None:
    redis = FakeRedis()
    limiter = RateLimiter(as_redis(redis), name="test", max_hits=2, window_seconds=60)

    await limiter.hit(IP)
    assert await limiter.retry_after(IP) is None
    await limiter.hit(IP)

    assert await limiter.retry_after(IP) == 60
    assert redis.ttls == {f"test:{IP}": 60}
