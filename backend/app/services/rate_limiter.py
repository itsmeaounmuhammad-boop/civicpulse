"""
Distributed rate limiter for POST /api/complaints.

Fixed-window counter in Redis, keyed by client IP. Deliberately NOT an
in-process dictionary: once the HPA scales the backend to N pods, an
in-process limiter would allow N times the intended traffic, since each
pod would count independently. Redis gives every pod a shared counter.
"""

import time

from redis.asyncio import Redis


class RateLimitExceeded(Exception):
    def __init__(self, retry_after_seconds: int) -> None:
        self.retry_after_seconds = retry_after_seconds
        super().__init__(f"Rate limit exceeded, retry after {retry_after_seconds}s")


class RedisRateLimiter:
    def __init__(self, redis: Redis, limit_per_minute: int) -> None:
        self.redis = redis
        self.limit_per_minute = limit_per_minute

    async def check(self, client_ip: str) -> None:
        """
        Raises RateLimitExceeded if the caller has exceeded the limit for
        the current 60-second fixed window. Otherwise increments the counter
        and returns normally.
        """
        window = int(time.time()) // 60
        key = f"ratelimit:{client_ip}:{window}"

        current = await self.redis.incr(key)
        if current == 1:
            # First request in this window — set the key to expire so we
            # don't accumulate stale window keys forever.
            await self.redis.expire(key, 60)

        if current > self.limit_per_minute:
            ttl = await self.redis.ttl(key)
            retry_after = ttl if ttl > 0 else 60
            raise RateLimitExceeded(retry_after_seconds=retry_after)