"""
merged_places.json을 읽어 각 장소의 임베딩 벡터 생성.
--save-to-redis 플래그를 주면 생성 후 Redis 저장까지 이어서 실행.

실행: python scripts/embed_places.py
      python scripts/embed_places.py --save-to-redis
입력: data/merged_places.json  (merge_places.py 먼저 실행 필요)
출력: data/place_vectors.json
의존성: pip install sentence-transformers
"""
import argparse
import asyncio
import json
import sys
from pathlib import Path

DATA_DIR    = Path(__file__).parent.parent / "data"
INPUT_PATH  = DATA_DIR / "merged_places.json"
OUTPUT_PATH = DATA_DIR / "place_vectors.json"

TTL = 60 * 60 * 24 * 30  # 30일


def _build_embed_text(place: dict) -> str:
    parts = [
        place["name"],
        place.get("kakao_category", ""),
        place.get("region_label", ""),
        (place.get("blog_reviews") or "")[:400],
    ]
    tweets = place.get("tweets", [])
    if tweets:
        parts.append(" ".join(t[:80] for t in tweets[:3]))
    return " | ".join(p for p in parts if p)


def _generate_vectors(places: list[dict]) -> list[dict]:
    try:
        from sentence_transformers import SentenceTransformer
    except ImportError:
        print("오류: pip install sentence-transformers 먼저 실행하세요.")
        sys.exit(1)

    print("모델 로드 중... (첫 실행 시 다운로드 ~500MB)")
    model = SentenceTransformer("jhgan/ko-sroberta-multitask")

    texts = [_build_embed_text(p) for p in places]
    print("임베딩 생성 중...")
    vectors = model.encode(texts, batch_size=64, show_progress_bar=True)

    for place, vector in zip(places, vectors):
        place["embedding"] = vector.tolist()

    return places


async def _save_to_redis(places: list[dict]) -> None:
    sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))
    from app.core.redis import init_redis, close_redis, get_redis

    print(f"\nRedis 저장 시작 ({len(places)}개)...")
    await init_redis()
    redis = await get_redis()

    pipe = redis.pipeline()
    all_ids: list[str] = []

    for place in places:
        pid = place["kakao_place_id"]
        all_ids.append(pid)

        detail = {k: v for k, v in place.items() if k != "embedding"}
        vector = place.get("embedding")

        pipe.set(f"places:detail:{pid}", json.dumps(detail, ensure_ascii=False), ex=TTL)
        if vector is not None:
            pipe.set(f"places:vector:{pid}", json.dumps(vector), ex=TTL)

    pipe.set("places:all_ids", json.dumps(all_ids), ex=TTL)
    await pipe.execute()

    await close_redis()
    print(f"Redis 저장 완료 — detail {len(places)}개, vector {len(places)}개, all_ids 갱신")


def run(save_to_redis: bool = False) -> None:
    if not INPUT_PATH.exists():
        print("오류: merged_places.json 없음. 먼저 merge_places.py를 실행하세요.")
        sys.exit(1)

    places = json.loads(INPUT_PATH.read_text(encoding="utf-8"))
    print(f"장소 {len(places)}개 로드")

    places = _generate_vectors(places)

    OUTPUT_PATH.write_text(
        json.dumps(places, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"\n완료 → {OUTPUT_PATH}")
    print(f"벡터 차원: {len(places[0]['embedding'])}")

    if save_to_redis:
        asyncio.run(_save_to_redis(places))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--save-to-redis", action="store_true", help="생성 후 Redis에도 저장")
    args = parser.parse_args()
    run(save_to_redis=args.save_to_redis)
