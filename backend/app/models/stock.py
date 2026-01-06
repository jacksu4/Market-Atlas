from datetime import datetime
from typing import Optional

from sqlalchemy import String, DateTime, JSON, Float, BigInteger
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.core.database import Base


class Stock(Base):
    __tablename__ = "stocks"

    ticker: Mapped[str] = mapped_column(String(10), primary_key=True)
    company_name: Mapped[str] = mapped_column(String(255))
    sector: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    industry: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # SEC identifier
    cik: Mapped[Optional[str]] = mapped_column(String(20), nullable=True, index=True)

    # Market data
    market_cap: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    exchange: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Additional metadata as JSON
    metadata_: Mapped[dict] = mapped_column("metadata", JSON, default=dict)
    # metadata structure:
    # {
    #   "website": "https://...",
    #   "description": "...",
    #   "employees": 10000,
    #   "country": "US",
    #   "ipo_date": "1980-12-12"
    # }

    last_updated: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    watchlist_items = relationship("WatchlistItem", back_populates="stock", lazy="selectin")
    news_items = relationship("News", back_populates="stock", lazy="selectin")
    filings = relationship("Filing", back_populates="stock", lazy="selectin")
