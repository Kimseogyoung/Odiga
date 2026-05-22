import json
from app.core.redis import get_redis


TTL_DETAIL  = 60 * 60 * 24 * 30   # 30일
TTL_VECTOR  = 60 * 60 * 24 * 30   # 30일
TTL_SUMMARY = 60 * 60 * 24 * 7    # 7일


# ── 장소 메타 ─────────────────────────────────────────────────────────────────

async def save_detail(place: dict) -> None:
    """embedding 필드 제외하고 메타만 저장."""
    redis = await get_redis()
    pid = place["kakao_place_id"]
    detail = {k: v for k, v in place.items() if k != "embedding"}
    await redis.set(f"places:detail:{pid}", json.dumps(detail, ensure_ascii=False), ex=TTL_DETAIL)


async def get_detail(kakao_place_id: str) -> dict | None:
    redis = await get_redis()
    data = await redis.get(f"places:detail:{kakao_place_id}")
    return json.loads(data) if data else None


# ── 임베딩 벡터 ───────────────────────────────────────────────────────────────

async def save_vector(kakao_place_id: str, vector: list[float]) -> None:
    redis = await get_redis()
    await redis.set(f"places:vector:{kakao_place_id}", json.dumps(vector), ex=TTL_VECTOR)


async def get_vector(kakao_place_id: str) -> list[float] | None:
    redis = await get_redis()
    data = await redis.get(f"places:vector:{kakao_place_id}")
    return json.loads(data) if data else None


# ── 전체 ID 목록 ──────────────────────────────────────────────────────────────

async def save_all_ids(ids: list[str]) -> None:
    redis = await get_redis()
    await redis.set("places:all_ids", json.dumps(ids), ex=TTL_VECTOR)


async def get_all_ids() -> list[str] | None:
    redis = await get_redis()
    data = await redis.get("places:all_ids")
    return json.loads(data) if data else None


# ── AI 요약 (M2) ──────────────────────────────────────────────────────────────

async def save_summary(kakao_place_id: str, summary: dict) -> None:
    redis = await get_redis()
    await redis.set(
        f"ai:summary:{kakao_place_id}",
        json.dumps(summary, ensure_ascii=False),
        ex=TTL_SUMMARY,
    )


async def get_summary(kakao_place_id: str) -> dict | None:
    redis = await get_redis()
    data = await redis.get(f"ai:summary:{kakao_place_id}")
    return json.loads(data) if data else None


async def summary_exists(kakao_place_id: str) -> bool:
    redis = await get_redis()
    return bool(await redis.exists(f"ai:summary:{kakao_place_id}"))
