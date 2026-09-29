"""
ComplaintService tests — status state machine.
"""

import pytest

from app.models import Status
from app.services.complaint_service import InvalidTransitionError


@pytest.mark.asyncio
async def test_valid_transition_open_to_in_progress(client, db_session, redis_client):
    service = await _build_service(db_session, redis_client)

    complaint = await service.create_complaint(
        text="Streetlight broken for three weeks now", location="Street 5", reporter_contact=None
    )
    assert Status(complaint.status) == Status.OPEN

    updated = await service.update_status(complaint.id, Status.IN_PROGRESS)
    assert Status(updated.status) == Status.IN_PROGRESS


@pytest.mark.asyncio
async def test_invalid_transition_raises(client, db_session, redis_client):
    service = await _build_service(db_session, redis_client)

    complaint = await service.create_complaint(
        text="Garbage not collected for over a week", location="Street 9", reporter_contact=None
    )

    with pytest.raises(InvalidTransitionError):
        # open -> resolved directly is not allowed; must pass through in_progress
        await service.update_status(complaint.id, Status.RESOLVED)


@pytest.mark.asyncio
async def test_terminal_status_rejects_further_transitions(client, db_session, redis_client):
    service = await _build_service(db_session, redis_client)

    complaint = await service.create_complaint(
        text="Pothole causing accidents on main road", location="Street 3", reporter_contact=None
    )
    await service.update_status(complaint.id, Status.IN_PROGRESS)
    await service.update_status(complaint.id, Status.RESOLVED)

    with pytest.raises(InvalidTransitionError):
        await service.update_status(complaint.id, Status.IN_PROGRESS)


async def _build_service(db_session, redis_client):
    from app.providers.triage.simulated import SimulatedTriage
    from app.repositories.complaint_repository import ComplaintRepository
    from app.services.complaint_service import ComplaintService
    from app.services.stats_cache import StatsCache
    from app.services.triage_service import TriageService

    repository = ComplaintRepository(db_session)
    triage_service = TriageService(provider=SimulatedTriage(), redis=redis_client)
    stats_cache = StatsCache(redis_client)
    return ComplaintService(
        repository=repository,
        triage_service=triage_service,
        stats_cache=stats_cache,
        redis=redis_client,
    )