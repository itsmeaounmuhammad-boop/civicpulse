"""
Complaint service — business rules. Routes call this; this calls the
repository (persistence) and the triage service (AI orchestration).
No SQL here, no HTTP concerns here.
"""

import json
from datetime import UTC, datetime
from uuid import UUID

from redis.asyncio import Redis

from app.models import Category, Priority, Status
from app.repositories.complaint_repository import ComplaintRepository
from app.services.stats_cache import StatsCache
from app.services.triage_service import TriageService

# Explicit transition table — the assignment specifically requires this
# over a chain of if-statements, so an invalid transition is a single
# dict lookup away from a clear 409, not buried in branching logic.
_ALLOWED_TRANSITIONS: dict[Status, set[Status]] = {
    Status.OPEN: {Status.IN_PROGRESS, Status.REJECTED},
    Status.IN_PROGRESS: {Status.RESOLVED, Status.REJECTED},
    Status.RESOLVED: set(),
    Status.REJECTED: set(),
}

_RECENT_OUTCOMES_KEY = "triage:recent_outcomes"
_RECENT_OUTCOMES_MAX = 20


class InvalidTransitionError(Exception):
    def __init__(self, current: Status, attempted: Status) -> None:
        self.current = current
        self.attempted = attempted
        super().__init__(
            f"Cannot transition from '{current.value}' to '{attempted.value}'"
        )


class ComplaintNotFoundError(Exception):
    pass


class ComplaintService:
    def __init__(
        self,
        repository: ComplaintRepository,
        triage_service: TriageService,
        stats_cache: StatsCache,
        redis: Redis,
    ) -> None:
        self.repository = repository
        self.triage_service = triage_service
        self.stats_cache = stats_cache
        self.redis = redis

    async def create_complaint(self, *, text: str, location: str, reporter_contact: str | None):
        outcome = await self.triage_service.triage(text, location)

        complaint = await self.repository.create(
            text=text,
            location=location,
            reporter_contact=reporter_contact,
            category=outcome.result.category,
            priority=outcome.result.priority,
            ai_summary=outcome.result.summary,
            triaged_by=outcome.triaged_by,
            triage_latency_ms=outcome.latency_ms,
        )

        await self._record_outcome(outcome)
        await self.stats_cache.invalidate()  # newly submitted complaint must appear immediately

        return complaint

    async def get_complaint(self, complaint_id: UUID):
        complaint = await self.repository.get_by_id(complaint_id)
        if complaint is None:
            raise ComplaintNotFoundError()
        return complaint

    async def list_complaints(
        self,
        *,
        category: Category | None,
        priority: Priority | None,
        status: Status | None,
        page: int,
        page_size: int,
    ):
        return await self.repository.list(
            category=category, priority=priority, status=status,
            page=page, page_size=page_size,
        )

    async def update_status(self, complaint_id: UUID, new_status: Status):
        complaint = await self.repository.get_by_id(complaint_id)
        if complaint is None:
            raise ComplaintNotFoundError()

        current_status = Status(complaint.status)
        if new_status not in _ALLOWED_TRANSITIONS[current_status]:
            raise InvalidTransitionError(current=current_status, attempted=new_status)

        updated = await self.repository.update_status(complaint_id, new_status)
        await self.stats_cache.invalidate()  # status change affects aggregates too
        return updated

    async def get_stats(self) -> tuple[dict, bool]:
        """Returns (stats, was_cache_hit)."""
        cached = await self.stats_cache.get()
        if cached is not None:
            return cached, True

        stats = await self.repository.stats()
        await self.stats_cache.set(stats)
        return stats, False

    async def _record_outcome(self, outcome) -> None:
        entry = {
            "provider": outcome.triaged_by,
            "latency_ms": outcome.latency_ms,
            "fallback": outcome.was_fallback,
            "timestamp": datetime.now(UTC).isoformat(),
        }
        await self.redis.lpush(_RECENT_OUTCOMES_KEY, json.dumps(entry))
        await self.redis.ltrim(_RECENT_OUTCOMES_KEY, 0, _RECENT_OUTCOMES_MAX - 1)

    async def get_recent_outcomes(self) -> list[dict]:
        raw_entries = await self.redis.lrange(_RECENT_OUTCOMES_KEY, 0, _RECENT_OUTCOMES_MAX - 1)
        return [json.loads(entry) for entry in raw_entries]