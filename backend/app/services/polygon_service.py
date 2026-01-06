import hashlib
from datetime import datetime, timezone, timedelta
from typing import List, Optional
import httpx

from app.core.config import settings


class PolygonService:
    BASE_URL = "https://api.polygon.io"

    def __init__(self):
        self.api_key = settings.POLYGON_API_KEY

    async def get_ticker_news(
        self,
        ticker: str,
        limit: int = 50,
        published_utc_gte: Optional[str] = None,
    ) -> List[dict]:
        """
        Get news for a specific ticker from Polygon.
        published_utc_gte format: YYYY-MM-DD
        """
        if not self.api_key:
            return []

        params = {
            "ticker": ticker.upper(),
            "limit": limit,
            "apiKey": self.api_key,
        }

        if published_utc_gte:
            params["published_utc.gte"] = published_utc_gte

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.BASE_URL}/v2/reference/news",
                    params=params,
                    timeout=15.0,
                )

                if response.status_code == 200:
                    data = response.json()
                    results = data.get("results", [])
                    return [self._transform_news_item(item, ticker) for item in results]
        except Exception as e:
            print(f"Error fetching Polygon news for {ticker}: {e}")

        return []

    async def get_ticker_details(self, ticker: str) -> Optional[dict]:
        """Get detailed information about a ticker"""
        if not self.api_key:
            return None

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.BASE_URL}/v3/reference/tickers/{ticker.upper()}",
                    params={"apiKey": self.api_key},
                    timeout=15.0,
                )

                if response.status_code == 200:
                    data = response.json()
                    return data.get("results")
        except Exception as e:
            print(f"Error fetching Polygon ticker details for {ticker}: {e}")

        return None

    async def get_financials(self, ticker: str, limit: int = 4) -> List[dict]:
        """Get financial statements for a ticker"""
        if not self.api_key:
            return []

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.BASE_URL}/vX/reference/financials",
                    params={
                        "ticker": ticker.upper(),
                        "limit": limit,
                        "apiKey": self.api_key,
                    },
                    timeout=15.0,
                )

                if response.status_code == 200:
                    data = response.json()
                    return data.get("results", [])
        except Exception as e:
            print(f"Error fetching Polygon financials for {ticker}: {e}")

        return []

    def _transform_news_item(self, item: dict, ticker: str) -> dict:
        """Transform Polygon news item to our format"""
        headline = item.get("title", "")
        url = item.get("article_url", "")

        # Create content hash for deduplication
        content_hash = hashlib.sha256(
            f"{headline}{url}".encode()
        ).hexdigest()

        # Parse published_utc
        published_utc = item.get("published_utc", "")
        try:
            published_at = datetime.fromisoformat(published_utc.replace("Z", "+00:00"))
        except:
            published_at = datetime.now(timezone.utc)

        return {
            "ticker": ticker.upper(),
            "headline": headline,
            "summary": item.get("description"),
            "url": url,
            "source": item.get("publisher", {}).get("name", "polygon"),
            "published_at": published_at,
            "content_hash": content_hash,
            "raw_data": item,
        }


polygon_service = PolygonService()
