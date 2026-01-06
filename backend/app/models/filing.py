import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import String, DateTime, Text, ForeignKey, JSON, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
import enum

from app.core.database import Base


class FilingType(str, enum.Enum):
    FORM_10K = "10-K"
    FORM_10Q = "10-Q"
    FORM_8K = "8-K"
    FORM_DEF14A = "DEF 14A"
    FORM_S1 = "S-1"
    FORM_4 = "4"
    OTHER = "OTHER"


class FilingStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    ANALYZED = "analyzed"
    FAILED = "failed"


class Filing(Base):
    __tablename__ = "filings"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    ticker: Mapped[str] = mapped_column(
        String(10), ForeignKey("stocks.ticker", ondelete="CASCADE"), index=True
    )

    # Filing metadata
    filing_type: Mapped[FilingType] = mapped_column(Enum(FilingType))
    accession_number: Mapped[str] = mapped_column(String(30), unique=True, index=True)
    filed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    period_of_report: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # SEC URLs
    filing_url: Mapped[str] = mapped_column(String(500))
    document_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # Processing status
    status: Mapped[FilingStatus] = mapped_column(
        Enum(FilingStatus), default=FilingStatus.PENDING
    )

    # AI Analysis
    ai_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    ai_analysis: Mapped[dict] = mapped_column(JSON, default=dict)
    # ai_analysis structure for 10-K/10-Q:
    # {
    #   "key_financials": {...},
    #   "risk_factors_changes": [...],
    #   "mda_highlights": [...],
    #   "guidance": {...},
    #   "notable_changes": [...]
    # }

    # Raw extracted text (stored for reference)
    raw_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    analyzed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Relationships
    stock = relationship("Stock", back_populates="filings")
