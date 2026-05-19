"""
네이버 블로그 검색 API로 장소별 리뷰 텍스트 수집.
collect_kakao.py 실행 후 data/collected_kakao.json 이 있어야 함.

실행: python scripts/collect_naver.py
출력: data/collected_naver.json
"""
import asyncio
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

import httpx
from app.core.config import settings


NAVER_BLOG_URL = "https://openapi.naver.com/v1/search/blog.json"
INPUT_PATH = Path(__file__).parent.parent / "data" / "collected_kakao.json"
OUTPUT_PATH = Path(__file__).parent.parent / "data" / "collected_naver.json"

DISPLAY = 5        # 장소당 블로그 포스트 수
CONCURRENCY = 5    # 동시 요청 수 (네이버 API 쿼터 고려)


async def fetch_reviews(
    client: httpx.AsyncClient,
    sem: asyncio.Semaphore,
    place_name: str,
    region_label: str,
) -> str:
    headers = {
        "X-Naver-Client-Id": settings.NAVER_CLIENT_ID,
        "X-Naver-Client-Secret": settings.NAVER_CLIENT_SECRET,
    }
    params = {
        "query": f"{region_label} {place_name} 후기",
        "display": DISPLAY,
        "sort": "sim",
    }

    async with sem:
        resp = await client.get(NAVER_BLOG_URL, headers=headers, params=params)
        resp.raise_for_status()
        data = resp.json()

    items = data.get("items", [])
    if not items:
        return ""

    texts = []
    for item in items:
        title = _strip_html(item.get("title", ""))
        desc = _strip_html(item.get("description", ""))
        texts.append(f"{title}. {desc}")

    return " ".join(texts)


def _strip_html(text: str) -> str:
    return re.sub(r"<[^>]+>", "", text)


async def run() -> None:
    if not INPUT_PATH.exists():
        print(f"오류: {INPUT_PATH} 없음. collect_kakao.py 먼저 실행하세요.")
        sys.exit(1)

    places = json.loads(INPUT_PATH.read_text(encoding="utf-8"))
    print(f"총 {len(places)}개 장소에 대한 블로그 리뷰 수집 시작")

    results: list[dict] = []
    sem = asyncio.Semaphore(CONCURRENCY)

    async with httpx.AsyncClient(timeout=30.0) as client:
        tasks = [
            fetch_reviews(client, sem, p["name"], p["region_label"])
            for p in places
        ]
        reviews_list = await asyncio.gather(*tasks, return_exceptions=True)

    for place, reviews in zip(places, reviews_list):
        if isinstance(reviews, Exception):
            print(f"  실패: {place['name']} — {reviews}")
            reviews = ""

        results.append({
            "kakao_place_id": place["kakao_place_id"],
            "name": place["name"],
            "region_label": place["region_label"],
            "blog_reviews": reviews,
        })

    OUTPUT_PATH.write_text(
        json.dumps(results, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    filled = sum(1 for r in results if r["blog_reviews"])
    print(f"리뷰 있음: {filled}/{len(results)}개 → {OUTPUT_PATH}")


if __name__ == "__main__":
    asyncio.run(run())
