"""
TriageProvider unit tests — RuleBasedTriage and SimulatedTriage only,
since these are the two that never touch a network and are safe for CI.
"""

import pytest

from app.providers.triage.rules import RuleBasedTriage
from app.providers.triage.simulated import SimulatedTriage
from app.schemas import TriageResult


@pytest.mark.asyncio
async def test_rules_triage_returns_valid_result():
    provider = RuleBasedTriage()
    result = await provider.triage("Burst water main flooding the street", "Main St")
    assert isinstance(result, TriageResult)
    assert result.category.value == "water"


@pytest.mark.asyncio
async def test_rules_triage_classifies_electricity():
    provider = RuleBasedTriage()
    result = await provider.triage("Transformer sparking, very dangerous", "Block C")
    assert result.category.value == "electricity"
    assert result.priority.value == "high"


@pytest.mark.asyncio
async def test_rules_triage_falls_back_to_other_category():
    provider = RuleBasedTriage()
    result = await provider.triage("Stray dogs roaming in the park", "F-8 Park")
    assert result.category.value == "other"


@pytest.mark.asyncio
async def test_simulated_triage_is_deterministic():
    provider = SimulatedTriage()
    result1 = await provider.triage("Same complaint text", "Same location")
    result2 = await provider.triage("Same complaint text", "Same location")
    assert result1.category == result2.category
    assert result1.priority == result2.priority


@pytest.mark.asyncio
async def test_simulated_triage_always_fail_raises():
    provider = SimulatedTriage(always_fail=True)
    with pytest.raises(RuntimeError):
        await provider.triage("Any text", "Any location")