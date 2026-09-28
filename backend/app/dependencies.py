"""
Dependency injection wiring. Routes depend on these functions rather than
constructing services/repositories/clients themselves.
"""

from typing import Annotated

from fastapi import Depends, Request
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings, get_settings
from app.database import get_db
from app.providers.triage.factory import get_triage_provider
from app.repositories.complaint_repository import ComplaintRepository
from app.services.complaint_service import ComplaintService
from app.services.rate_limiter import RedisRateLimiter
from app.services.stats_cache import StatsCache
from app.services.triage_service import TriageService


def get_redis(request: Request) -> Redis:
    # The Redis client is created once at startup and stashed on app.state
    # (see main.py lifespan) — never created per-request.
    return request.app.state.redis


def get_complaint_repository(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ComplaintRepository:
    return ComplaintRepository(db)


def get_triage_service(
    settings: Annotated[Settings, Depends(get_settings)],
    redis: Annotated[Redis, Depends(get_redis)],
) -> TriageService:
    provider = get_triage_provider(settings)
    return TriageService(provider=provider, redis=redis)


def get_stats_cache(redis: Annotated[Redis, Depends(get_redis)]) -> StatsCache:
    return StatsCache(redis)


def get_rate_limiter(
    settings: Annotated[Settings, Depends(get_settings)],
    redis: Annotated[Redis, Depends(get_redis)],
) -> RedisRateLimiter:
    return RedisRateLimiter(redis=redis, limit_per_minute=settings.rate_limit_per_minute)


def get_complaint_service(
    repository: Annotated[ComplaintRepository, Depends(get_complaint_repository)],
    triage_service: Annotated[TriageService, Depends(get_triage_service)],
    stats_cache: Annotated[StatsCache, Depends(get_stats_cache)],
    redis: Annotated[Redis, Depends(get_redis)],
) -> ComplaintService:
    return ComplaintService(
        repository=repository,
        triage_service=triage_service,
        stats_cache=stats_cache,
        redis=redis,
    )