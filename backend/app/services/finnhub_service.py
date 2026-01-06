import hashlib
from datetime import datetime, timezone
from typing import List, Optional
import httpx

from app.core.config import settings


class FinnhubService:
    BASE_URL = "https://finnhub.io/api/v1"

    def __init__(self):
        self.api_key = settings.FINNHUB_API_KEY

    async def get_company_news(
        self,
        ticker: str,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
    ) -> List[dict]:
        """
        Get company news from Finnhub.
        from_date and to_date format: YYYY-MM-DD
        """
        if not self.api_key:
            return []

        if not from_date:
            from_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        if not to_date:
            to_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.BASE_URL}/company-news",
                    params={
                        "symbol": ticker.upper(),
                        "from": from_date,
                        "to": to_date,
                        "token": self.api_key,
                    },
                    timeout=15.0,
                )

                if response.status_code == 200:
                    news_items = response.json()
                    return [self._transform_news_item(item, ticker) for item in news_items]
        except Exception as e:
            print(f"Error fetching Finnhub news for {ticker}: {e}")

        return []

    async def get_market_news(self, category: str = "general") -> List[dict]:
        """Get general market news"""
        if not self.api_key:
            return []

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.BASE_URL}/news",
                    params={
                        "category": category,
                        "token": self.api_key,
                    },
                    timeout=15.0,
                )

                if response.status_code == 200:
                    return response.json()
        except Exception as e:
            print(f"Error fetching market news: {e}")

        return []

    def _transform_news_item(self, item: dict, ticker: str) -> dict:
        """Transform Finnhub news item to our format"""
        headline = item.get("headline", "")
        url = item.get("url", "")

        # Create content hash for deduplication
        content_hash = hashlib.sha256(
            f"{headline}{url}".encode()
        ).hexdigest()

        return {
            "ticker": ticker.upper(),
            "headline": headline,
            "summary": item.get("summary"),
            "url": url,
            "source": item.get("source", "finnhub"),
            "published_at": datetime.fromtimestamp(
                item.get("datetime", 0), tz=timezone.utc
            ),
            "content_hash": content_hash,
            "raw_data": item,
        }


finnhub_service = FinnhubService()
