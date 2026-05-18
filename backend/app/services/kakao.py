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

    seen: set[str] = set()
    places: list[dict] = []

    async with httpx.AsyncClient() as client:
        # category_group_code 기반 (정확한 분류)
        for code in CATEGORY_CODES:
            params = {"query": region_label, "size": 15, "category_group_code": code}
            response = await client.get(KAKAO_LOCAL_URL, headers=headers, params=params)
            response.raise_for_status()
            data = response.json()
            _append_docs(data.get("documents", []), seen, places)

        # 키워드 기반 (술집, 편집샵 등 코드 없는 것)
        for suffix in KEYWORD_QUERIES:
            params = {"query": f"{region_label} {suffix}", "size": 15}
            response = await client.get(KAKAO_LOCAL_URL, headers=headers, params=params)
            response.raise_for_status()
            data = response.json()
            _append_docs(data.get("documents", []), seen, places)

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
