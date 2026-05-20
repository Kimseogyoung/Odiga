"""
4개 collected_*.json 통합 + Claude Batch API로 요약/키워드 생성.
카카오 ID 기준 중복 제거 후 각 장소에 summary, caution, keyword_ids 추가.
트윗에서 발견된 신규 장소는 카카오 API로 상세 정보 수집 후 포함.

실행: python scripts/process_with_claude.py
출력: data/redis_data.json

사전 조건: data/ 아래 collected_kakao.json, collected_naver.json,
           collected_twitter.json 존재
"""
import asyncio
import hashlib
import json
import re
import sys
import time
from pathlib import Path

import anthropic
import httpx

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from app.core.config import settings
from app.core.constants import PLACE_CATEGORY_LABEL, KAKAO_CATEGORY_MAP, PlaceCategory, Keyword


DATA_DIR    = Path(__file__).parent.parent / "data"
OUTPUT_PATH = DATA_DIR / "redis_data.json"
CACHE_PATH  = DATA_DIR / "claude_cache.json"  # {kakao_place_id: {hash, summary, caution}}

KAKAO_LOCAL_URL = "https://dapi.kakao.com/v2/local/search/keyword.json"

REGION_CENTERS: dict[str, tuple[float, float]] = {
    "성수": (127.0557, 37.5443),
    "홍대": (126.9247, 37.5577),
    "연남": (126.9230, 37.5650),
}

_PLACE_PATTERN = re.compile(r"📍\s*([^\n#@(]{2,20})")
_REGION_ONLY   = {"성수", "홍대", "연남", "성수동", "홍대입구", "연남동", "서울", "카페", "맛집"}

_SYSTEM_PROMPT = "서울 핫플 큐레이터. JSON만 반환. 한국어."

_USER_TEMPLATE = """장소명: {name} / 카테고리: {category}
리뷰: {reviews}
{tweets_section}
{{
  "summary": "한 줄 특징 소개 (장소명 반복 금지)",
  "caution": "방문 팁. 없으면 빈 문자열."
}}"""

# 규칙 기반 키워드 매칭 테이블 {Keyword: [매칭 텍스트]}
_KEYWORD_RULES: dict[int, list[str]] = {
    Keyword.VINTAGE:    ["빈티지", "vintage", "구제"],
    Keyword.HIP:        ["힙", "힙스터", "트렌디"],
    Keyword.KITSCH:     ["키치", "kitsch", "레트로", "복고"],
    Keyword.OTAKU:      ["오타쿠", "피규어", "애니", "덕후"],
    Keyword.CUTE:       ["귀여", "캐릭터", "cute", "인형"],
    Keyword.DESSERT:    ["디저트", "케이크", "마카롱", "빙수", "와플"],
    Keyword.VIBE:       ["감성", "분위기", "뷰", "인테리어"],
    Keyword.DELICIOUS:  ["맛있", "존맛", "맛집", "줄서", "유명"],
    Keyword.HOTPLACE:   ["핫플", "핫한", "인기"],
    Keyword.WAITING:    ["웨이팅", "대기", "줄서", "예약 필수"],
    Keyword.PHOTOGENIC: ["사진", "포토", "인스타", "감성샷"],
    Keyword.QUIET:      ["조용", "한적", "여유"],
    Keyword.SPACIOUS:   ["넓", "대형", "공간"],
    Keyword.PARKING:    ["주차"],
    Keyword.PHOTOSPOT:  ["포토스팟", "포토존", "인생사진"],
}


def _content_hash(place: dict) -> str:
    """리뷰 + 트윗 내용의 해시. 내용이 바뀌면 재처리."""
    raw = (place.get("blog_reviews") or "") + "|" + "|".join(place.get("tweets", []))
    return hashlib.md5(raw.encode()).hexdigest()


