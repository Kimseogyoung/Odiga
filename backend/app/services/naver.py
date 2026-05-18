import httpx
from app.core.config import settings


NAVER_BLOG_URL = "https://openapi.naver.com/v1/search/blog.json"


async def fetch_blog_reviews(place_name: str, region: str) -> str:
    """장소명으로 네이버 블로그 검색 후 리뷰 텍스트 반환."""
    headers = {
        "X-Naver-Client-Id": settings.NAVER_CLIENT_ID,
        "X-Naver-Client-Secret": settings.NAVER_CLIENT_SECRET,
    }
    params = {"query": f"{region} {place_name} 후기", "display": 5, "sort": "sim"}

    async with httpx.AsyncClient() as client:
        response = await client.get(NAVER_BLOG_URL, headers=headers, params=params)
        response.raise_for_status()
        data = response.json()

    items = data.get("items", [])
    if not items:
        return ""

    # 제목 + 설명 텍스트 합산 (HTML 태그 제거)
    texts = []
    for item in items:
        title = _strip_html(item.get("title", ""))
        desc = _strip_html(item.get("description", ""))
        texts.append(f"{title}. {desc}")

    return " ".join(texts)


def _strip_html(text: str) -> str:
    import re
    return re.sub(r"<[^>]+>", "", text)
