"""
Structured logging configuration for the application.
"""
import logging
import sys

try:
    from pythonjsonlogger import jsonlogger
    HAS_JSON_LOGGER = True
except ImportError:
    HAS_JSON_LOGGER = False

from app.core.config import settings


def setup_logging():
    """Configure structured JSON logging"""

    # Create logger
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG if settings.DEBUG else logging.INFO)

    # Remove existing handlers
    logger.handlers = []

    # Create console handler
    handler = logging.StreamHandler(sys.stdout)

    # Create JSON formatter if available, otherwise use standard formatter
    if HAS_JSON_LOGGER:
        formatter = jsonlogger.JsonFormatter(
            "%(asctime)s %(name)s %(levelname)s %(message)s %(pathname)s %(lineno)d",
            timestamp=True
        )
    else:
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )

    handler.setFormatter(formatter)
    logger.addHandler(handler)

    return logger


# Application logger
app_logger = logging.getLogger("market_atlas")


def log_api_request(method: str, path: str, status_code: int, duration_ms: float):
    """Log API request with structured data"""
    app_logger.info(
        "API Request",
        extra={
            "method": method,
            "path": path,
            "status_code": status_code,
            "duration_ms": duration_ms,
            "event_type": "api_request"
        }
    )


def log_celery_task(task_name: str, status: str, duration_ms: float = None, error: str = None):
    """Log Celery task execution"""
    extra = {
        "task_name": task_name,
        "status": status,
        "event_type": "celery_task"
    }

    if duration_ms is not None:
        extra["duration_ms"] = duration_ms

    if error:
        extra["error"] = error
        app_logger.error(f"Celery task failed: {task_name}", extra=extra)
    else:
        app_logger.info(f"Celery task {status}: {task_name}", extra=extra)


def log_external_api_call(service: str, endpoint: str, status_code: int = None, error: str = None):
    """Log external API calls"""
    extra = {
        "service": service,
        "endpoint": endpoint,
        "event_type": "external_api"
    }

    if status_code:
        extra["status_code"] = status_code

    if error:
        extra["error"] = error
        app_logger.error(f"External API error: {service}", extra=extra)
    else:
        app_logger.info(f"External API call: {service}", extra=extra)
