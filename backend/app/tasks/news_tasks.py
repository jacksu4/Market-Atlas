import json
import hashlib
from datetime import datetime, timezone

import httpx
import redis
from sqlalchemy import select

from app.core.celery_app import celery_app
from app.core.config import settings
from app.core.database import SyncSessionLocal
from app.models.watchlist import WatchlistItem
from app.models.news import News, NewsSentiment, NewsImportance


def get_company_news_sync(ticker: str, days_back: int = 7) -> list[dict]:
    """Synchronous version of fetching company news from Finnhub"""
    if not settings.FINNHUB_API_KEY:
        return []

    from datetime import timedelta
    today = datetime.now(timezone.utc)
    from_date = (today - timedelta(days=days_back)).strftime("%Y-%m-%d")
    to_date = today.strftime("%Y-%m-%d")

    try:
        with httpx.Client(timeout=15.0) as client:
            response = client.get(
                "https://finnhub.io/api/v1/company-news",
                params={
                    "symbol": ticker.upper(),
                    "from": from_date,
                    "to": to_date,
                    "token": settings.FINNHUB_API_KEY,
                },
            )

            if response.status_code == 200:
                news_items = response.json()
                results = []
                for item in news_items:
                    headline = item.get("headline", "")
                    url = item.get("url", "")
                    content_hash = hashlib.sha256(f"{headline}{url}".encode()).hexdigest()

                    results.append({
                        "ticker": ticker.upper(),
                        "headline": headline,
                        "summary": item.get("summary"),
                        "url": url,
                        "source": item.get("source", "finnhub"),
                        "published_at": datetime.fromtimestamp(
                            item.get("datetime", 0), tz=timezone.utc
                        ),
                        "content_hash": content_hash,
                    })
                return results
    except Exception as e:
        print(f"Error fetching Finnhub news for {ticker}: {e}")

    return []


@celery_app.task(name="app.tasks.news_tasks.fetch_watchlist_news")
def fetch_watchlist_news():
    """
    Fetch news for all stocks in all watchlists.
    This runs periodically via Celery Beat.
    """
    db = SyncSessionLocal()
    try:
        # Get all unique tickers from watchlists
        result = db.execute(select(WatchlistItem.ticker).distinct())
        tickers = [row[0] for row in result.fetchall()]

        if not tickers:
            return {"message": "No tickers to fetch"}

        redis_client = redis.from_url(settings.REDIS_URL)
        news_count = 0

        for ticker in tickers:
            # Fetch news synchronously
            news_items = get_company_news_sync(ticker)

            for news_item in news_items:
                # Check if news already exists
                existing = db.execute(
                    select(News).where(News.content_hash == news_item["content_hash"])
                ).scalar_one_or_none()

                if existing:
                    continue

                # Create news record (skip AI analysis for now to keep it simple)
                news = News(
                    ticker=ticker,
                    headline=news_item["headline"],
                    summary=news_item.get("summary"),
                    url=news_item["url"],
                    source=news_item["source"],
                    published_at=news_item["published_at"],
                    content_hash=news_item["content_hash"],
                    sentiment=NewsSentiment.NEUTRAL,
                    importance=NewsImportance.MEDIUM,
                )

                db.add(news)
                news_count += 1

                # Publish to Redis for WebSocket broadcast
                try:
                    redis_client.publish(
                        "news_updates",
                        json.dumps({
                            "ticker": ticker,
                            "headline": news_item["headline"],
                            "published_at": news_item["published_at"].isoformat(),
                        }),
                    )
                except Exception:
                    pass

        db.commit()
        redis_client.close()

        return {"message": f"Fetched {news_count} new articles for {len(tickers)} tickers"}
    except Exception as e:
        db.rollback()
        return {"error": str(e)}
    finally:
        db.close()


@celery_app.task(name="app.tasks.news_tasks.fetch_news_for_ticker")
def fetch_news_for_ticker(ticker: str):
    """
    Fetch news for a specific ticker.
    Called when a new stock is added to a watchlist.
    """
    db = SyncSessionLocal()
    try:
        news_items = get_company_news_sync(ticker)
        news_count = 0

        for news_item in news_items:
            existing = db.execute(
                select(News).where(News.content_hash == news_item["content_hash"])
            ).scalar_one_or_none()

            if existing:
                continue

            news = News(
                ticker=ticker,
                headline=news_item["headline"],
                summary=news_item.get("summary"),
                url=news_item["url"],
                source=news_item["source"],
                published_at=news_item["published_at"],
                content_hash=news_item["content_hash"],
                sentiment=NewsSentiment.NEUTRAL,
                importance=NewsImportance.MEDIUM,
            )

            db.add(news)
            news_count += 1

        db.commit()
        return {"message": f"Fetched {news_count} news articles for {ticker}"}
    except Exception as e:
        db.rollback()
        return {"error": str(e)}
    finally:
        db.close()
