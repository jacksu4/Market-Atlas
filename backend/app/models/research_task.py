import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import String, DateTime, Text, ForeignKey, JSON, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
import enum

from app.core.database import Base


class TaskType(str, enum.Enum):
    DISCOVERY = "discovery"  # AI stock discovery
    DEEP_DIVE = "deep_dive"  # Deep research on a specific stock
    EARNINGS_ANALYSIS = "earnings_analysis"  # Earnings call analysis
    FILING_ANALYSIS = "filing_analysis"  # SEC filing analysis
    COMPARATIVE = "comparative"  # Compare multiple stocks


class TaskStatus(str, enum.Enum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ResearchTask(Base):
    __tablename__ = "research_tasks"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True
    )

    # Task configuration
    task_type: Mapped[TaskType] = mapped_column(Enum(TaskType))
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Input parameters (JSON)
    parameters: Mapped[dict] = mapped_column(JSON, default=dict)
    # For DISCOVERY:
    # {
    #   "theme": "AI infrastructure",
    #   "market_cap_min": 1000000000,
    #   "market_cap_max": 50000000000,
    #   "sectors": ["Technology"],
    #   "criteria": "..."
    # }
    # For DEEP_DIVE:
    # {
    #   "ticker": "NVDA",
    #   "focus_areas": ["financials", "competition", "growth"]
    # }

    # Status
    status: Mapped[TaskStatus] = mapped_column(Enum(TaskStatus), default=TaskStatus.QUEUED)
    progress: Mapped[int] = mapped_column(default=0)  # 0-100
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Results (JSON)
    results: Mapped[dict] = mapped_column(JSON, default=dict)
    # For DISCOVERY:
    # {
    #   "candidates": [
    #     {
    #       "ticker": "...",
    #       "company_name": "...",
    #       "score": 85,
    #       "summary": "...",
    #       "key_points": [...]
    #     }
    #   ],
    #   "methodology": "..."
    # }

    # Celery task ID for tracking
    celery_task_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # Notification sent
    notification_sent: Mapped[bool] = mapped_column(default=False)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    started_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Relationships
    user = relationship("User", back_populates="research_tasks")
