import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import String, DateTime, Text, ForeignKey, JSON, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
import enum

from app.core.database import Base


class NewsSentiment(str, enum.Enum):
    BULLISH = "bullish"
    BEARISH = "bearish"
    NEUTRAL = "neutral"


class NewsImportance(str, enum.Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class News(Base):
    __tablename__ = "news"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    ticker: Mapped[str] = mapped_column(
        String(10), ForeignKey("stocks.ticker", ondelete="CASCADE"), index=True
    )

    # News content
    headline: Mapped[str] = mapped_column(String(500))
    summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    url: Mapped[str] = mapped_column(String(1000))
    source: Mapped[str] = mapped_column(String(100))  # "finnhub", "polygon", etc.

    # Original publish time
    published_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    # AI Analysis
    ai_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    sentiment: Mapped[Optional[NewsSentiment]] = mapped_column(
        Enum(NewsSentiment), nullable=True
    )
    importance: Mapped[Optional[NewsImportance]] = mapped_column(
        Enum(NewsImportance), nullable=True
    )
    ai_analysis: Mapped[dict] = mapped_column(JSON, default=dict)
    # ai_analysis structure:
    # {
    #   "key_points": [...],
    #   "impact_assessment": "...",
    #   "related_tickers": [...]
    # }

    # Deduplication
    content_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relationships
    stock = relationship("Stock", back_populates="news_items")
