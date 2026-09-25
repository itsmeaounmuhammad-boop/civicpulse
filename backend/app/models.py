"""
SQLAlchemy ORM models.

Schema, indexes and enums exactly as specified in the assignment brief (§2.3).
Indexes are justified in docs/ENGINEERING-NOTES.md, referencing the exact
queries each one serves.
"""

import enum
import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, Index, Integer, String, text
from sqlalchemy.dialects.postgresql import TIMESTAMP, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Category(str, enum.Enum):
    WATER = "water"
    ELECTRICITY = "electricity"
    SANITATION = "sanitation"
    ROADS = "roads"
    STREETLIGHTS = "streetlights"
    OTHER = "other"


class Priority(str, enum.Enum):
    HIGH = "high"
    NORMAL = "normal"
    LOW = "low"


class Status(str, enum.Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    REJECTED = "rejected"


class Complaint(Base):
    __tablename__ = "complaints"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )

    text: Mapped[str] = mapped_column(String(2000), nullable=False)
    location: Mapped[str] = mapped_column(String(200), nullable=False)
    reporter_contact: Mapped[str | None] = mapped_column(String(100), nullable=True)

    category: Mapped[Category] = mapped_column(String(20), nullable=False)
    priority: Mapped[Priority] = mapped_column(String(10), nullable=False)
    status: Mapped[Status] = mapped_column(
        String(20), nullable=False, server_default=Status.OPEN.value
    )

    ai_summary: Mapped[str | None] = mapped_column(String(140), nullable=True)
    triaged_by: Mapped[str] = mapped_column(String(30), nullable=False)
    triage_latency_ms: Mapped[int] = mapped_column(Integer, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=text("now()"), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        server_default=text("now()"),
        onupdate=text("now()"),
        nullable=False,
    )

    __table_args__ = (
        # Serves: GET /api/complaints?status=...&priority=... — the dashboard's
        # primary filter query, and the most frequent read this system takes.
        Index("ix_complaints_status_priority", "status", "priority"),
        # Serves: default recency ordering + pagination cursor on
        # GET /api/complaints, and any time-windowed stats aggregation.
        Index("ix_complaints_created_at", "created_at"),
        # DB-level validation, mirroring the Pydantic schema (defense in depth —
        # the assignment requires bounds enforced in the DB as well as the app).
        CheckConstraint(
            "char_length(text) >= 10 AND char_length(text) <= 2000",
            name="ck_complaints_text_length",
        ),
        CheckConstraint(
            "char_length(location) >= 3 AND char_length(location) <= 200",
            name="ck_complaints_location_length",
        ),
    )