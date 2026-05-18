"""
API 연동 1회 테스트. Redis 없이 텍스트로 결과 확인.
실행: python test_run.py
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from app.core.constants import REGION_LABEL, PLACE_CATEGORY_LABEL, KEYWORD_LABEL
from app.services.kakao import search_places_by_region
from app.services.naver import fetch_blog_reviews
from app.services.claude import summarize_place, tag_keywords


async def run():
    region_id = 1  # 성수

    print(f"=== 테스트: {REGION_LABEL[region_id]} ===\n")

    # Step 1: 카카오 지역 검색
    print("[1] 카카오 장소 검색")
    places = await search_places_by_region(region_id)
    for p in places:
        print(f"  - {p['name']} ({p['kakao_category']})")
    print(f"  총 {len(places)}개\n")

    if not places:
        print("검색 결과 없음")
        return

    # Step 2~4: 첫 번째 장소만 풀 파이프라인 테스트
    target = places[0]
    category_label = PLACE_CATEGORY_LABEL.get(target.get("category_id", 1), "장소")
    print(f"[2] 네이버 블로그 리뷰 — {target['name']}")
    reviews = await fetch_blog_reviews(target["name"], REGION_LABEL[region_id])
    print(f"  {reviews[:300]}{'...' if len(reviews) > 300 else ''}\n")

    print(f"[3] Claude 요약 — {target['name']}")
    summary = await summarize_place(target["name"], category_label, reviews)
    print(f"  summary : {summary['summary']}")
    print(f"  caution : {summary['caution']}\n")

    print(f"[4] Claude 키워드 태깅 — {target['name']}")
    keyword_ids = await tag_keywords(target["name"], category_label, summary["summary"], reviews)
    keyword_names = [KEYWORD_LABEL.get(kid, str(kid)) for kid in keyword_ids]
    print(f"  keywords: {keyword_names}")

    print("\n=== 완료 ===")


if __name__ == "__main__":
    asyncio.run(run())
