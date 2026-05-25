"""
Claude Haiku를 활용한 장소 요약 및 키워드 태깅.

[미구현] place별 AI 요약 데이터 생성 파이프라인
  - 구현 위치: scripts/commands/summarize_places.py (신규 작성 필요)
  - 실행 시점: embed_places.py 실행 후 (Redis에 places:detail 저장된 후)
  - 로직:
      merged_places.json 읽기
      → place_store.summary_exists(pid) 로 이미 있는 것 skip
      → summarize_place() + tag_keywords() 병렬 호출 (asyncio.Semaphore(10))
      → place_store.save_summary(pid, result) 저장
  - 비용: Claude Haiku 기준 1622개 약 $1.14 (1회)
  - TTL: 제거 권장 (장소 데이터는 파이프라인 실행 시에만 변경됨)
  - 현재 상태: Redis에 ai:summary 없음 → PlaceCandidate.summary = ""
"""
import json
import anthropic
from app.core.config import settings
from app.core.constants import KEYWORD_LABEL


_client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)

_SUMMARIZE_SYSTEM = """당신은 서울 핫플레이스 전문 큐레이터입니다.
장소 정보와 블로그 리뷰를 분석해서 JSON 형태로 요약을 작성합니다.
반드시 한국어로, 반드시 아래 JSON 형식만 반환하세요. 설명 없이 JSON만."""

_SUMMARIZE_TEMPLATE = """장소명: {name}
카테고리: {category}
블로그 리뷰:
{reviews}
{tweets_section}
위 정보를 바탕으로 아래 JSON 형식으로만 응답하세요:
{{
  "summary": "이 장소의 특징을 담은 한 줄 소개. 장소명 그대로 쓰지 말고 특징을 설명할 것. (예: '성수 감성 뜨개카페. 취미 재료 구비.')",
  "caution": "방문 시 주의사항이나 팁. 없으면 빈 문자열."
}}"""

_KEYWORD_SYSTEM = """당신은 서울 핫플레이스 전문 큐레이터입니다.
장소 정보를 보고 어울리는 키워드 ID를 골라 JSON 배열로 반환하세요.
설명 없이 JSON 배열만 반환하세요."""

_KEYWORD_TEMPLATE = """장소명: {name}
카테고리: {category}
한줄 소개: {summary}
블로그 리뷰: {reviews}

아래 키워드 목록 중 이 장소에 어울리는 것의 ID만 골라 배열로 반환하세요:
{keyword_list}

예시: [1, 4, 7]"""


async def summarize_place(
    name: str,
    category: str,
    reviews: str,
    tweets: list[str] | None = None,
) -> dict:
    """장소 정보 + 블로그 리뷰 + SNS 트윗 → 한줄 요약 + 주의사항 생성."""
    tweets = tweets or []
    if not reviews and not tweets:
        return {"summary": f"{category} 장소입니다.", "caution": ""}

    tweets_section = ""
    if tweets:
        lines = "\n".join(f"- {t[:120]}" for t in tweets[:5])
        tweets_section = f"SNS 트윗:\n{lines}\n"

    message = _client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=256,
        system=_SUMMARIZE_SYSTEM,
        messages=[{
            "role": "user",
            "content": _SUMMARIZE_TEMPLATE.format(
                name=name,
                category=category,
                reviews=reviews[:1500] if reviews else "없음",
                tweets_section=tweets_section,
            ),
        }],
    )
    try:
        return json.loads(message.content[0].text.strip())
    except json.JSONDecodeError:
        return {"summary": name, "caution": ""}


async def tag_keywords(name: str, category: str, summary: str, reviews: str) -> list[int]:
    """장소 정보 → 어울리는 키워드 ID 목록 반환."""
    keyword_list = "\n".join(
        f"  {kid}: {label}" for kid, label in KEYWORD_LABEL.items()
    )

    message = _client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=128,
        system=_KEYWORD_SYSTEM,
        messages=[{
            "role": "user",
            "content": _KEYWORD_TEMPLATE.format(
                name=name,
                category=category,
                summary=summary,
                reviews=reviews[:800],
                keyword_list=keyword_list,
            ),
        }],
    )
    try:
        result = json.loads(message.content[0].text.strip())
        return [int(k) for k in result if isinstance(k, (int, str))]
    except (json.JSONDecodeError, ValueError):
        return []
