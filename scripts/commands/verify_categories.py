# -*- coding: utf-8 -*-
"""
카테고리 분류 버그 검증 스크립트.
파이프라인 수정 전후 양쪽에서 실행해서 비교한다.

사용법:
  python scripts/commands/verify_categories.py
"""
import asyncio
import json
import sys
from collections import Counter
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "backend"))

from app.core.constants import KAKAO_CATEGORY_MAP, PLACE_CATEGORY_LABEL, REGION_LABEL, PlaceCategory
from app.core.redis import get_redis, init_redis, close_redis
from app.services.place_store import get_region_category_vectors, get_detail

DATA_DIR    = Path(__file__).parent.parent.parent / "data"
MERGED_PATH = DATA_DIR / "merged_places.json"


def _parse_category(kakao_category: str) -> int:
    for kw, cid in KAKAO_CATEGORY_MAP.items():
        if kw in kakao_category:
            return cid
    return PlaceCategory.RESTAURANT


# ── 1. merged_places.json 분석 ──────────────────────────────────────────────

def check_json() -> None:
    if not MERGED_PATH.exists():
        print("[JSON] merged_places.json 없음")
        return

    places = json.loads(MERGED_PATH.read_text(encoding="utf-8"))
    print(f"\n[JSON] merged_places.json - 총 {len(places)}개\n")

    current_dist     = Counter(p["category_id"] for p in places)
    reclassified     = Counter(_parse_category(p.get("kakao_category", "")) for p in places)

    print(f"  {'카테고리':<10} {'현재':>6}  {'수정 후':>6}  {'변화':>6}")
    print("  " + "-" * 38)
    for cid in sorted(set(current_dist) | set(reclassified)):
        label   = PLACE_CATEGORY_LABEL.get(cid, "?")
        cur     = current_dist.get(cid, 0)
        new     = reclassified.get(cid, 0)
        diff    = new - cur
        sign    = f"+{diff}" if diff > 0 else str(diff)
        print(f"  {label:<10} {cur:>6}   {new:>6}   {sign:>6}")

    wrong = [
        p for p in places
        if p["category_id"] != _parse_category(p.get("kakao_category", ""))
    ]
    print(f"\n  오분류 장소: {len(wrong)}개")

    if wrong:
        print("\n  샘플 (최대 8개):")
        for p in wrong[:8]:
            old_label = PLACE_CATEGORY_LABEL.get(p["category_id"], "?")
            new_cid   = _parse_category(p.get("kakao_category", ""))
            new_label = PLACE_CATEGORY_LABEL.get(new_cid, "?")
            name      = p["name"][:22]
            kcat      = p.get("kakao_category", "")[:38]
            print(f"    [{old_label} -> {new_label}] {name}")
            print(f"    kakao_category: {kcat}")


# ── 2. Redis 버킷 상태 ───────────────────────────────────────────────────────

async def check_redis() -> None:
    print("\n[Redis] region x category 버킷 장소 수\n")
    print(f"  {'지역':<6} {'카테고리':<10} {'장소수':>5}  샘플")
    print("  " + "-" * 55)

    for region_id, region_name in REGION_LABEL.items():
        for category_id, category_name in PLACE_CATEGORY_LABEL.items():
            result = await get_region_category_vectors(region_id, category_id)
            if result is None:
                count  = 0
                sample = ""
                flag   = "  <- 비어있음"
            else:
                ids, _ = result
                count  = len(ids)
                flag   = ""
                if ids:
                    detail = await get_detail(ids[0])
                    sample = detail["name"][:20] if detail else ids[0][:20]
                else:
                    sample = ""

            print(f"  {region_name:<4}   {category_name:<10} {count:>4}개  {sample}{flag}")

    print(f"\n[Redis] 연남(3) + 카페(2) 버킷 상세:")
    result = await get_region_category_vectors(3, 2)
    if result is None:
        print("  -> 데이터 없음")
    else:
        ids, _ = result
        print(f"  -> 장소 {len(ids)}개")
        for pid in ids[:5]:
            detail = await get_detail(pid)
            if detail:
                kcat = detail.get("kakao_category", "")[:40]
                print(f"    {detail['name']:<25} | {kcat}")


async def main() -> None:
    print("=" * 60)
    print("카테고리 분류 검증")
    print("=" * 60)

    check_json()

    try:
        await init_redis()
        await check_redis()
        await close_redis()
    except Exception as e:
        print(f"\n[Redis] 연결 실패: {e}")

    print("\n" + "=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
