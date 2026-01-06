"""
Redis caching utilities for performance optimization.
"""
import json
import hashlib
from typing import Optional, Any, Callable
from functools import wraps
import redis.asyncio as aioredis

from app.core.config import settings
from app.core.metrics import cache_hits_total, cache_misses_total


class CacheManager:
    def __init__(self):
        self.redis: Optional[aioredis.Redis] = None

    async def init_redis(self):
        """Initialize Redis connection"""
        if not self.redis:
            self.redis = await aioredis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True
            )

    async def close(self):
        """Close Redis connection"""
        if self.redis:
            await self.redis.close()

    async def get(self, key: str) -> Optional[str]:
        """Get value from cache"""
        await self.init_redis()
        value = await self.redis.get(key)

        # Track metrics
        key_prefix = key.split(":")[0]
        if value:
            cache_hits_total.labels(cache_key_prefix=key_prefix).inc()
        else:
            cache_misses_total.labels(cache_key_prefix=key_prefix).inc()

        return value

    async def set(self, key: str, value: str, ttl: int = 3600):
        """Set value in cache with TTL (default 1 hour)"""
        await self.init_redis()
        await self.redis.setex(key, ttl, value)

    async def delete(self, key: str):
        """Delete key from cache"""
        await self.init_redis()
        await self.redis.delete(key)

    async def get_json(self, key: str) -> Optional[Any]:
        """Get JSON value from cache"""
        value = await self.get(key)
        if value:
            return json.loads(value)
        return None

    async def set_json(self, key: str, value: Any, ttl: int = 3600):
        """Set JSON value in cache"""
        await self.set(key, json.dumps(value), ttl)


cache_manager = CacheManager()


def cache_key(*args, **kwargs) -> str:
    """Generate cache key from function arguments"""
    key_parts = [str(arg) for arg in args]
    key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
    key_string = ":".join(key_parts)
    return hashlib.md5(key_string.encode()).hexdigest()


def cached(prefix: str, ttl: int = 3600):
    """
    Decorator to cache function results in Redis.

    Args:
        prefix: Cache key prefix
        ttl: Time to live in seconds (default 1 hour)

    Example:
        @cached("stock_price", ttl=300)
        async def get_stock_price(ticker: str):
            # expensive operation
            return price
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate cache key
            key = f"{prefix}:{cache_key(*args, **kwargs)}"

            # Try to get from cache
            cached_value = await cache_manager.get_json(key)
            if cached_value is not None:
                return cached_value

            # Call function and cache result
            result = await func(*args, **kwargs)
            await cache_manager.set_json(key, result, ttl)

            return result

        return wrapper
    return decorator
