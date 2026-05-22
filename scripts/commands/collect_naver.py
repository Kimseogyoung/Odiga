"""
네이버 블로그 검색 API로 장소별 리뷰 텍스트 수집.
collect_kakao.py 실행 후 data/collected_kakao.json 이 있어야 함.

실행: python scripts/collect_naver.py
출력: data/collected_naver.json
"""
import argparse
import asyncio
import json
import re
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "backend"))

import httpx
from app.core.config import settings


NAVER_BLOG_URL = "https://openapi.naver.com/v1/search/blog.json"
INPUT_PATH = Path(__file__).parent.parent.parent / "data" / "collected_kakao.json"
OUTPUT_PATH = Path(__file__).parent.parent.parent / "data" / "collected_naver.json"

DISPLAY = 5        # 장소당 블로그 포스트 수
CONCURRENCY = 3    # 네이버 API rate limit 대응
REQUEST_DELAY = 0.1  # 요청 간 딜레이 (초)


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
        await asyncio.sleep(REQUEST_DELAY)
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


async def run(limit: int | None = None) -> None:
    if not INPUT_PATH.exists():
        print(f"오류: {INPUT_PATH} 없음. collect_kakao.py 먼저 실행하세요.")
        sys.exit(1)

    places = json.loads(INPUT_PATH.read_text(encoding="utf-8"))
    if limit:
        places = places[:limit]
    print(f"총 {len(places)}개 장소에 대한 블로그 리뷰 수집 시작")

    results: list[dict] = []
    sem = asyncio.Semaphore(CONCURRENCY)
    total = len(places)
    done = 0

    async def fetch_with_progress(place: dict) -> tuple[dict, str | Exception]:
        nonlocal done
        result = await fetch_reviews(client, sem, place["name"], place["region_label"])
        done += 1
        print(f"  [{done}/{total}] {place['name']}", flush=True)
        return place, result

    async with httpx.AsyncClient(timeout=30.0) as client:
        outcomes = await asyncio.gather(
            *[fetch_with_progress(p) for p in places],
            return_exceptions=True,
        )

    for outcome in outcomes:
        if isinstance(outcome, Exception):
            continue
        place, reviews = outcome
        if isinstance(reviews, Exception):
            print(f"  실패: {place['name']} — {reviews}")
            reviews = ""
        results.append({
            "kakao_place_id": place["kakao_place_id"],
            "name": place["name"],
            "region_label": place["region_label"],
            "blog_reviews": reviews,
        })

    data_str = json.dumps(results, ensure_ascii=False, indent=2)
    OUTPUT_PATH.write_text(data_str, encoding="utf-8")
    backup = OUTPUT_PATH.parent / f"collected_naver_{datetime.now().strftime('%y%m%d%H%M')}.json"
    backup.write_text(data_str, encoding="utf-8")

    filled = sum(1 for r in results if r["blog_reviews"])
    print(f"리뷰 있음: {filled}/{len(results)}개 → {OUTPUT_PATH}")
    print(f"백업 → {backup.name}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-n", "--limit", type=int, default=None, help="처리할 장소 수 제한 (테스트용)")
    args = parser.parse_args()
    asyncio.run(run(args.limit))
