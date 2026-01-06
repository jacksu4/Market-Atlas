from datetime import datetime
from typing import Optional, List
from uuid import UUID

from pydantic import BaseModel


class StockCreate(BaseModel):
    ticker: str
    company_name: str
    sector: Optional[str] = None
    industry: Optional[str] = None
    cik: Optional[str] = None
    market_cap: Optional[int] = None
    exchange: Optional[str] = None


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
