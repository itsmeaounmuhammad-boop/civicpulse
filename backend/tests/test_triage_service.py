"""
TriageService tests — resilience layer: fallback, caching.

Contains the assignment's explicitly-mandated test: given a provider that
always raises, the service must fall back to rules and record
triaged_by == "rules:fallback".
"""

import pytest

from app.providers.triage.simulated import SimulatedTriage
from app.services.triage_service import TriageService


@pytest.mark.asyncio
async def test_triage_service_falls_back_when_provider_always_fails(redis_client):
    failing_provider = SimulatedTriage(always_fail=True)
    service = TriageService(provider=failing_provider, redis=redis_client)

    outcome = await service.triage("Burst water main flooding the street", "Main St")

    assert outcome.was_fallback is True
    assert outcome.triaged_by == "rules:fallback"
    assert outcome.result is not None


@pytest.mark.asyncio
async def test_triage_service_caches_by_content_hash(redis_client):
    provider = SimulatedTriage()
    service = TriageService(provider=provider, redis=redis_client)

    outcome1 = await service.triage("Duplicate complaint text here", "Location A")
    assert outcome1.cache_hit is False

    outcome2 = await service.triage("Duplicate complaint text here", "Location A")
    assert outcome2.cache_hit is True
    assert outcome2.result.category == outcome1.result.category


@pytest.mark.asyncio
async def test_triage_service_does_not_cache_fallback_results(redis_client):
    failing_provider = SimulatedTriage(always_fail=True)
    service = TriageService(provider=failing_provider, redis=redis_client)

    outcome1 = await service.triage("Some complaint text", "Location B")
    assert outcome1.was_fallback is True

    # A second identical call should attempt the provider again (and fail
    # again), NOT serve a cached fallback result — confirms we never cache
    # degraded answers.
    outcome2 = await service.triage("Some complaint text", "Location B")
    assert outcome2.was_fallback is True
    assert outcome2.cache_hit is False