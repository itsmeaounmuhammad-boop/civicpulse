"""
Redis client provider. All Redis access — cache and rate limiter both —
goes through this single client instance, injected via FastAPI dependency
(see app/main.py in Phase 5), so tests can substitute a fake easily.
"""

from redis.asyncio import Redis

from app.config import Settings


def create_redis_client(settings: Settings) -> Redis:
    return Redis.from_url(settings.redis_url, decode_responses=True)