def _load_cache() -> dict[str, dict]:
    if not CACHE_PATH.exists():
        return {}
    try:
        return json.loads(CACHE_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _save_cache(cache: dict[str, dict]) -> None:
    CACHE_PATH.write_text(json.dumps(cache, ensure_ascii=False, indent=2), encoding="utf-8")


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


def _filter_tweets_for_place(place_name: str, tweets: list[str]) -> list[str]:
    keywords = [k for k in re.split(r"[\s·]", place_name) if len(k) >= 2]
    if not keywords:
        return []
    return [t for t in tweets if any(k in t for k in keywords)][:5]


def _extract_place_names_from_tweets(tweets: list[str]) -> list[str]:
    seen: set[str] = set()
    names: list[str] = []
    for tweet in tweets:
        for match in _PLACE_PATTERN.finditer(tweet):
            name = match.group(1).strip().rstrip(".")
            if name and name not in seen and name not in _REGION_ONLY and len(name) >= 3:
                seen.add(name)
                names.append(name)
    return names


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


async def merge_sources() -> list[dict]:
    kakao_places = load_json(DATA_DIR / "collected_kakao.json")
    naver_data   = load_json(DATA_DIR / "collected_naver.json")
    twitter_data = load_json(DATA_DIR / "collected_twitter.json")
    google_data  = load_json(DATA_DIR / "collected_google.json")

    naver_map:  dict[str, str]  = {r["kakao_place_id"]: r["blog_reviews"] for r in naver_data}
    google_map: dict[str, dict] = {r["kakao_place_id"]: r for r in google_data}
    region_tweets_map: dict[str, list[str]] = {
        r["region_label"]: r.get("tweets", []) for r in twitter_data
    }

    seen_ids: set[str] = set()
    merged: list[dict] = []

    for place in kakao_places:
        pid = place["kakao_place_id"]
        if pid in seen_ids:
            continue
        seen_ids.add(pid)

        region_label = place.get("region_label", "")
        all_tweets   = region_tweets_map.get(region_label, [])
        google       = google_map.get(pid, {})

        merged.append({
            "kakao_place_id": pid,
            "name":           place["name"],
            "address":        place["address"],
            "lat":            place["lat"],
            "lng":            place["lng"],
            "category_id":    place["category_id"],
            "kakao_category": place.get("kakao_category", ""),
            "kakao_url":      place.get("kakao_url", ""),
            "phone":          place.get("phone", ""),
            "region_label":   region_label,
            "blog_reviews":   naver_map.get(pid, ""),
            "tweets":         _filter_tweets_for_place(place["name"], all_tweets),
            "google_place_id": google.get("google_place_id"),
            "rating":         google.get("rating"),
            "review_count":   google.get("review_count"),
            "opening_hours":  google.get("opening_hours", []),
            "photo_count":    google.get("photo_count", 0),
        })

    print("트윗에서 신규 장소 탐색 중...")
    new_count = 0
    for region_label, tweets in region_tweets_map.items():
        candidates = _extract_place_names_from_tweets(tweets)
        print(f"  [{region_label}] 후보 {len(candidates)}개: {candidates}")
        for name in candidates:
            place = await _fetch_kakao_by_name(name, region_label)
            if place is None:
                print(f"    ✗ '{name}' — 카카오 검색 결과 없음")
                continue
            if place["kakao_place_id"] in seen_ids:
                print(f"    - '{name}' → {place['name']} (이미 존재)")
                continue
            pid = place["kakao_place_id"]
            seen_ids.add(pid)
            merged.append({
                **place,
                "blog_reviews":  naver_map.get(pid, ""),
                "tweets":        _filter_tweets_for_place(place["name"], tweets),
                "google_place_id": None,
                "rating":        None,
                "review_count":  None,
                "opening_hours": [],
                "photo_count":   0,
            })
            new_count += 1
            print(f"    ✓ '{name}' → {place['name']} ({place['address']})")

    print(f"트윗 신규 장소 {new_count}개 추가")
    return merged


def _rule_based_keywords(place: dict) -> list[int]:
    text = " ".join([
        place.get("blog_reviews", ""),
        place.get("kakao_category", ""),
        " ".join(place.get("tweets", [])),
    ]).lower()

    ids = []
    for kid, patterns in _KEYWORD_RULES.items():
        if any(p in text for p in patterns):
            ids.append(kid)
    return ids


def _build_prompt(place: dict) -> str:
    category_label = PLACE_CATEGORY_LABEL.get(place["category_id"], "장소")
    reviews        = place.get("blog_reviews", "") or "없음"
    tweets         = place.get("tweets", [])

    tweets_section = ""
    if tweets:
        lines = "\n".join(f"- {t[:80]}" for t in tweets[:3])
        tweets_section = f"트윗: {lines}\n"

    return _USER_TEMPLATE.format(
        name=place["name"],
        category=category_label,
        reviews=reviews[:400],
        tweets_section=tweets_section,
    )


def _submit_batch(places: list[dict], cache: dict[str, dict]) -> tuple[str, dict[str, dict]]:
    """캐시 미스 장소만 Batch 제출. (batch_id, 업데이트된 캐시) 반환."""
    from anthropic.types.messages.batch_create_params import Request

    client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)

    batch_requests = []
    new_hashes: dict[str, str] = {}  # 이번 실행에서 처리할 장소의 해시

    for place in places:
        pid = place["kakao_place_id"]
        if not place.get("blog_reviews") and not place.get("tweets"):
            continue

        h = _content_hash(place)
        cached = cache.get(pid)
        if cached and cached.get("hash") == h:
            continue  # 캐시 히트 — 스킵

        new_hashes[pid] = h
        batch_requests.append(Request(
            custom_id=pid,
            params=anthropic.types.message_create_params.MessageCreateParamsNonStreaming(
                model="claude-haiku-4-5-20251001",
                max_tokens=256,
                system=_SYSTEM_PROMPT,
                messages=[{"role": "user", "content": _build_prompt(place)}],
            ),
        ))

    cache_hits = sum(
        1 for p in places
        if cache.get(p["kakao_place_id"], {}).get("hash") == _content_hash(p)
        and (p.get("blog_reviews") or p.get("tweets"))
    )
    print(f"캐시 히트: {cache_hits}개 스킵 / 신규·변경: {len(batch_requests)}개 처리")

    if not batch_requests:
        return "", {}

    print(f"Batch 제출 중... ({len(batch_requests)}개 요청)")
    batch = client.messages.batches.create(requests=batch_requests)
    print(f"Batch ID: {batch.id}")
    return batch.id, new_hashes


