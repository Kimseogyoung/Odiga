import redis.asyncio as aioredis
from app.core.config import settings


class PrefixedPipeline:
    def __init__(self, pipe: aioredis.client.Pipeline, prefix: str) -> None:
        self._pipe = pipe
        self._prefix = prefix

    def _k(self, key: str) -> str:
        return f"{self._prefix}:{key}"

    def set(self, key: str, value, **kwargs) -> "PrefixedPipeline":
        self._pipe.set(self._k(key), value, **kwargs)
        return self

    def get(self, key: str) -> "PrefixedPipeline":
        self._pipe.get(self._k(key))
        return self

    async def execute(self):
        return await self._pipe.execute()


class PrefixedRedis:
    def __init__(self, client: aioredis.Redis, prefix: str) -> None:
        self._client = client
        self._prefix = prefix

    def _k(self, key: str) -> str:
        return f"{self._prefix}:{key}"

    async def get(self, key: str):
        return await self._client.get(self._k(key))

    async def set(self, key: str, value, **kwargs):
        return await self._client.set(self._k(key), value, **kwargs)

    async def exists(self, *keys: str) -> int:
        return await self._client.exists(*[self._k(k) for k in keys])

    def pipeline(self) -> PrefixedPipeline:
        return PrefixedPipeline(self._client.pipeline(), self._prefix)

    async def aclose(self) -> None:
        await self._client.aclose()


_client: PrefixedRedis | None = None


async def init_redis() -> None:
    global _client
    raw = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
    _client = PrefixedRedis(raw, settings.REDIS_KEY_PREFIX)


async def close_redis() -> None:
    if _client:
        await _client.aclose()


async def get_redis() -> PrefixedRedis:
    return _client
