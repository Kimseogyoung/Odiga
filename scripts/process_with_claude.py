"""
4개 collected_*.json 통합 + Claude 요약/키워드 생성.
카카오 ID 기준 중복 제거 후 각 장소에 summary, caution, keyword_ids 추가.

실행: python scripts/process_with_claude.py
출력: data/redis_data.json

사전 조건: data/ 아래 collected_kakao.json, collected_naver.json,
           collected_instagram.json, collected_google.json 존재
"""
import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from app.core.constants import PLACE_CATEGORY_LABEL
from app.services.claude import summarize_place, tag_keywords


DATA_DIR = Path(__file__).parent.parent / "data"
OUTPUT_PATH = DATA_DIR / "redis_data.json"

CONCURRENCY = 3   # Claude API 동시 호출 수 (비용/쿼터 고려)


def load_json(path: Path) -> list[dict]:
    if not path.exists():
        print(f"경고: {path.name} 없음 — 건너뜀")
        return []
    return json.loads(path.read_text(encoding="utf-8"))


def merge_sources() -> list[dict]:
    """4개 소스 로드 후 kakao_place_id 기준 통합."""
    kakao_places = load_json(DATA_DIR / "collected_kakao.json")
    naver_data = load_json(DATA_DIR / "collected_naver.json")
    twitter_data = load_json(DATA_DIR / "collected_twitter.json")
    google_data = load_json(DATA_DIR / "collected_google.json")

    # 보조 소스를 kakao_place_id 기준 딕셔너리로
    naver_map: dict[str, str] = {
        r["kakao_place_id"]: r["blog_reviews"] for r in naver_data
    }
    google_map: dict[str, dict] = {
        r["kakao_place_id"]: r for r in google_data
    }

    # 트위터는 장소명 기반이라 name으로 매핑
    twitter_map: dict[str, int] = {}
    for r in twitter_data:
        twitter_map[r["name"]] = r.get("twitter_mention_count", 0)

    merged: list[dict] = []
    seen: set[str] = set()

    for place in kakao_places:
        pid = place["kakao_place_id"]
        if pid in seen:
            continue
        seen.add(pid)

        google = google_map.get(pid, {})
        merged.append({
            "kakao_place_id": pid,
            "name": place["name"],
            "address": place["address"],
            "lat": place["lat"],
            "lng": place["lng"],
            "category_id": place["category_id"],
            "kakao_category": place.get("kakao_category", ""),
            "kakao_url": place.get("kakao_url", ""),
            "phone": place.get("phone", ""),
            "region_label": place["region_label"],
            # 네이버 블로그 리뷰
            "blog_reviews": naver_map.get(pid, ""),
            # 트위터 언급 수
            "twitter_mention_count": twitter_map.get(place["name"], 0),
            # 구글 상세 정보
            "google_place_id": google.get("google_place_id"),
            "rating": google.get("rating"),
            "review_count": google.get("review_count"),
            "opening_hours": google.get("opening_hours", []),
            "photo_count": google.get("photo_count", 0),
        })

    return merged


async def process_place(
    sem: asyncio.Semaphore,
    place: dict,
    index: int,
    total: int,
) -> dict:
    category_label = PLACE_CATEGORY_LABEL.get(place["category_id"], "장소")
    reviews = place["blog_reviews"]

    async with sem:
        summary_result = await summarize_place(place["name"], category_label, reviews)
        keyword_ids = await tag_keywords(
            place["name"],
            category_label,
            summary_result["summary"],
            reviews,
        )

    print(f"  [{index}/{total}] {place['name']} — {summary_result['summary'][:40]}...")

    return {
        **place,
        "summary": summary_result["summary"],
        "caution": summary_result["caution"],
        "keyword_ids": keyword_ids,
    }


async def run() -> None:
    places = merge_sources()
    if not places:
        print("처리할 장소 없음. collect_kakao.py부터 실행하세요.")
        sys.exit(1)

    print(f"총 {len(places)}개 장소 Claude 처리 시작")

    sem = asyncio.Semaphore(CONCURRENCY)
    tasks = [
        process_place(sem, place, i + 1, len(places))
        for i, place in enumerate(places)
    ]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    final: list[dict] = []
    failed = 0
    for place, result in zip(places, results):
        if isinstance(result, Exception):
            print(f"  예외 ({place['name']}): {result}")
            failed += 1
            final.append({**place, "summary": place["name"], "caution": "", "keyword_ids": []})
        else:
            final.append(result)

    OUTPUT_PATH.write_text(
        json.dumps(final, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"\n완료: {len(final) - failed}/{len(final)}개 처리 성공 → {OUTPUT_PATH}")


if __name__ == "__main__":
    asyncio.run(run())
