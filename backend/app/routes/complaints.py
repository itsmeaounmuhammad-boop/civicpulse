"""
Complaint routes — HTTP only: parse, validate, serialize, status codes.
No business rules here (those live in ComplaintService).
"""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request

from app.dependencies import get_complaint_service, get_rate_limiter
from app.models import Category, Priority, Status
from app.schemas import ComplaintCreate, ComplaintListOut, ComplaintOut, StatusUpdate
from app.services.complaint_service import (
    ComplaintNotFoundError,
    ComplaintService,
    InvalidTransitionError,
)
from app.services.rate_limiter import RateLimitExceeded, RedisRateLimiter

router = APIRouter(prefix="/api/complaints", tags=["complaints"])


@router.post("", response_model=ComplaintOut, status_code=201)
async def create_complaint(
    body: ComplaintCreate,
    request: Request,
    service: Annotated[ComplaintService, Depends(get_complaint_service)],
    rate_limiter: Annotated[RedisRateLimiter, Depends(get_rate_limiter)],
):
    client_ip = request.client.host if request.client else "unknown"
    try:
        await rate_limiter.check(client_ip)
    except RateLimitExceeded as exc:
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded",
            headers={"Retry-After": str(exc.retry_after_seconds)},
        ) from exc

    return await service.create_complaint(
        text=body.text, location=body.location, reporter_contact=body.reporter_contact
    )


@router.get("/{complaint_id}", response_model=ComplaintOut)
async def get_complaint(
    complaint_id: UUID,
    service: Annotated[ComplaintService, Depends(get_complaint_service)],
):
    try:
        return await service.get_complaint(complaint_id)
    except ComplaintNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Complaint not found") from exc


@router.get("", response_model=ComplaintListOut)
async def list_complaints(
    service: Annotated[ComplaintService, Depends(get_complaint_service)],
    category: Category | None = None,
    priority: Priority | None = None,
    status: Status | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
):
    items, total = await service.list_complaints(
        category=category, priority=priority, status=status,
        page=page, page_size=page_size,
    )
    return ComplaintListOut(items=items, total=total, page=page, page_size=page_size)


@router.patch("/{complaint_id}/status", response_model=ComplaintOut)
async def update_status(
    complaint_id: UUID,
    body: StatusUpdate,
    service: Annotated[ComplaintService, Depends(get_complaint_service)],
):
    try:
        return await service.update_status(complaint_id, body.status)
    except ComplaintNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Complaint not found") from exc
    except InvalidTransitionError as exc:
        raise HTTPException(
            status_code=409,
            detail=f"Cannot transition from '{exc.current.value}' to '{exc.attempted.value}'",
        ) from exc