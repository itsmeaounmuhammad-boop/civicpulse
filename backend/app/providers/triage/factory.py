"""
Provider factory — the ONLY place that reads TRIAGE_PROVIDER and decides
which concrete TriageProvider to instantiate. Nothing else in the app
should branch on this setting.
"""

from app.config import Settings
from app.providers.triage.base import TriageProvider
from app.providers.triage.llm import LLMTriage
from app.providers.triage.ollama import OllamaTriage
from app.providers.triage.rules import RuleBasedTriage
from app.providers.triage.simulated import SimulatedTriage


def get_triage_provider(settings: Settings) -> TriageProvider:
    if settings.triage_provider == "llm":
        return LLMTriage(api_key=settings.groq_api_key, model=settings.groq_model)
    if settings.triage_provider == "ollama":
        return OllamaTriage(base_url=settings.ollama_base_url, model=settings.ollama_model)
    if settings.triage_provider == "rules":
        return RuleBasedTriage()
    if settings.triage_provider == "simulated":
        return SimulatedTriage()

    raise ValueError(f"Unknown TRIAGE_PROVIDER: {settings.triage_provider!r}")