def _wait_for_batch(batch_id: str) -> dict[str, dict]:
    """배치 완료 대기 후 {kakao_place_id: parsed_result} 반환."""
    client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)

    while True:
        batch = client.messages.batches.retrieve(batch_id)
        counts = batch.request_counts
        print(f"  상태: {batch.processing_status} | "
              f"완료: {counts.succeeded} / 오류: {counts.errored} / 처리중: {counts.processing}")
        if batch.processing_status == "ended":
            break
        time.sleep(30)

    results: dict[str, dict] = {}
    for result in client.messages.batches.results(batch_id):
        pid = result.custom_id
        if result.result.type != "succeeded":
            print(f"  오류 ({pid}): {result.result}")
            continue
        text = next(
            (b.text for b in result.result.message.content if b.type == "text"), ""
        )
        try:
            parsed = json.loads(text.strip())
            results[pid] = parsed
        except json.JSONDecodeError:
            print(f"  JSON 파싱 실패 ({pid}): {text[:80]}")

    return results


def _apply_results(
    places: list[dict],
    results: dict[str, dict],
    cache: dict[str, dict],
    new_hashes: dict[str, str],
) -> list[dict]:
    final = []
    for place in places:
        pid    = place["kakao_place_id"]
        parsed = results.get(pid)
        keyword_ids = _rule_based_keywords(place)
        cached = cache.get(pid)

        if parsed:
            # Batch 결과 → 캐시 갱신
            cache[pid] = {
                "hash":    new_hashes[pid],
                "summary": parsed.get("summary", place["name"]),
                "caution": parsed.get("caution", ""),
            }
            final.append({
                **place,
                "summary":     cache[pid]["summary"],
                "caution":     cache[pid]["caution"],
                "keyword_ids": keyword_ids,
            })
        elif cached and cached.get("summary"):
            # 캐시 히트 — 기존 결과 재사용
            final.append({
                **place,
                "summary":     cached["summary"],
                "caution":     cached.get("caution", ""),
                "keyword_ids": keyword_ids,
            })
        else:
            category_label = PLACE_CATEGORY_LABEL.get(place["category_id"], "장소")
            final.append({
                **place,
                "summary":     f"{category_label} 장소입니다.",
                "caution":     "",
                "keyword_ids": keyword_ids,
            })
    return final


async def run() -> None:
    places = await merge_sources()
    if not places:
        print("처리할 장소 없음. collect_kakao.py부터 실행하세요.")
        sys.exit(1)

    print(f"\n총 {len(places)}개 장소")

    cache = _load_cache()

    batch_id, new_hashes = _submit_batch(places, cache)

    if batch_id:
        print("\nBatch 완료 대기 중... (보통 수 분 이내)")
        results = _wait_for_batch(batch_id)
        print(f"\nBatch 완료: {len(results)}개 결과 수신")
    else:
        results = {}
        new_hashes = {}

    final = _apply_results(places, results, cache, new_hashes)
    _save_cache(cache)

    OUTPUT_PATH.write_text(
        json.dumps(final, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"\n완료: {len(final)}개 장소 저장 → {OUTPUT_PATH}")


if __name__ == "__main__":
    asyncio.run(run())
