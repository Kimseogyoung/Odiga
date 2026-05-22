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


# ── 지역×카테고리 단위 벡터 DB ────────────────────────────────────────────────

async def save_region_category_vectors(
    region_id: int,
    category_id: int,
    ids: list[str],
    matrix_flat: list[float],
) -> None:
    """
    ids: 장소 ID 목록
    matrix_flat: 벡터를 1차원으로 flatten한 리스트 (len = len(ids) * 768)
    """
    redis = await get_redis()
    prefix = f"places:vectors:{region_id}:{category_id}"
    pipe = redis.pipeline()
    pipe.set(f"{prefix}:ids",    json.dumps(ids),         ex=TTL_VECTOR)
    pipe.set(f"{prefix}:matrix", json.dumps(matrix_flat), ex=TTL_VECTOR)
    await pipe.execute()


async def get_region_category_vectors(
    region_id: int,
    category_id: int,
) -> tuple[list[str], list[float]] | None:
    """
    반환: (ids, matrix_flat) 또는 None
    matrix_flat → np.array(matrix_flat).reshape(-1, 768) 으로 복원
    """
    redis = await get_redis()
    prefix = f"places:vectors:{region_id}:{category_id}"
    pipe = redis.pipeline()
    pipe.get(f"{prefix}:ids")
    pipe.get(f"{prefix}:matrix")
    ids_data, matrix_data = await pipe.execute()
    if not ids_data or not matrix_data:
        return None
    return json.loads(ids_data), json.loads(matrix_data)


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
