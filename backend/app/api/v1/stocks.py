from typing import List
from fastapi import APIRouter, Depends, Query

from app.models.user import User
from app.api.deps import get_current_user
from app.services.stock_service import search_stocks
from pydantic import BaseModel


router = APIRouter()


class StockSearchResult(BaseModel):
    ticker: str
    name: str | None
    type: str | None


@router.get("/search", response_model=List[StockSearchResult])
async def search_stocks_endpoint(
    q: str = Query(..., min_length=1, description="Search query (ticker or company name)"),
    limit: int = Query(10, ge=1, le=50),
    current_user: User = Depends(get_current_user),
):
    """Search for stocks by ticker or company name using Finnhub API"""
    results = await search_stocks(q, limit)
    return results
