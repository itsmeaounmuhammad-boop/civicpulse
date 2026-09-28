"""
Distributed rate limiter tests: unit level (Redis counter) and API level
(429 + Retry-After header).
"""

import pytest

from app.dependencies import get_rate_limiter
from app.main import app
from app.services.rate_limiter import RateLimitExceeded, RedisRateLimiter


@pytest.mark.asyncio
async def test_limiter_allows_requests_under_limit(redis_client):
    limiter = RedisRateLimiter(redis_client, limit_per_minute=3)
    for _ in range(3):
        await limiter.check("10.0.0.1")


@pytest.mark.asyncio
async def test_limiter_blocks_over_limit_with_retry_after(redis_client):
    limiter = RedisRateLimiter(redis_client, limit_per_minute=2)
    await limiter.check("10.0.0.2")
    await limiter.check("10.0.0.2")

    with pytest.raises(RateLimitExceeded) as exc_info:
        await limiter.check("10.0.0.2")
    assert 1 <= exc_info.value.retry_after_seconds <= 60


@pytest.mark.asyncio
async def test_limiter_counts_per_client_ip(redis_client):
    limiter = RedisRateLimiter(redis_client, limit_per_minute=1)
    await limiter.check("10.0.0.3")
    await limiter.check("10.0.0.4")  # a different IP has its own counter


@pytest.mark.asyncio
async def test_api_returns_429_with_retry_after_header(client, redis_client):
    app.dependency_overrides[get_rate_limiter] = lambda: RedisRateLimiter(
        redis_client, limit_per_minute=1
    )
    payload = {"text": "Burst water main flooding the street", "location": "Main Street"}

    first = await client.post("/api/complaints", json=payload)
    second = await client.post("/api/complaints", json=payload)

    assert first.status_code == 201
    assert second.status_code == 429
    assert "retry-after" in second.headers