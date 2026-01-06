from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.models.user import User
from app.models.watchlist import Watchlist, WatchlistItem
from app.models.stock import Stock
from app.schemas.watchlist import (
    WatchlistCreate,
    WatchlistResponse,
    WatchlistUpdate,
    WatchlistItemCreate,
    WatchlistItemResponse,
)
from app.api.deps import get_current_user
from app.services.stock_service import get_or_create_stock

router = APIRouter()


@router.get("", response_model=List[WatchlistResponse])
async def list_watchlists(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Watchlist)
        .where(Watchlist.user_id == current_user.id)
        .options(selectinload(Watchlist.items).selectinload(WatchlistItem.stock))
        .order_by(Watchlist.created_at.desc())
    )
    watchlists = result.scalars().all()
    return watchlists


@router.post("", response_model=WatchlistResponse, status_code=status.HTTP_201_CREATED)
async def create_watchlist(
    watchlist_in: WatchlistCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    watchlist = Watchlist(
        user_id=current_user.id,
        name=watchlist_in.name,
        description=watchlist_in.description,
    )
    db.add(watchlist)
    await db.commit()
    await db.refresh(watchlist)
    return watchlist


@router.get("/{watchlist_id}", response_model=WatchlistResponse)
async def get_watchlist(
    watchlist_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Watchlist)
        .where(Watchlist.id == watchlist_id, Watchlist.user_id == current_user.id)
        .options(selectinload(Watchlist.items).selectinload(WatchlistItem.stock))
    )
    watchlist = result.scalar_one_or_none()

    if not watchlist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Watchlist not found",
        )

    return watchlist


@router.patch("/{watchlist_id}", response_model=WatchlistResponse)
async def update_watchlist(
    watchlist_id: UUID,
    watchlist_in: WatchlistUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Watchlist).where(
            Watchlist.id == watchlist_id, Watchlist.user_id == current_user.id
        )
    )
    watchlist = result.scalar_one_or_none()

    if not watchlist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Watchlist not found",
        )

    if watchlist_in.name is not None:
        watchlist.name = watchlist_in.name
    if watchlist_in.description is not None:
        watchlist.description = watchlist_in.description

    await db.commit()
    await db.refresh(watchlist)
    return watchlist


@router.delete("/{watchlist_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_watchlist(
    watchlist_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Watchlist).where(
            Watchlist.id == watchlist_id, Watchlist.user_id == current_user.id
        )
    )
    watchlist = result.scalar_one_or_none()

    if not watchlist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Watchlist not found",
        )

    await db.delete(watchlist)
    await db.commit()


@router.post("/{watchlist_id}/items", response_model=WatchlistItemResponse, status_code=status.HTTP_201_CREATED)
async def add_stock_to_watchlist(
    watchlist_id: UUID,
    item_in: WatchlistItemCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Verify watchlist ownership
    result = await db.execute(
        select(Watchlist).where(
            Watchlist.id == watchlist_id, Watchlist.user_id == current_user.id
        )
    )
    watchlist = result.scalar_one_or_none()

    if not watchlist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Watchlist not found",
        )

    # Check if stock already in watchlist
    result = await db.execute(
        select(WatchlistItem).where(
            WatchlistItem.watchlist_id == watchlist_id,
            WatchlistItem.ticker == item_in.ticker.upper(),
        )
    )
    existing_item = result.scalar_one_or_none()

    if existing_item:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Stock already in watchlist",
        )

    # Get or create stock
    stock = await get_or_create_stock(db, item_in.ticker.upper())

    # Create watchlist item
    item = WatchlistItem(
        watchlist_id=watchlist_id,
        ticker=stock.ticker,
        notes=item_in.notes,
    )
    db.add(item)
    await db.commit()
    await db.refresh(item)

    # Trigger news fetch for this ticker (async via Celery)
    from app.tasks.news_tasks import fetch_news_for_ticker
    fetch_news_for_ticker.delay(stock.ticker)

    # Load stock relationship
    result = await db.execute(
        select(WatchlistItem)
        .where(WatchlistItem.id == item.id)
        .options(selectinload(WatchlistItem.stock))
    )
    item = result.scalar_one()

    return item


@router.delete("/{watchlist_id}/items/{ticker}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_stock_from_watchlist(
    watchlist_id: UUID,
    ticker: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Verify watchlist ownership
    result = await db.execute(
        select(Watchlist).where(
            Watchlist.id == watchlist_id, Watchlist.user_id == current_user.id
        )
    )
    watchlist = result.scalar_one_or_none()

    if not watchlist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Watchlist not found",
        )

    # Find and delete item
    result = await db.execute(
        select(WatchlistItem).where(
            WatchlistItem.watchlist_id == watchlist_id,
            WatchlistItem.ticker == ticker.upper(),
        )
    )
    item = result.scalar_one_or_none()

    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Stock not found in watchlist",
        )

    await db.delete(item)
    await db.commit()
