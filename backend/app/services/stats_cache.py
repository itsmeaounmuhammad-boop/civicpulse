"""
Read-through cache for GET /api/stats.

TTL is 30s, but we ALSO invalidate explicitly on every complaint write
(create or status update) rather than relying on the TTL alone. Reasoning,
for the engineering notes: TTL bounds staleness for the general case (nobody
writes for a while), but explicit invalidation makes a just-submitted
complaint show up in aggregates immediately — a citizen submitting a report
and then checking the dashboard should never see stale counts for up to 30s.
Either alone is defensible; together they cover both the "nobody's watching"
and "someone's watching right now" cases.
"""

import json

from redis.asyncio import Redis

_STATS_CACHE_KEY = "cache:stats"
_STATS_CACHE_TTL_SECONDS = 30


class StatsCache:
    def __init__(self, redis: Redis) -> None:
        self.redis = redis

    async def get(self) -> dict | None:
        raw = await self.redis.get(_STATS_CACHE_KEY)
        if raw is None:
            return None
        return json.loads(raw)

    async def set(self, stats: dict) -> None:
        await self.redis.set(
            _STATS_CACHE_KEY, json.dumps(stats), ex=_STATS_CACHE_TTL_SECONDS
        )

    async def invalidate(self) -> None:
        await self.redis.delete(_STATS_CACHE_KEY)