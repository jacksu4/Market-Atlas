from celery import Celery

from app.core.config import settings

celery_app = Celery(
    "market_atlas",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=[
        "app.tasks.news_tasks",
        "app.tasks.research_tasks",
    ],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,  # 1 hour max
    worker_prefetch_multiplier=1,
    task_acks_late=True,
)

# Celery Beat schedule for periodic tasks
celery_app.conf.beat_schedule = {
    "fetch-news-every-minute": {
        "task": "app.tasks.news_tasks.fetch_watchlist_news",
        "schedule": 60.0,  # Every minute
    },
    "check-sec-filings-hourly": {
        "task": "app.tasks.research_tasks.check_sec_filings",
        "schedule": 3600.0,  # Every hour
    },
    "check-earnings-transcripts-daily": {
        "task": "app.tasks.research_tasks.check_earnings_transcripts",
        "schedule": 86400.0,  # Every 24 hours
    },
}
