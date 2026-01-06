from datetime import datetime
from typing import Optional, List
from uuid import UUID
import re

from pydantic import BaseModel, field_validator


class StockCreate(BaseModel):
    ticker: str
    company_name: str
    sector: Optional[str] = None
    industry: Optional[str] = None
    cik: Optional[str] = None
    market_cap: Optional[int] = None
    exchange: Optional[str] = None

    @field_validator("ticker")
    @classmethod
    def validate_ticker(cls, v: str) -> str:
        """Validate stock ticker format"""
        v = v.strip().upper()

        if not v:
            raise ValueError("Ticker cannot be empty")

        if len(v) > 10:
            raise ValueError("Ticker must be 10 characters or less")

        if not re.match(r"^[A-Z0-9.\-]+$", v):
            raise ValueError(
                "Ticker must contain only uppercase letters, numbers, hyphens, or periods"
            )

        return v


class StockResponse(BaseModel):
    ticker: str
    company_name: str
    sector: Optional[str] = None
    industry: Optional[str] = None
    cik: Optional[str] = None
    market_cap: Optional[int] = None
    exchange: Optional[str] = None
    metadata_: dict = {}
    last_updated: datetime

    class Config:
        from_attributes = True


class WatchlistItemCreate(BaseModel):
    ticker: str
    notes: Optional[str] = None

    @field_validator("ticker")
    @classmethod
    def validate_ticker(cls, v: str) -> str:
        """
        Validate stock ticker format:
        - 1-5 characters
        - Uppercase letters and optionally numbers
        - Some tickers may have hyphens (e.g., BRK-A)
        """
        v = v.strip().upper()

        if not v:
            raise ValueError("Ticker cannot be empty")

        if len(v) > 10:
            raise ValueError("Ticker must be 10 characters or less")

        # Allow letters, numbers, hyphens, and periods (for some international tickers)
        if not re.match(r"^[A-Z0-9.\-]+$", v):
            raise ValueError(
                "Ticker must contain only uppercase letters, numbers, hyphens, or periods"
            )

        return v


class WatchlistItemResponse(BaseModel):
    id: UUID
    ticker: str
    notes: Optional[str] = None
    added_at: datetime
    stock: Optional[StockResponse] = None

    class Config:
        from_attributes = True


class WatchlistCreate(BaseModel):
    name: str = "My Watchlist"
    description: Optional[str] = None


class WatchlistResponse(BaseModel):
    id: UUID
    name: str
    description: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    items: List[WatchlistItemResponse] = []

    class Config:
        from_attributes = True


class WatchlistUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
