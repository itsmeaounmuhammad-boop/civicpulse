"""
Pydantic schemas (request/response models).
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.models import Category, Priority, Status


class TriageResult(BaseModel):
    """
    The one and only shape a TriageProvider is allowed to return.
    """
    category: Category
    priority: Priority
    summary: str = Field(max_length=140)
    confidence: float = Field(ge=0.0, le=1.0)


class ComplaintCreate(BaseModel):
    text: str = Field(min_length=10, max_length=2000)
    location: str = Field(min_length=3, max_length=200)
    reporter_contact: str | None = Field(default=None, max_length=100)


class ComplaintOut(BaseModel):
    id: UUID
    text: str
    location: str
    reporter_contact: str | None
    category: Category
    priority: Priority
    status: Status
    ai_summary: str | None
    triaged_by: str
    triage_latency_ms: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ComplaintListOut(BaseModel):
    items: list[ComplaintOut]
    total: int
    page: int
    page_size: int


class StatusUpdate(BaseModel):
    status: Status


class FieldError(BaseModel):
    field: str
    message: str


class ErrorResponse(BaseModel):
    detail: str
    errors: list[FieldError] | None = None


class ProviderInfo(BaseModel):
    active_provider: str


class TriageOutcomeOut(BaseModel):
    provider: str
    latency_ms: int
    fallback: bool
    timestamp: datetime


class ProvidersMetaOut(BaseModel):
    active_provider: str
    recent_outcomes: list[TriageOutcomeOut]


class StatsOut(BaseModel):
    by_category: dict[str, int]
    by_priority: dict[str, int]
    total: int