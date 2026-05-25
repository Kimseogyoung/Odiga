"""
카카오 로컬 API로 지역 × 카테고리 전체 수집.

pageable_count 45 제한을 그리드 분할로 우회.
지역을 500m 반경 원 여러 개로 쪼개 각 포인트에서 45개씩 수집 후 중복 제거.

카테고리 코드(FD6/CE7/CT1): 카테고리 검색 API (좌표+반경 기반)
술집/편집샵 등: 키워드 검색 API (카테고리 코드 없는 업종)

실행: python scripts/collect_kakao.py
출력: data/collected_kakao.json
"""
import asyncio
import json
import re
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "backend"))

import httpx
from app.core.config import settings
from app.core.constants import REGION_LABEL, REGION_GRID, KAKAO_CATEGORY_MAP, PlaceCategory


KAKAO_CATEGORY_URL = "https://dapi.kakao.com/v2/local/search/category.json"
KAKAO_KEYWORD_URL  = "https://dapi.kakao.com/v2/local/search/keyword.json"
OUTPUT_PATH = Path(__file__).parent.parent.parent / "data" / "collected_kakao.json"

CATEGORY_CODES = [
    ("FD6", "음식점"),
    ("CE7", "카페"),
    ("CT1", "문화시설"),
]

KEYWORD_QUERIES = ["술집", "편집샵", "빈티지샵", "소품샵", "빵집", "베이커리"]

MAX_PAGES = 3    # pageable_count 45 = 15 × 3, 이후는 is_end: true
PAGE_SIZE = 15


async def collect_category_at_point(
    client: httpx.AsyncClient,
    lat: float,
    lng: float,
    radius: int,
    code: str,
    region_label: str,
    seen: set[str],
) -> list[dict]:
    headers = {"Authorization": f"KakaoAK {settings.KAKAO_API_KEY}"}
    results = []

    for page in range(1, MAX_PAGES + 1):
        params = {
            "category_group_code": code,
            "x": lng,
            "y": lat,
            "radius": radius,
            "size": PAGE_SIZE,
            "page": page,
            "sort": "accuracy",
        }
        resp = await client.get(KAKAO_CATEGORY_URL, headers=headers, params=params)
        resp.raise_for_status()
        data = resp.json()

        _append_docs(data.get("documents", []), seen, results, region_label)

        if data.get("meta", {}).get("is_end", True):
            break

    return results


async def collect_keyword_at_point(
    client: httpx.AsyncClient,
    lat: float,
    lng: float,
    radius: int,
    query: str,
    region_label: str,
    seen: set[str],
) -> list[dict]:
    headers = {"Authorization": f"KakaoAK {settings.KAKAO_API_KEY}"}
    results = []

    for page in range(1, MAX_PAGES + 1):
        params = {
            "query": f"{region_label} {query}",
            "x": lng,
            "y": lat,
            "radius": radius,
            "size": PAGE_SIZE,
            "page": page,
        }
        resp = await client.get(KAKAO_KEYWORD_URL, headers=headers, params=params)
        resp.raise_for_status()
        data = resp.json()

        _append_docs(data.get("documents", []), seen, results, region_label)

        if data.get("meta", {}).get("is_end", True):
            break

    return results


def _append_docs(docs: list, seen: set, results: list, region_label: str) -> None:
    for doc in docs:
        pid = doc["id"]
        if pid in seen:
            continue
        seen.add(pid)
        results.append({
            "kakao_place_id": pid,
            "name": doc["place_name"],
            "address": doc["road_address_name"] or doc["address_name"],
            "lat": float(doc["y"]),
            "lng": float(doc["x"]),
            "kakao_category": doc.get("category_name", ""),
            "category_id": _parse_category(doc.get("category_name", "")),
            "kakao_url": doc.get("place_url", ""),
            "phone": doc.get("phone", ""),
            "region_label": region_label,
        })


def _parse_category(kakao_category: str) -> int:
    for kw, cid in KAKAO_CATEGORY_MAP.items():
        if kw in kakao_category:
            return cid
    return PlaceCategory.RESTAURANT


_PHOTO_SEM = asyncio.Semaphore(20)

_OG_IMAGE_RE = re.compile(
    r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)["\']'
    r'|<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']og:image["\']',
    re.IGNORECASE,
)


async def _fetch_og_image(client: httpx.AsyncClient, url: str) -> str | None:
    if not url:
        return None
    async with _PHOTO_SEM:
        try:
            resp = await client.get(url, timeout=10.0, follow_redirects=True)
            if resp.status_code != 200:
                return None
            m = _OG_IMAGE_RE.search(resp.text)
            raw = (m.group(1) or m.group(2)) if m else None
            if raw and raw.startswith("//"):
                raw = "https:" + raw
            return raw
        except Exception:
            return None


async def _attach_photos(client: httpx.AsyncClient, places: list[dict]) -> None:
    """kakao_url에서 og:image를 병렬로 가져와 photo_url 필드 추가."""
    photos = await asyncio.gather(*[
        _fetch_og_image(client, p.get("kakao_url", "")) for p in places
    ])
    found = sum(1 for p in photos if p)
    for place, photo in zip(places, photos):
        place["photo_url"] = photo
    print(f"  사진 수집: {found}/{len(places)}개")


async def run() -> None:
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    all_places: list[dict] = []
    seen: set[str] = set()

    async with httpx.AsyncClient(timeout=30.0) as client:
        for region_id, region_label in REGION_LABEL.items():
            grid = REGION_GRID[region_id]
            print(f"\n[{region_label}] 수집 시작 ({len(grid)}개 포인트)")

            for code, label in CATEGORY_CODES:
                total = 0
                for i, (lat, lng, radius) in enumerate(grid):
                    places = await collect_category_at_point(
                        client, lat, lng, radius, code, region_label, seen
                    )
                    total += len(places)
                    all_places.extend(places)
                print(f"  {code} ({label}): {total}개")

            for query in KEYWORD_QUERIES:
                total = 0
                for lat, lng, radius in grid:
                    places = await collect_keyword_at_point(
                        client, lat, lng, radius, query, region_label, seen
                    )
                    total += len(places)
                    all_places.extend(places)
                print(f"  키워드 '{query}': {total}개")

        print(f"\n[사진] og:image 수집 중... ({len(all_places)}개)")
        await _attach_photos(client, all_places)

    data_str = json.dumps(all_places, ensure_ascii=False, indent=2)
    OUTPUT_PATH.write_text(data_str, encoding="utf-8")
    backup = OUTPUT_PATH.parent / f"collected_kakao_{datetime.now().strftime('%y%m%d%H%M')}.json"
    backup.write_text(data_str, encoding="utf-8")
    print(f"\n총 {len(all_places)}개 저장 → {OUTPUT_PATH}")
    print(f"백업 → {backup.name}")


if __name__ == "__main__":
    asyncio.run(run())
