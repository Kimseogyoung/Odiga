import redis.asyncio as redis
from app.core.config import settings

_client: redis.Redis | None = None


async def init_redis():
    global _client
    _client = redis.from_url(settings.REDIS_URL, decode_responses=True)


async def close_redis():
    if _client:
        await _client.aclose()


async def get_redis() -> redis.Redis:
    return _client
