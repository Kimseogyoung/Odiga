import asyncio
import httpx
from app.core.config import settings
from app.core.constants import REGION_LABEL, KAKAO_CATEGORY_MAP, PlaceCategory


KAKAO_LOCAL_URL = "https://dapi.kakao.com/v2/local/search/keyword.json"

# category_group_code 기반 수집 (카카오 공식 분류)
# CE7: 카페, FD6: 음식점, CT1: 문화시설
CATEGORY_CODES = ["CE7", "FD6", "CT1"]

# category_group_code 없이 키워드로 수집 (술집, 편집샵)
KEYWORD_QUERIES = ["술집", "편집샵", "빈티지샵"]


async def search_places_by_region(region_id: int) -> list[dict]:
    """지역으로만 검색해 장소 목록 수집. 중복 제거 후 반환."""
    region_label = REGION_LABEL[region_id]
    headers = {"Authorization": f"KakaoAK {settings.KAKAO_API_KEY}"}

    category_params = [
        {"query": region_label, "size": 15, "category_group_code": code}
        for code in CATEGORY_CODES
    ]
    keyword_params = [
        {"query": f"{region_label} {suffix}", "size": 15}
        for suffix in KEYWORD_QUERIES
    ]
    all_params = category_params + keyword_params

    async with httpx.AsyncClient() as client:
        responses = await asyncio.gather(*[
            client.get(KAKAO_LOCAL_URL, headers=headers, params=p)
            for p in all_params
        ])

    seen: set[str] = set()
    places: list[dict] = []
    for response in responses:
        response.raise_for_status()
        _append_docs(response.json().get("documents", []), seen, places)

    return places


def _append_docs(docs: list, seen: set, places: list) -> None:
    for doc in docs:
        pid = doc["id"]
        if pid in seen:
            continue
        seen.add(pid)
        category_id = _parse_category(doc.get("category_name", ""))
        places.append({
            "kakao_place_id": pid,
            "name": doc["place_name"],
            "address": doc["road_address_name"] or doc["address_name"],
            "lat": float(doc["y"]),
            "lng": float(doc["x"]),
            "kakao_category": doc.get("category_name", ""),
            "category_id": category_id,
            "kakao_url": doc.get("place_url", ""),
        })


def _parse_category(kakao_category: str) -> int:
    for kw, cid in KAKAO_CATEGORY_MAP.items():
        if kw in kakao_category:
            return cid
    return PlaceCategory.RESTAURANT
