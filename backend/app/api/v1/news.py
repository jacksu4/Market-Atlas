from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.user import User
from app.models.news import News
from app.models.watchlist import Watchlist, WatchlistItem
from app.schemas.news import NewsResponse, NewsListResponse
from app.api.deps import get_current_user

router = APIRouter()


@router.get("", response_model=NewsListResponse)
async def list_news(
    ticker: Optional[str] = None,
    watchlist_id: Optional[UUID] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Build query
    query = select(News)

    if ticker:
        query = query.where(News.ticker == ticker.upper())
    elif watchlist_id:
        # Get tickers from watchlist
        result = await db.execute(
            select(WatchlistItem.ticker).where(
                WatchlistItem.watchlist_id == watchlist_id
            )
        )
        tickers = [row[0] for row in result.fetchall()]
        if tickers:
            query = query.where(News.ticker.in_(tickers))
        else:
            return NewsListResponse(items=[], total=0, page=page, page_size=page_size)

    # Count total
    count_query = select(News.id)
    if ticker:
        count_query = count_query.where(News.ticker == ticker.upper())
    elif watchlist_id and tickers:
        count_query = count_query.where(News.ticker.in_(tickers))

    count_result = await db.execute(count_query)
    total = len(count_result.fetchall())

    # Get paginated results
    query = (
        query.order_by(desc(News.published_at))
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    result = await db.execute(query)
    news_items = result.scalars().all()

    return NewsListResponse(
        items=news_items,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{news_id}", response_model=NewsResponse)
async def get_news_item(
    news_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(News).where(News.id == news_id))
    news_item = result.scalar_one_or_none()

    if not news_item:
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="News item not found",
        )

    return news_item


@router.get("/ticker/{ticker}", response_model=List[NewsResponse])
async def get_news_for_ticker(
    ticker: str,
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(News)
        .where(News.ticker == ticker.upper())
        .order_by(desc(News.published_at))
        .limit(limit)
    )
    news_items = result.scalars().all()
    return news_items
