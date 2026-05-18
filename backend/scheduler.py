"""
M1 데이터 수집 스케줄러.
수동 실행: python scheduler.py
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from app.core.redis import init_redis, close_redis
from app.core.constants import Region, Keyword, REGION_LABEL, PLACE_CATEGORY_LABEL
from app.services.kakao import search_places
from app.services.naver import fetch_blog_reviews
from app.services.claude import summarize_place
from app.services import place_store


SEMAPHORE = asyncio.Semaphore(10)


async def collect_places(region_id: int, keyword_id: int) -> list[str]:
    """카카오 검색 → Redis 저장. place_id 목록 반환."""
    places = await search_places(region_id, keyword_id)
    place_ids = [p["kakao_place_id"] for p in places]

    for place in places:
        await place_store.save_detail(place)

    await place_store.save_search(region_id, keyword_id, place_ids)

    region = REGION_LABEL[region_id]
    keyword = Keyword(keyword_id).name
    print(f"  [수집] {region} / {keyword}: {len(places)}개")
    return place_ids


async def summarize_one(place_id: str, region_id: int) -> None:
    """장소 1개 AI 요약 생성 → Redis 저장."""
    async with SEMAPHORE:
        if await place_store.summary_exists(place_id):
            return

        detail = await place_store.get_detail(place_id)
        if not detail:
            return

        region_label = REGION_LABEL[region_id]
        reviews = await fetch_blog_reviews(detail["name"], region_label)
        category_label = PLACE_CATEGORY_LABEL.get(detail.get("category_id", 1), "장소")

        summary = await summarize_place(
            name=detail["name"],
            category=category_label,
            reviews=reviews,
        )

        await place_store.save_summary(place_id, summary)
        print(f"  [요약] {detail['name']}: {summary['summary']}")


async def run():
    print("=== Odiga 데이터 수집 시작 ===\n")
    await init_redis()

    all_place_ids: dict[str, int] = {}  # place_id → region_id

    # Step 1: 지역 × 키워드 전체 수집
    print("[Step 1] 장소 수집")
    for region_id in [r.value for r in Region]:
        for keyword_id in [k.value for k in Keyword]:
            try:
                place_ids = await collect_places(region_id, keyword_id)
                for pid in place_ids:
                    all_place_ids[pid] = region_id
            except Exception as e:
                print(f"  [오류] region={region_id} keyword={keyword_id}: {e}")

    # Step 2: AI 요약 생성 (중복 제거된 장소만)
    print(f"\n[Step 2] AI 요약 생성 ({len(all_place_ids)}개 장소)")
    tasks = [
        summarize_one(place_id, region_id)
        for place_id, region_id in all_place_ids.items()
    ]
    await asyncio.gather(*tasks)

    await close_redis()
    print("\n=== 완료 ===")


if __name__ == "__main__":
    asyncio.run(run())
