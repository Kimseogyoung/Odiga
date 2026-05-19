"""
Google Places API (New)로 카카오 수집 장소의 상세 정보 보강.
영업시간, 평점, 리뷰 수, 사진 레퍼런스 수집.
collect_kakao.py 실행 후 data/collected_kakao.json 이 있어야 함.

실행: python scripts/collect_google.py
출력: data/collected_google.json

주의: Places API (New) 기준. Text Search → Place Details 순서.
"""
import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

import httpx
from app.core.config import settings


INPUT_PATH = Path(__file__).parent.parent / "data" / "collected_kakao.json"
OUTPUT_PATH = Path(__file__).parent.parent / "data" / "collected_google.json"

PLACES_TEXT_SEARCH_URL = "https://places.googleapis.com/v1/places:searchText"
PLACES_DETAILS_URL = "https://places.googleapis.com/v1/places/{place_id}"

CONCURRENCY = 3   # Google Places API 분당 쿼터 고려
RETRY_DELAY = 2.0


async def text_search(
    client: httpx.AsyncClient,
    sem: asyncio.Semaphore,
    name: str,
    address: str,
    api_key: str,
) -> str | None:
    """장소명 + 주소로 Google Place ID 조회."""
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": api_key,
        "X-Goog-FieldMask": "places.id,places.displayName",
    }
    body = {"textQuery": f"{name} {address}"}

    async with sem:
        try:
            resp = await client.post(PLACES_TEXT_SEARCH_URL, headers=headers, json=body)
            resp.raise_for_status()
        except httpx.HTTPStatusError as e:
            print(f"  TextSearch 실패 ({name}): {e.response.status_code}")
            return None

    data = resp.json()
    places = data.get("places", [])
    if not places:
        return None

    return places[0]["id"]


async def fetch_place_details(
    client: httpx.AsyncClient,
    sem: asyncio.Semaphore,
    google_place_id: str,
    api_key: str,
) -> dict:
    """Place Details: 영업시간, 평점, 리뷰 수, 사진 수 조회."""
    headers = {
        "X-Goog-Api-Key": api_key,
        "X-Goog-FieldMask": (
            "id,rating,userRatingCount,regularOpeningHours,photos"
        ),
    }
    url = PLACES_DETAILS_URL.format(place_id=google_place_id)

    async with sem:
        try:
            resp = await client.get(url, headers=headers)
            resp.raise_for_status()
        except httpx.HTTPStatusError as e:
            print(f"  Details 실패 ({google_place_id}): {e.response.status_code}")
            return {}

    return resp.json()


def _parse_opening_hours(details: dict) -> list[str]:
    """weekday_descriptions 파싱 → ['월: 09:00-22:00', ...]"""
    hours = details.get("regularOpeningHours", {})
    return hours.get("weekdayDescriptions", [])


async def process_place(
    client: httpx.AsyncClient,
    sem: asyncio.Semaphore,
    place: dict,
    api_key: str,
) -> dict:
    base = {
        "kakao_place_id": place["kakao_place_id"],
        "name": place["name"],
        "google_place_id": None,
        "rating": None,
        "review_count": None,
        "opening_hours": [],
        "photo_count": 0,
    }

    google_id = await text_search(client, sem, place["name"], place["address"], api_key)
    if not google_id:
        return base

    base["google_place_id"] = google_id
    await asyncio.sleep(RETRY_DELAY)

    details = await fetch_place_details(client, sem, google_id, api_key)
    if not details:
        return base

    base["rating"] = details.get("rating")
    base["review_count"] = details.get("userRatingCount")
    base["opening_hours"] = _parse_opening_hours(details)
    base["photo_count"] = len(details.get("photos", []))

    return base


async def run() -> None:
    if not INPUT_PATH.exists():
        print(f"오류: {INPUT_PATH} 없음. collect_kakao.py 먼저 실행하세요.")
        sys.exit(1)

    api_key = settings.GOOGLE_PLACES_API_KEY
    if not api_key:
        print("오류: GOOGLE_PLACES_API_KEY 환경변수 없음.")
        sys.exit(1)

    places = json.loads(INPUT_PATH.read_text(encoding="utf-8"))
    print(f"총 {len(places)}개 장소 Google Places 조회 시작")

    results: list[dict] = []
    sem = asyncio.Semaphore(CONCURRENCY)

    async with httpx.AsyncClient(timeout=30.0) as client:
        tasks = [process_place(client, sem, p, api_key) for p in places]
        batch_results = await asyncio.gather(*tasks, return_exceptions=True)

    for place, result in zip(places, batch_results):
        if isinstance(result, Exception):
            print(f"  예외 ({place['name']}): {result}")
            results.append({
                "kakao_place_id": place["kakao_place_id"],
                "name": place["name"],
                "google_place_id": None,
                "rating": None,
                "review_count": None,
                "opening_hours": [],
                "photo_count": 0,
            })
        else:
            results.append(result)

    matched = sum(1 for r in results if r["google_place_id"])
    data_str = json.dumps(results, ensure_ascii=False, indent=2)
    OUTPUT_PATH.write_text(data_str, encoding="utf-8")
    backup = OUTPUT_PATH.parent / f"collected_google_{datetime.now().strftime('%y%m%d%H%M')}.json"
    backup.write_text(data_str, encoding="utf-8")
    print(f"Google 매칭: {matched}/{len(results)}개 → {OUTPUT_PATH}")
    print(f"백업 → {backup.name}")


if __name__ == "__main__":
    asyncio.run(run())
