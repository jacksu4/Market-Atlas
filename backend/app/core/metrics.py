"""
Prometheus metrics for monitoring application performance.
"""
from prometheus_client import Counter, Histogram, Gauge
import time
from functools import wraps
from typing import Callable

# API Metrics
api_requests_total = Counter(
    "api_requests_total",
    "Total API requests",
    ["method", "endpoint", "status_code"]
)

api_request_duration = Histogram(
    "api_request_duration_seconds",
    "API request duration in seconds",
    ["method", "endpoint"]
)

api_requests_in_progress = Gauge(
    "api_requests_in_progress",
    "Number of API requests in progress",
    ["method", "endpoint"]
)

# Celery Task Metrics
celery_tasks_total = Counter(
    "celery_tasks_total",
    "Total Celery tasks",
    ["task_name", "status"]
)

celery_task_duration = Histogram(
    "celery_task_duration_seconds",
    "Celery task duration in seconds",
    ["task_name"]
)

# External API Metrics
external_api_calls_total = Counter(
    "external_api_calls_total",
    "Total external API calls",
    ["service", "status"]
)

external_api_duration = Histogram(
    "external_api_duration_seconds",
    "External API call duration in seconds",
    ["service"]
)

# Database Metrics
db_query_duration = Histogram(
    "db_query_duration_seconds",
    "Database query duration in seconds",
    ["query_type"]
)

# Cache Metrics
cache_hits_total = Counter(
    "cache_hits_total",
    "Total cache hits",
    ["cache_key_prefix"]
)

cache_misses_total = Counter(
    "cache_misses_total",
    "Total cache misses",
    ["cache_key_prefix"]
)


def track_celery_task(task_name: str):
    """Decorator to track Celery task execution"""
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            status = "success"

            try:
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                status = "error"
                raise
            finally:
                duration = time.time() - start_time
                celery_task_duration.labels(task_name=task_name).observe(duration)
                celery_tasks_total.labels(task_name=task_name, status=status).inc()

        return wrapper
    return decorator


def track_external_api(service: str):
    """Decorator to track external API calls"""
    def decorator(func: Callable):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            status = "success"

            try:
                result = await func(*args, **kwargs)
                return result
            except Exception as e:
                status = "error"
                raise
            finally:
                duration = time.time() - start_time
                external_api_duration.labels(service=service).observe(duration)
                external_api_calls_total.labels(service=service, status=status).inc()

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            status = "success"

            try:
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                status = "error"
                raise
            finally:
                duration = time.time() - start_time
                external_api_duration.labels(service=service).observe(duration)
                external_api_calls_total.labels(service=service, status=status).inc()

        # Check if function is async
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator
