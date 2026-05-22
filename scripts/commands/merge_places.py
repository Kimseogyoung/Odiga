"""
수집된 데이터를 병합하고 트윗에서 신규 장소를 발굴.

1. 카카오 + 네이버 데이터 병합
2. Claude Batch로 트윗에서 장소명 추출 (지역당 1 요청)
3. 추출된 신규 장소 카카오 API 검색 후 추가
4. data/merged_places.json 저장

실행: python scripts/merge_places.py
출력: data/merged_places.json
"""
import asyncio
import json
import sys
from pathlib import Path

import anthropic
import httpx

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "backend"))

from app.core.config import settings
from app.core.constants import KAKAO_CATEGORY_MAP, PlaceCategory

DATA_DIR    = Path(__file__).parent.parent.parent / "data"
OUTPUT_PATH = DATA_DIR / "merged_places.json"

KAKAO_LOCAL_URL = "https://dapi.kakao.com/v2/local/search/keyword.json"

REGION_CENTERS: dict[str, tuple[float, float]] = {
    "성수": (127.0557, 37.5443),
    "홍대": (126.9247, 37.5577),
    "연남": (126.9230, 37.5650),
}


def load_json(path: Path) -> list[dict]:
    if not path.exists():
        print(f"경고: {path.name} 없음 — 건너뜀")
        return []
    return json.loads(path.read_text(encoding="utf-8"))


def _parse_category(kakao_category: str) -> int:
    for kw, cid in KAKAO_CATEGORY_MAP.items():
        if kw in kakao_category:
            return cid
    return PlaceCategory.RESTAURANT


async def _fetch_kakao_by_name(name: str, region_label: str) -> dict | None:
    center = REGION_CENTERS.get(region_label)
    if not center:
        return None
    headers = {"Authorization": f"KakaoAK {settings.KAKAO_API_KEY}"}
    params  = {"query": name, "x": str(center[0]), "y": str(center[1]), "radius": 1000, "size": 1}
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(KAKAO_LOCAL_URL, headers=headers, params=params, timeout=10)
            resp.raise_for_status()
            docs = resp.json().get("documents", [])
        except Exception:
            return None
    if not docs:
        return None
    doc = docs[0]
    return {
        "kakao_place_id": doc["id"],
        "name":           doc["place_name"],
        "address":        doc.get("road_address_name") or doc.get("address_name", ""),
        "lat":            float(doc["y"]),
        "lng":            float(doc["x"]),
        "kakao_category": doc.get("category_name", ""),
        "category_id":    _parse_category(doc.get("category_name", "")),
        "kakao_url":      doc.get("place_url", ""),
        "phone":          doc.get("phone", ""),
        "region_label":   region_label,
    }


# ── 1단계: 카카오 + 네이버 병합 ───────────────────────────────────────────────

def merge_kakao_naver(twitter_data: list[dict]) -> tuple[list[dict], dict[str, list[str]]]:
    kakao_places = load_json(DATA_DIR / "collected_kakao.json")
    naver_data   = load_json(DATA_DIR / "collected_naver.json")

    print(f"  카카오: {len(kakao_places)}개 로드")
    print(f"  네이버: {len(naver_data)}개 로드")
    print(f"  트위터: {sum(len(r.get('tweets',[])) for r in twitter_data)}개 트윗 로드")

    naver_map: dict[str, str] = {r["kakao_place_id"]: r["blog_reviews"] for r in naver_data}
    region_tweets_map: dict[str, list[str]] = {
        r["region_label"]: r.get("tweets", []) for r in twitter_data
    }

    seen_ids: set[str] = set()
    places: list[dict] = []

    for place in kakao_places:
        pid = place["kakao_place_id"]
        if pid in seen_ids:
            continue
        seen_ids.add(pid)
        places.append({
            **place,
            "blog_reviews": naver_map.get(pid, ""),
            "tweets":       [],
            "source":       "kakao",
        })

    naver_matched = sum(1 for p in places if p["blog_reviews"])
    print(f"  네이버 리뷰 매핑: {naver_matched}/{len(places)}개")

    return places, region_tweets_map


# ── 2단계: Claude로 트윗에서 장소명 추출 ─────────────────────────────────────

def extract_places_from_tweets(region_tweets_map: dict[str, list[str]]) -> dict[str, list[str]]:
    client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
    results: dict[str, list[str]] = {}

    for region_label, tweets in region_tweets_map.items():
        if not tweets:
            print(f"  [{region_label}] 트윗 없음 — 스킵")
            continue

        print(f"  [{region_label}] 트윗 {len(tweets)}개 → Claude 호출 중...")
        tweets_text = "\n".join(f"- {t[:200]}" for t in tweets[:80])

        resp = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=512,
            system="장소명 추출 전문가. JSON 배열만 반환.",
            messages=[{
                "role": "user",
                "content": (
                    f"아래 {region_label} 지역 SNS 트윗에서 언급된 구체적인 가게명/장소명을 추출하세요.\n"
                    f"일반 단어(맛집, 카페, 핫플 등)나 지역명은 제외, 실제 상호명만 추출하세요.\n\n"
                    f"트윗:\n{tweets_text}\n\n"
                    f'JSON 배열로만 반환: ["장소명1", "장소명2", ...]'
                ),
            }],
        )

        text = next(
            (b.text for b in resp.content if b.type == "text"), ""
        ).strip()
        try:
            names = json.loads(text)
            if isinstance(names, list):
                results[region_label] = [str(n) for n in names if n]
                print(f"  [{region_label}] {len(results[region_label])}개 추출: "
                      f"{results[region_label][:5]}{'...' if len(results[region_label]) > 5 else ''}")
        except json.JSONDecodeError:
            print(f"  파싱 실패 [{region_label}]: {text[:80]}")

    return results


# ── 3단계: 신규 장소 카카오 검색 ─────────────────────────────────────────────

async def discover_new_places(
    extracted: dict[str, list[str]],
    existing_ids: set[str],
) -> list[dict]:
    new_places: list[dict] = []

    for region_label, names in extracted.items():
        print(f"  [{region_label}] 카카오 검색 중...")
        for name in names:
            place = await _fetch_kakao_by_name(name, region_label)
            if place is None:
                print(f"    ✗ '{name}' — 검색 결과 없음")
                continue
            if place["kakao_place_id"] in existing_ids:
                print(f"    - '{name}' → {place['name']} (이미 존재)")
                continue
            existing_ids.add(place["kakao_place_id"])
            new_places.append({**place, "blog_reviews": "", "tweets": [], "source": "twitter"})
            print(f"    ✓ '{name}' → {place['name']} ({place['address']})")

    return new_places


# ── 메인 ─────────────────────────────────────────────────────────────────────

async def run() -> None:
    print("=== 1단계: 카카오 + 네이버 병합 ===")
    twitter_data = load_json(DATA_DIR / "collected_twitter.json")
    places, region_tweets_map = merge_kakao_naver(twitter_data)
    print(f"  카카오 장소: {len(places)}개")

    print("\n=== 2단계: 트윗에서 장소명 추출 (Claude) ===")
    extracted = extract_places_from_tweets(region_tweets_map)

    print("\n=== 3단계: 신규 장소 카카오 검색 ===")
    existing_ids = {p["kakao_place_id"] for p in places}
    new_places   = await discover_new_places(extracted, existing_ids)
    places.extend(new_places)
    print(f"  신규 {len(new_places)}개 추가 → 총 {len(places)}개")

    OUTPUT_PATH.write_text(
        json.dumps(places, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"\n완료 → {OUTPUT_PATH}")


if __name__ == "__main__":
    asyncio.run(run())
