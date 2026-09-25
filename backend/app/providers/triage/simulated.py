"""
SimulatedTriage — deterministic fake for CI.
No network calls, ever. Seeded by input text so the same complaint always
produces the same result — this is what CI pins TRIAGE_PROVIDER to, so the
test suite is green on every single run regardless of what a real LLM would do.
"""

import hashlib

from app.models import Category, Priority
from app.schemas import TriageResult

_CATEGORIES = list(Category)
_PRIORITIES = list(Priority)


class SimulatedTriage:
    name = "simulated"

    def __init__(self, always_fail: bool = False, return_malformed: bool = False) -> None:
        """
        always_fail: makes triage() always raise, to test the fallback path.
        return_malformed: bypasses TriageResult validation to test the
            validator's rejection of bad LLM-shaped output.
        """
        self.always_fail = always_fail
        self.return_malformed = return_malformed

    async def triage(self, text: str, location: str) -> TriageResult:
        if self.always_fail:
            raise RuntimeError("SimulatedTriage: injected failure")

        if self.return_malformed:
            # Deliberately invalid — caller must catch the validation error.
            raise ValueError("SimulatedTriage: injected malformed output")

        # Deterministic pseudo-classification based on a hash of the text,
        # so the same complaint always triages the same way in tests.
        digest = hashlib.sha256(text.encode()).hexdigest()
        category = _CATEGORIES[int(digest[:4], 16) % len(_CATEGORIES)]
        priority = _PRIORITIES[int(digest[4:8], 16) % len(_PRIORITIES)]

        return TriageResult(
            category=category,
            priority=priority,
            summary=text.strip()[:140],
            confidence=0.9,
        )