"""
TriageProvider interface. Every triage implementation (LLM, Ollama, rules,
simulated) satisfies this Protocol, so the service layer that calls triage()
never knows or cares which concrete provider is behind it.
"""

from typing import Protocol

from app.schemas import TriageResult


class TriageProvider(Protocol):
    name: str

    async def triage(self, text: str, location: str) -> TriageResult:
        """
        Classify a complaint. Must return a valid TriageResult or raise —
        never return a malformed/partial result. Callers (the triage service
        in Phase 5) are responsible for timeout, retry, and fallback around
        this call; a provider itself just does one honest attempt.
        """
        ...