"""
Complaint repository — ALL SQL for the complaints table lives here.
Routes and services must never construct a query directly.
"""

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Category, Complaint, Priority, Status


class ComplaintRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(
        self,
        *,
        text: str,
        location: str,
        reporter_contact: str | None,
        category: Category,
        priority: Priority,
        ai_summary: str | None,
        triaged_by: str,
        triage_latency_ms: int,
    ) -> Complaint:
        complaint = Complaint(
            text=text,
            location=location,
            reporter_contact=reporter_contact,
            category=category.value,
            priority=priority.value,
            status=Status.OPEN.value,
            ai_summary=ai_summary,
            triaged_by=triaged_by,
            triage_latency_ms=triage_latency_ms,
        )
        self.session.add(complaint)
        await self.session.commit()
        await self.session.refresh(complaint)
        return complaint

    async def get_by_id(self, complaint_id: UUID) -> Complaint | None:
        result = await self.session.execute(
            select(Complaint).where(Complaint.id == complaint_id)
        )
        return result.scalar_one_or_none()

    async def list(
        self,
        *,
        category: Category | None,
        priority: Priority | None,
        status: Status | None,
        page: int,
        page_size: int,
    ) -> tuple[list[Complaint], int]:
        query = select(Complaint)
        count_query = select(func.count()).select_from(Complaint)

        if category is not None:
            query = query.where(Complaint.category == category.value)
            count_query = count_query.where(Complaint.category == category.value)
        if priority is not None:
            query = query.where(Complaint.priority == priority.value)
            count_query = count_query.where(Complaint.priority == priority.value)
        if status is not None:
            query = query.where(Complaint.status == status.value)
            count_query = count_query.where(Complaint.status == status.value)

        query = query.order_by(Complaint.created_at.desc())
        query = query.offset((page - 1) * page_size).limit(page_size)

        items_result = await self.session.execute(query)
        total_result = await self.session.execute(count_query)

        items = list(items_result.scalars().all())
        total = total_result.scalar_one()
        return items, total

    async def update_status(self, complaint_id: UUID, new_status: Status) -> Complaint | None:
        complaint = await self.get_by_id(complaint_id)
        if complaint is None:
            return None
        complaint.status = new_status.value
        await self.session.commit()
        await self.session.refresh(complaint)
        return complaint

    async def stats(self) -> dict:
        category_result = await self.session.execute(
            select(Complaint.category, func.count()).group_by(Complaint.category)
        )
        priority_result = await self.session.execute(
            select(Complaint.priority, func.count()).group_by(Complaint.priority)
        )
        total_result = await self.session.execute(select(func.count()).select_from(Complaint))

        return {
            "by_category": dict(category_result.all()),
            "by_priority": dict(priority_result.all()),
            "total": total_result.scalar_one(),
        }