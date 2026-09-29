"""
Meta and stats routes: /api/stats and /api/meta/providers.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, Response

from app.config import Settings, get_settings
from app.dependencies import get_complaint_service
from app.schemas import ProvidersMetaOut, StatsOut, TriageOutcomeOut
from app.services.complaint_service import ComplaintService

router = APIRouter(prefix="/api", tags=["meta"])


@router.get("/stats", response_model=StatsOut)
async def get_stats(
    response: Response,
    service: Annotated[ComplaintService, Depends(get_complaint_service)],
):
    stats, was_hit = await service.get_stats()
    response.headers["X-Cache"] = "HIT" if was_hit else "MISS"
    return StatsOut(**stats)


@router.get("/meta/providers", response_model=ProvidersMetaOut)
async def get_providers_meta(
    service: Annotated[ComplaintService, Depends(get_complaint_service)],
    settings: Annotated[Settings, Depends(get_settings)],
):
    outcomes = await service.get_recent_outcomes()
    return ProvidersMetaOut(
        active_provider=settings.triage_provider,
        recent_outcomes=[TriageOutcomeOut(**outcome) for outcome in outcomes],
    )