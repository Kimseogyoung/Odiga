"""
instaloader로 지역 해시태그 포스트에서 장소 언급 수집.
로그인 없이 공개 해시태그 피드만 사용 (rate limit 주의).

실행: python scripts/collect_instagram.py
출력: data/collected_instagram.json

의존성: pip install instaloader
"""
import json
import re
import sys
import time
from collections import defaultdict
from datetime import datetime
from pathlib import Path

try:
    import instaloader
except ImportError:
    print("instaloader 없음. 설치: pip install instaloader")
    sys.exit(1)

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from app.core.constants import REGION_LABEL


OUTPUT_PATH = Path(__file__).parent.parent / "data" / "collected_instagram.json"

# 지역별 해시태그
REGION_HASHTAGS: dict[str, list[str]] = {
    "성수": ["성수동카페", "성수카페", "성수맛집", "성수동맛집", "성수핫플"],
    "홍대": ["홍대카페", "홍대맛집", "홍대핫플", "홍대술집"],
    "연남": ["연남동카페", "연남카페", "연남맛집", "연남동맛집"],
}

# 해시태그당 수집할 최대 포스트 수
MAX_POSTS_PER_TAG = 50

# 요청 간 딜레이 (초) — rate limit 방지
SLEEP_BETWEEN_TAGS = 10

# 장소명 추출에 사용할 정규식 (@ 멘션, 특수기호 앞 단어 등)
_PLACE_PATTERN = re.compile(
    r"[「『\[\(《【]([^\]】』」\)》]{2,20})[」』\]\)》】]|"  # 괄호 안 텍스트
    r"📍\s*([^\n#@]{2,20})"                              # 📍 뒤 텍스트
)


def extract_place_mentions(caption: str) -> list[str]:
    """캡션에서 장소명 후보 추출."""
    mentions = []
    for match in _PLACE_PATTERN.finditer(caption):
        name = (match.group(1) or match.group(2) or "").strip()
        if name:
            mentions.append(name)
    return mentions


def run() -> None:
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    loader = instaloader.Instaloader(
        download_pictures=False,
        download_videos=False,
        download_video_thumbnails=False,
        download_geotags=False,
        download_comments=False,
        save_metadata=False,
        quiet=True,
    )

    # 장소별 언급 카운트: {region_label: {place_name: count}}
    mention_counts: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))

    for region_label, hashtags in REGION_HASHTAGS.items():
        print(f"\n[{region_label}] 해시태그 수집 시작")

        for tag in hashtags:
            print(f"  #{tag} 수집 중...")
            try:
                hashtag = instaloader.Hashtag.from_name(loader.context, tag)
                count = 0

                for post in hashtag.get_posts():
                    if count >= MAX_POSTS_PER_TAG:
                        break
                    caption = post.caption or ""
                    places = extract_place_mentions(caption)
                    for place in places:
                        mention_counts[region_label][place] += 1
                    count += 1

                print(f"    {count}개 포스트 처리")
            except Exception as e:
                print(f"    실패: {e}")

            time.sleep(SLEEP_BETWEEN_TAGS)

    # 결과 정리: 지역별 언급 빈도 상위 장소 목록
    results: list[dict] = []
    for region_label, place_counts in mention_counts.items():
        sorted_places = sorted(place_counts.items(), key=lambda x: x[1], reverse=True)
        for place_name, mention_count in sorted_places:
            results.append({
                "region_label": region_label,
                "name": place_name,
                "instagram_mention_count": mention_count,
            })

    data_str = json.dumps(results, ensure_ascii=False, indent=2)
    OUTPUT_PATH.write_text(data_str, encoding="utf-8")
    backup = OUTPUT_PATH.parent / f"collected_instagram_{datetime.now().strftime('%y%m%d%H%M')}.json"
    backup.write_text(data_str, encoding="utf-8")

    total = sum(len(v) for v in mention_counts.values())
    print(f"\n총 {total}개 장소 언급 저장 → {OUTPUT_PATH}")
    print(f"백업 → {backup.name}")


if __name__ == "__main__":
    run()
