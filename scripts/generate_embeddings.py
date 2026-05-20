"""
merged_places.json을 읽어 각 장소의 임베딩 벡터 생성.

실행: python scripts/generate_embeddings.py
입력: data/merged_places.json  (merge_places.py 먼저 실행 필요)
출력: data/place_vectors.json
의존성: pip install sentence-transformers
"""
import json
import sys
from pathlib import Path

DATA_DIR    = Path(__file__).parent.parent / "data"
INPUT_PATH  = DATA_DIR / "merged_places.json"
OUTPUT_PATH = DATA_DIR / "place_vectors.json"


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


def run() -> None:
    if not INPUT_PATH.exists():
        print("오류: merged_places.json 없음. 먼저 merge_places.py를 실행하세요.")
        sys.exit(1)

    try:
        from sentence_transformers import SentenceTransformer
    except ImportError:
        print("오류: pip install sentence-transformers 먼저 실행하세요.")
        sys.exit(1)

    places = json.loads(INPUT_PATH.read_text(encoding="utf-8"))
    print(f"장소 {len(places)}개 로드")

    print("모델 로드 중... (첫 실행 시 다운로드 ~500MB)")
    model = SentenceTransformer("jhgan/ko-sroberta-multitask")

    texts = [_build_embed_text(p) for p in places]
    print(f"임베딩 생성 중...")
    vectors = model.encode(texts, batch_size=64, show_progress_bar=True)

    for place, vector in zip(places, vectors):
        place["embedding"] = vector.tolist()

    OUTPUT_PATH.write_text(
        json.dumps(places, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"\n완료 → {OUTPUT_PATH}")
    print(f"벡터 차원: {len(places[0]['embedding'])}")


if __name__ == "__main__":
    run()
