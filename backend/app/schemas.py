"""
Pydantic schemas (request/response models).
TriageResult here; API request/response bodies added in Phase 5.
"""

from pydantic import BaseModel, Field

from app.models import Category, Priority


class TriageResult(BaseModel):
    """
    The one and only shape a TriageProvider is allowed to return.
    Every provider — LLM, Ollama, rules, simulated — must produce this,
    and callers validate against it before trusting anything from an LLM.
    """

    category: Category
    priority: Priority
    summary: str = Field(max_length=140)
    confidence: float = Field(ge=0.0, le=1.0)