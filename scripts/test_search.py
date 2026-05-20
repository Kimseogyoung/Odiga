"""
임베딩 검색 테스트.
실행: python scripts/test_search.py
"""
import json
import sys
from pathlib import Path

import numpy as np

DATA_DIR   = Path(__file__).parent.parent / "data"
VECTORS_PATH = DATA_DIR / "place_vectors.json"


def cosine_similarity(a: list[float], b: list[float]) -> float:
    a, b = np.array(a), np.array(b)
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))


def search(query: str, places: list[dict], model, top_k: int = 10) -> list[dict]:
    query_vec = model.encode(query).tolist()
    scored = [
        (cosine_similarity(query_vec, p["embedding"]), p)
        for p in places if p.get("embedding")
    ]
    scored.sort(key=lambda x: x[0], reverse=True)
    return [(score, p) for score, p in scored[:top_k]]


def main():
    if not VECTORS_PATH.exists():
        print("오류: place_vectors.json 없음. generate_embeddings.py 먼저 실행하세요.")
        sys.exit(1)

    print("데이터 로드 중...")
    places = json.loads(VECTORS_PATH.read_text(encoding="utf-8"))
    print(f"총 {len(places)}개 장소 로드")

    print("모델 로드 중...")
    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer("jhgan/ko-sroberta-multitask")
    print("준비 완료\n")

    while True:
        query = input("검색어 입력 (종료: q): ").strip()
        if query.lower() == "q":
            break
        if not query:
            continue

        results = search(query, places, model)
        print(f"\n['{query}' 검색 결과 Top 10]")
        print("-" * 60)
        for i, (score, p) in enumerate(results, 1):
            print(f"{i:2}. {p['name']:<20} [{p['region_label']}] {p['kakao_category'][:20]}")
            print(f"    유사도: {score:.3f} | {p['address'][:35]}")
        print()


if __name__ == "__main__":
    main()
