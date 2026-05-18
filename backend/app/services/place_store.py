import json
from app.core.redis import get_redis


TTL_SEARCH = 60 * 60 * 24        # 24h
TTL_DETAIL = 60 * 60 * 24        # 24h
TTL_SUMMARY = 60 * 60 * 24 * 7   # 7일


async def save_search(region_id: int, keyword_id: int, place_ids: list[str]) -> None:
    redis = await get_redis()
    key = f"places:search:{region_id}:{keyword_id}"
    await redis.set(key, json.dumps(place_ids), ex=TTL_SEARCH)


async def get_search(region_id: int, keyword_id: int) -> list[str] | None:
    redis = await get_redis()
    key = f"places:search:{region_id}:{keyword_id}"
    data = await redis.get(key)
    return json.loads(data) if data else None


async def save_detail(place: dict) -> None:
    redis = await get_redis()
    key = f"places:detail:{place['kakao_place_id']}"
    await redis.set(key, json.dumps(place, ensure_ascii=False), ex=TTL_DETAIL)


async def get_detail(kakao_place_id: str) -> dict | None:
    redis = await get_redis()
    key = f"places:detail:{kakao_place_id}"
    data = await redis.get(key)
    return json.loads(data) if data else None


async def save_summary(kakao_place_id: str, summary: dict) -> None:
    redis = await get_redis()
    key = f"ai:summary:{kakao_place_id}"
    await redis.set(key, json.dumps(summary, ensure_ascii=False), ex=TTL_SUMMARY)


async def get_summary(kakao_place_id: str) -> dict | None:
    redis = await get_redis()
    key = f"ai:summary:{kakao_place_id}"
    data = await redis.get(key)
    return json.loads(data) if data else None


async def summary_exists(kakao_place_id: str) -> bool:
    redis = await get_redis()
    return bool(await redis.exists(f"ai:summary:{kakao_place_id}"))
