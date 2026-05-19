"""
data/redis_data.json → Redis 저장.
장소 상세(places:detail:*), 지역×키워드 검색 인덱스(places:search:*:*) 구축.

실행: python scripts/import_to_redis.py
사전 조건: Redis 실행 중, data/redis_data.json 존재
"""
import asyncio
import json
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from app.core.redis import init_redis, close_redis, get_redis
from app.core.constants import REGION_LABEL


INPUT_PATH = Path(__file__).parent.parent / "data" / "redis_data.json"

TTL_DETAIL = 60 * 60 * 24 * 30   # 30일 (수집 데이터는 장기 보관)
TTL_SEARCH = 60 * 60 * 24 * 30


async def run() -> None:
    if not INPUT_PATH.exists():
        print(f"오류: {INPUT_PATH} 없음. process_with_claude.py 먼저 실행하세요.")
        sys.exit(1)

    places = json.loads(INPUT_PATH.read_text(encoding="utf-8"))
    print(f"총 {len(places)}개 장소 Redis 적재 시작")

    await init_redis()
    redis = await get_redis()

    # 지역×키워드 → 장소 ID 목록 (검색 인덱스 빌드용)
    # {(region_id, keyword_id): [kakao_place_id, ...]}
    search_index: dict[tuple[int, int], list[str]] = defaultdict(list)

    # 지역명 → region_id 역매핑
    label_to_region_id = {v: k for k, v in REGION_LABEL.items()}

    pipe = redis.pipeline()

    for place in places:
        pid = place["kakao_place_id"]
        detail_key = f"places:detail:{pid}"

        # 상세 정보 저장 (blog_reviews 제외 — 용량 절감)
        detail = {k: v for k, v in place.items() if k != "blog_reviews"}
        pipe.set(detail_key, json.dumps(detail, ensure_ascii=False), ex=TTL_DETAIL)

        # 검색 인덱스 구축
        region_id = label_to_region_id.get(place.get("region_label", ""))
        if region_id is None:
            continue
        for keyword_id in place.get("keyword_ids", []):
            search_index[(region_id, keyword_id)].append(pid)

    await pipe.execute()
    print(f"  장소 상세 {len(places)}개 저장 완료")

    # 검색 인덱스 저장
    pipe = redis.pipeline()
    for (region_id, keyword_id), place_ids in search_index.items():
        key = f"places:search:{region_id}:{keyword_id}"
        pipe.set(key, json.dumps(place_ids), ex=TTL_SEARCH)
    await pipe.execute()

    index_count = len(search_index)
    print(f"  검색 인덱스 {index_count}개 저장 완료")

    # 통계 출력
    print("\n--- 인덱스 통계 ---")
    for (region_id, keyword_id), place_ids in sorted(search_index.items()):
        region_name = REGION_LABEL.get(region_id, str(region_id))
        print(f"  {region_name} × keyword_id={keyword_id}: {len(place_ids)}개")

    await close_redis()
    print("\n적재 완료")


if __name__ == "__main__":
    asyncio.run(run())
