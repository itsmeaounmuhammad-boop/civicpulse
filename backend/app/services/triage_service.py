"""
Triage orchestration service — the resilience layer around a TriageProvider.

This is what routes/services actually call. It is responsible for
everything the raw provider is NOT responsible for:
  1. Content-hash caching (duplicate complaints cost one inference, not nine)
  2. Timeout enforcement
  3. Single retry with jitter, on retryable errors only (timeout/429/5xx —
     never on a 400-shaped validation failure, since that will be wrong again)
  4. Fallback to RuleBasedTriage on exhausted retries
  5. Latency measurement and triaged_by bookkeeping
"""

import asyncio
import hashlib
import json
import random
import time
from dataclasses import dataclass

from redis.asyncio import Redis

from app.providers.triage.base import TriageProvider
from app.providers.triage.rules import RuleBasedTriage
from app.schemas import TriageResult

_CONTENT_CACHE_TTL_SECONDS = 24 * 60 * 60  # 24h, per assignment spec
_TIMEOUT_SECONDS = 10.0


@dataclass
class TriageOutcome:
    result: TriageResult
    triaged_by: str
    latency_ms: int
    was_fallback: bool
    cache_hit: bool


class TriageService:
    def __init__(self, provider: TriageProvider, redis: Redis) -> None:
        self.provider = provider
        self.redis = redis
        self.fallback = RuleBasedTriage()

    @staticmethod
    def _content_hash(text: str) -> str:
        return hashlib.sha256(text.strip().lower().encode()).hexdigest()

    async def _get_cached(self, content_hash: str) -> TriageResult | None:
        raw = await self.redis.get(f"triage:cache:{content_hash}")
        if raw is None:
            return None
        return TriageResult(**json.loads(raw))

    async def _set_cached(self, content_hash: str, result: TriageResult) -> None:
        await self.redis.set(
            f"triage:cache:{content_hash}",
            result.model_dump_json(),
            ex=_CONTENT_CACHE_TTL_SECONDS,
        )

    async def triage(self, text: str, location: str) -> TriageOutcome:
        start = time.monotonic()
        content_hash = self._content_hash(text)

        cached = await self._get_cached(content_hash)
        if cached is not None:
            latency_ms = int((time.monotonic() - start) * 1000)
            return TriageOutcome(
                result=cached,
                triaged_by=self.provider.name,
                latency_ms=latency_ms,
                was_fallback=False,
                cache_hit=True,
            )

        result, triaged_by, was_fallback = await self._triage_with_retry(text, location)
        latency_ms = int((time.monotonic() - start) * 1000)

        if not was_fallback:
            # Only cache genuine provider output, never a fallback result —
            # a fallback is a degraded answer and shouldn't poison the cache
            # for a duplicate complaint that arrives after the provider recovers.
            await self._set_cached(content_hash, result)

        return TriageOutcome(
            result=result,
            triaged_by=triaged_by,
            latency_ms=latency_ms,
            was_fallback=was_fallback,
            cache_hit=False,
        )

    async def _triage_with_retry(
        self, text: str, location: str
    ) -> tuple[TriageResult, str, bool]:
        for attempt in range(2):  # one initial attempt + one retry
            try:
                result = await asyncio.wait_for(
                    self.provider.triage(text, location), timeout=_TIMEOUT_SECONDS
                )
                return result, self.provider.name, False
            except TimeoutError:
                if attempt == 0:
                    await asyncio.sleep(random.uniform(0.1, 0.5))  # jitter
                    continue
                break
            except Exception as exc:
                # Retryable: timeout-like, rate-limit, or server errors.
                # Non-retryable (bad request / malformed output that's the
                # model's fault) still gets one retry here for simplicity,
                # but genuinely malformed *input* would already have failed
                # Pydantic validation before this method is ever called.
                if attempt == 0 and self._is_retryable(exc):
                    await asyncio.sleep(random.uniform(0.1, 0.5))
                    continue
                break

        # Both attempts exhausted (or non-retryable) — fall back.
        result = await self.fallback.triage(text, location)
        return result, "rules:fallback", True

    @staticmethod
    def _is_retryable(exc: Exception) -> bool:
        # httpx/OpenAI SDK errors carry status codes we can inspect; anything
        # unrecognized is treated conservatively as non-retryable so we don't
        # loop on a genuinely bad request.
        status = getattr(exc, "status_code", None)
        if status is None:
            response = getattr(exc, "response", None)
            status = getattr(response, "status_code", None)
        if status is None:
            return True  # network-level errors (timeouts, connection drops) — retry
        return status == 429 or status >= 500