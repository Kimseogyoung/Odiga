"""
키워드 조합(1~5개) 쿼리 벡터 사전 생성.

실행:
  python scripts/embed_search_keywords.py --storage json    # data/search_keywords.json 저장
  python scripts/embed_search_keywords.py --storage redis   # Redis 저장
의존성: pip install sentence-transformers
"""
import argparse
import asyncio
import json
import sys
from itertools import combinations
from pathlib import Path

DATA_DIR    = Path(__file__).parent.parent / "data"
OUTPUT_PATH = DATA_DIR / "search_keywords.json"

BATCH_SIZE    = 256
PIPELINE_SIZE = 500


def _all_keyword_combos(keyword_label: dict[int, str]) -> list[tuple[int, ...]]:
    combos = []
    for r in range(1, 6):
        combos.extend(combinations(sorted(keyword_label.keys()), r))
    return combos


def _build_query_text(keyword_ids: tuple[int, ...], keyword_label: dict[int, str]) -> str:
    return " ".join(keyword_label[kid] for kid in keyword_ids)


def _generate(keyword_label: dict[int, str]) -> list[tuple[tuple[int, ...], str, list[float]]]:
    try:
        from sentence_transformers import SentenceTransformer
    except ImportError:
        print("오류: pip install sentence-transformers 먼저 실행하세요.")
        sys.exit(1)

    combos = _all_keyword_combos(keyword_label)
    texts  = [_build_query_text(c, keyword_label) for c in combos]

    print(f"키워드 조합 {len(combos)}개 (1~5개 선택)")
    print("모델 로드 중...")
    model = SentenceTransformer("jhgan/ko-sroberta-multitask")

    print("임베딩 생성 중...")
    vectors = model.encode(texts, batch_size=BATCH_SIZE, show_progress_bar=True)

    return [(combo, text, vec.tolist()) for combo, text, vec in zip(combos, texts, vectors)]


def _save_to_json(results: list[tuple[tuple[int, ...], str, list[float]]]) -> None:
    data = [
        {"keyword_ids": list(combo), "text": text, "vector": vector}
        for combo, text, vector in results
    ]
    OUTPUT_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"저장 완료 → {OUTPUT_PATH}  ({len(data)}개, 약 {OUTPUT_PATH.stat().st_size // 1024 // 1024}MB)")


async def _save_to_redis(results: list[tuple[tuple[int, ...], str, list[float]]]) -> None:
    sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))
    from app.core.redis import init_redis, close_redis, get_redis
    from app.services.place_store import _keyword_key

    TTL = 60 * 60 * 24 * 30
    print(f"\nRedis 저장 시작 ({len(results)}개)...")
    await init_redis()
    redis = await get_redis()

    saved = 0
    for i in range(0, len(results), PIPELINE_SIZE):
        chunk = results[i : i + PIPELINE_SIZE]
        pipe  = redis.pipeline()
        for keyword_ids, _, vector in chunk:
            pipe.set(_keyword_key(list(keyword_ids)), json.dumps(vector), ex=TTL)
        await pipe.execute()
        saved += len(chunk)
        print(f"  {saved}/{len(results)} 저장 완료", end="\r")

    await close_redis()
    print(f"\nRedis 저장 완료 — query:keyword:* {len(results)}개")


def run(storage: str) -> None:
    sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))
    from app.core.constants import KEYWORD_LABEL

    results = _generate(KEYWORD_LABEL)
    print(f"\n생성 완료 — 벡터 차원: {len(results[0][2])}")

    if storage == "json":
        _save_to_json(results)
    else:
        asyncio.run(_save_to_redis(results))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--storage", choices=["json", "redis"], required=True,
        help="저장 방식 선택: json → search_keywords.json, redis → Redis 저장",
    )
    args = parser.parse_args()
    run(storage=args.storage)
