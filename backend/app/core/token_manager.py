"""
Token management service for refresh token rotation.
Uses Redis to maintain a whitelist of valid refresh tokens.
"""
from typing import Optional
import redis.asyncio as aioredis
from app.core.config import settings


class TokenManager:
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

    async def store_refresh_token(self, user_id: str, token: str, ttl_days: int = 7):
        """
        Store a valid refresh token in Redis with expiration.
        Each user can have only one active refresh token (automatic rotation).
        """
        await self.init_redis()
        key = f"refresh_token:{user_id}"
        # Store token with TTL in seconds
        await self.redis.setex(key, ttl_days * 24 * 60 * 60, token)

    async def verify_refresh_token(self, user_id: str, token: str) -> bool:
        """
        Verify if the refresh token is valid (exists in Redis whitelist).
        """
        await self.init_redis()
        key = f"refresh_token:{user_id}"
        stored_token = await self.redis.get(key)
        return stored_token == token

    async def revoke_refresh_token(self, user_id: str):
        """
        Revoke (delete) a refresh token from Redis.
        """
        await self.init_redis()
        key = f"refresh_token:{user_id}"
        await self.redis.delete(key)


token_manager = TokenManager()
