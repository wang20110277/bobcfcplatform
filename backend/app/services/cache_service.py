import json
from typing import Any, Optional

import redis.asyncio as redis
from app.config import get_settings

settings = get_settings()

_redis: Optional[redis.Redis] = None


async def get_redis() -> redis.Redis:
    global _redis
    if _redis is None:
        _redis = redis.from_url(settings.redis_url, decode_responses=True)
    return _redis


async def init_redis():
    global _redis
    if _redis is None:
        _redis = redis.from_url(settings.redis_url, decode_responses=True)


async def close_redis():
    global _redis
    if _redis:
        await _redis.close()
        _redis = None


class CacheService:
    def __init__(self, redis_client: redis.Redis):
        self._redis = redis_client

    async def get(self, key: str) -> Any:
        raw = await self._redis.get(key)
        if raw is None:
            return None
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return raw

    async def set(self, key: str, value: Any, ttl: int = 300):
        if isinstance(value, (dict, list)):
            value = json.dumps(value)
        await self._redis.set(key, value, ex=ttl)

    async def delete(self, key: str):
        await self._redis.delete(key)

    async def invalidate_pattern(self, pattern: str):
        """Delete all keys matching a glob pattern."""
        async for key in self._redis.scan_iter(match=pattern):
            await self._redis.delete(key)
