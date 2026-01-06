from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel

from app.models.news import NewsSentiment, NewsImportance


class NewsCreate(BaseModel):
    ticker: str
    headline: str
    summary: Optional[str] = None
    url: str
    source: str
    published_at: datetime
    content_hash: str


class NewsResponse(BaseModel):
    id: UUID
    ticker: str
    headline: str
    summary: Optional[str] = None
    url: str
    source: str
    published_at: datetime
    ai_summary: Optional[str] = None
    sentiment: Optional[NewsSentiment] = None
    importance: Optional[NewsImportance] = None
    ai_analysis: dict = {}
    created_at: datetime

    class Config:
        from_attributes = True


class NewsListResponse(BaseModel):
    items: list[NewsResponse]
    total: int
    page: int
    page_size: int
