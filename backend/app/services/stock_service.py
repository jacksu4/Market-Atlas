from typing import Optional
import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.stock import Stock
from app.core.config import settings


async def get_or_create_stock(db: AsyncSession, ticker: str) -> Stock:
    """Get stock from database or fetch from API and create"""
    ticker = ticker.upper()

    # Check if stock exists
    result = await db.execute(select(Stock).where(Stock.ticker == ticker))
    stock = result.scalar_one_or_none()

    if stock:
        return stock

    # Fetch stock info from Finnhub
    stock_info = await fetch_stock_info(ticker)

    # Create stock
    stock = Stock(
        ticker=ticker,
        company_name=stock_info.get("name", ticker),
        sector=stock_info.get("finnhubIndustry"),
        exchange=stock_info.get("exchange"),
        market_cap=stock_info.get("marketCapitalization"),
        metadata_={
            "website": stock_info.get("weburl"),
            "country": stock_info.get("country"),
            "ipo_date": stock_info.get("ipo"),
            "logo": stock_info.get("logo"),
        },
    )

    # Try to get CIK from SEC
    cik = await fetch_sec_cik(ticker)
    if cik:
        stock.cik = cik

    db.add(stock)
    await db.commit()
    await db.refresh(stock)

    return stock


async def fetch_stock_info(ticker: str) -> dict:
    """Fetch stock profile from Finnhub API"""
    if not settings.FINNHUB_API_KEY:
        return {"name": ticker}

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://finnhub.io/api/v1/stock/profile2",
                params={"symbol": ticker, "token": settings.FINNHUB_API_KEY},
                timeout=10.0,
            )
            if response.status_code == 200:
                data = response.json()
                if data:
                    return data
    except Exception:
        pass

    return {"name": ticker}


async def fetch_sec_cik(ticker: str) -> Optional[str]:
    """Fetch CIK number from SEC EDGAR"""
    try:
        async with httpx.AsyncClient() as client:
            # SEC provides a ticker -> CIK mapping
            response = await client.get(
                "https://www.sec.gov/cgi-bin/browse-edgar",
                params={
                    "action": "getcompany",
                    "CIK": ticker,
                    "type": "",
                    "dateb": "",
                    "owner": "include",
                    "count": "1",
                    "output": "atom",
                },
                headers={"User-Agent": "Market-Atlas research@example.com"},
                timeout=10.0,
            )
            if response.status_code == 200:
                # Parse CIK from response
                content = response.text
                if "CIK=" in content:
                    import re
                    match = re.search(r"CIK=(\d+)", content)
                    if match:
                        return match.group(1).zfill(10)
    except Exception:
        pass

    return None


async def search_stocks(query: str, limit: int = 10) -> list[dict]:
    """Search for stocks using Finnhub symbol search"""
    if not settings.FINNHUB_API_KEY:
        return []

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://finnhub.io/api/v1/search",
                params={"q": query, "token": settings.FINNHUB_API_KEY},
                timeout=10.0,
            )
            if response.status_code == 200:
                data = response.json()
                results = data.get("result", [])[:limit]
                return [
                    {
                        "ticker": r.get("symbol"),
                        "name": r.get("description"),
                        "type": r.get("type"),
                    }
                    for r in results
                    if r.get("symbol") and r.get("type") == "Common Stock"
                ]
    except Exception:
        pass

    return []
