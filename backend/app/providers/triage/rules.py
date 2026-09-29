"""
RuleBasedTriage — deterministic keyword classifier.
This is the fallback every other provider falls back to. It must never raise
and never depend on the network, since its entire job is to work when
everything else has failed.
"""

from app.models import Category, Priority
from app.schemas import TriageResult

# Ordered by specificity — first match wins. Keep water/electricity/sanitation
# checks before the generic "roads" and "streetlights" ones since complaint
# text often mentions a road in passing ("water main under the road").
_CATEGORY_KEYWORDS: list[tuple[Category, list[str]]] = [
    (Category.WATER, ["water", "burst main", "pipe", "leak", "sewerage", "flood"]),
    (Category.ELECTRICITY, ["electric", "bijli", "transformer", "wapda", "voltage", "wire", "power"]),
    (Category.SANITATION, ["garbage", "sewer", "drain", "sanitation", "trash", "waste", "sfai", "kachra"]),
    (Category.STREETLIGHTS, ["streetlight", "street light", "pole", "lamp"]),
    (Category.ROADS, ["road", "pothole", "footpath", "traffic", "manhole", "speed breaker"]),
]

_HIGH_URGENCY_WORDS = [
    "flood", "spark", "danger", "khatarnak", "accident", "leak", "fire",
    "gir", "collapsed", "burst", "urgent", "emergency",
]

_LOW_URGENCY_WORDS = [
    "flicker", "slow", "minor", "cosmetic", "overgrown", "paint",
]


def _classify_category(text: str) -> Category:
    lowered = text.lower()
    for category, keywords in _CATEGORY_KEYWORDS:
        if any(kw in lowered for kw in keywords):
            return category
    return Category.OTHER


def _classify_priority(text: str) -> Priority:
    lowered = text.lower()
    if any(kw in lowered for kw in _HIGH_URGENCY_WORDS):
        return Priority.HIGH
    if any(kw in lowered for kw in _LOW_URGENCY_WORDS):
        return Priority.LOW
    return Priority.NORMAL


def _summarize(text: str, category: Category) -> str:
    snippet = text.strip().replace("\n", " ")
    summary = f"{category.value.capitalize()} issue: {snippet}"
    return summary[:140]


class RuleBasedTriage:
    name = "rules"

    async def triage(self, text: str, location: str) -> TriageResult:
        category = _classify_category(text)
        priority = _classify_priority(text)
        summary = _summarize(text, category)
        return TriageResult(
            category=category,
            priority=priority,
            summary=summary,
            confidence=0.5,  # rules are a reasonable guess, never a confident one
        )