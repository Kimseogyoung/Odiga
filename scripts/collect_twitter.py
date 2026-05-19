"""
Playwright으로 트위터 검색 → 장소 언급 수집.
로그인 없이 .env의 auth_token + ct0 쿠키로 세션 구성.

쿠키 얻는 법:
  Chrome → x.com 로그인 → F12 → Application → Cookies → https://x.com
  → auth_token, ct0 값을 .env에 복사

실행: python scripts/collect_twitter.py
      python scripts/collect_twitter.py --debug  (브라우저 화면 표시)
의존성: pip install playwright && playwright install chromium
"""
import argparse
import asyncio
import json
import re
import sys
import urllib.parse
from collections import defaultdict
from datetime import datetime
from pathlib import Path

try:
    from playwright.async_api import async_playwright, Page
except ImportError:
    print("playwright 없음. 설치: pip install playwright && playwright install chromium")
    sys.exit(1)

try:
    from playwright_stealth import stealth_async
    _STEALTH = True
except ImportError:
    _STEALTH = False

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from app.core.config import settings


OUTPUT_PATH = Path(__file__).parent.parent / "data" / "collected_twitter.json"

REGION_QUERIES: dict[str, list[str]] = {
    "성수": [
        "성수 📍", "성수동 📍",
        "성수 맛집 📍", "성수 카페 📍", "성수 핫플 📍",
    ],
    "홍대": [
        "홍대 📍", "홍대입구 📍",
        "홍대 맛집 📍", "홍대 카페 📍", "홍대 핫플 📍",
    ],
    "연남": [
        "연남동 📍", "연남 📍",
        "연남동 맛집 📍", "연남동 카페 📍",
    ],
}

TWEETS_PER_QUERY      = 100
SCROLL_COUNT          = 3
SLEEP_AFTER_SCROLL    = 2.0
SLEEP_BETWEEN_QUERIES = 3.0

_PLACE_PATTERN = re.compile(
    r"📍\s*([^\n#@]{2,20})|"
    r"[「『\[\(《【]([^\]】』」\)》]{2,20})[」』\]\)》】]"
)


def extract_place_mentions(text: str) -> list[str]:
    mentions = []
    for match in _PLACE_PATTERN.finditer(text):
        name = (match.group(1) or match.group(2) or "").strip()
        if name:
            mentions.append(name)
    return mentions


def _parse_tweets_from_response(data: dict) -> list[str]:
    texts = []
    try:
        instructions = (
            data["data"]["search_by_raw_query"]
                ["search_timeline"]["timeline"]["instructions"]
        )
        for instruction in instructions:
            for entry in instruction.get("entries", []):
                result = (
                    entry.get("content", {})
                         .get("itemContent", {})
                         .get("tweet_results", {})
                         .get("result", {})
                )
                text = result.get("legacy", {}).get("full_text", "")
                if text:
                    texts.append(text)
    except (KeyError, TypeError):
        pass
    return texts


async def search_tweets(page: Page, query: str) -> list[str]:
    collected: list[str] = []

    async def on_response(response):
        if "SearchTimeline" in response.url:
            try:
                data = await response.json()
                collected.extend(_parse_tweets_from_response(data))
            except Exception:
                pass

    page.on("response", on_response)

    encoded = urllib.parse.quote(query)
    await page.goto(
        f"https://x.com/search?q={encoded}&src=typed_query&f=live",
        wait_until="load",
    )
    await page.wait_for_timeout(2000)

    for _ in range(SCROLL_COUNT):
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        await page.wait_for_timeout(SLEEP_AFTER_SCROLL * 1000)

    page.remove_listener("response", on_response)
    return collected[:TWEETS_PER_QUERY]


async def run(debug: bool = False) -> None:
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    if not settings.TWITTER_AUTH_TOKEN or not settings.TWITTER_CT0:
        print("오류: .env에 TWITTER_AUTH_TOKEN / TWITTER_CT0 설정 필요")
        print("Chrome → x.com 로그인 → F12 → Application → Cookies → https://x.com")
        sys.exit(1)

    mention_counts: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    total_queries = sum(len(q) for q in REGION_QUERIES.values())
    done = 0

    async with async_playwright() as p:
        launch_opts: dict = {
            "headless": not debug,
            "slow_mo": 300 if debug else 0,
            "args": ["--no-sandbox", "--disable-dev-shm-usage"],
        }
        if debug:
            try:
                browser = await p.chromium.launch(**launch_opts, channel="chrome")
            except Exception:
                browser = await p.chromium.launch(**launch_opts)
        else:
            browser = await p.chromium.launch(**launch_opts)

        context = await browser.new_context()

        # .env 쿠키로 세션 구성
        await context.add_cookies([
            {
                "name": "auth_token",
                "value": settings.TWITTER_AUTH_TOKEN,
                "domain": ".x.com",
                "path": "/",
                "httpOnly": True,
                "secure": True,
            },
            {
                "name": "ct0",
                "value": settings.TWITTER_CT0,
                "domain": ".x.com",
                "path": "/",
                "secure": True,
            },
        ])

        page = await context.new_page()
        if _STEALTH:
            await stealth_async(page)

        # 세션 유효 확인
        await page.goto("https://x.com/home", wait_until="load")
        await page.wait_for_timeout(2000)
        if "login" in page.url:
            print("오류: 쿠키가 만료됐거나 잘못됐습니다. .env의 auth_token / ct0를 다시 복사하세요.")
            await browser.close()
            sys.exit(1)
        print("세션 확인 완료")

        for region_label, queries in REGION_QUERIES.items():
            print(f"\n[{region_label}] 검색 시작")
            for query in queries:
                done += 1
                print(f"  [{done}/{total_queries}] '{query}' ...", end=" ", flush=True)
                try:
                    tweets = await search_tweets(page, query)
                    count = 0
                    for tweet in tweets:
                        places = extract_place_mentions(tweet)
                        for place in places:
                            mention_counts[region_label][place] += 1
                        count += 1
                    print(f"{count}개 트윗")
                except Exception as e:
                    print(f"실패 — {e}")

                await asyncio.sleep(SLEEP_BETWEEN_QUERIES)

        await browser.close()

    results: list[dict] = []
    for region_label, place_counts in mention_counts.items():
        for place_name, mention_count in sorted(place_counts.items(), key=lambda x: x[1], reverse=True):
            results.append({
                "region_label": region_label,
                "name": place_name,
                "twitter_mention_count": mention_count,
            })

    data_str = json.dumps(results, ensure_ascii=False, indent=2)
    OUTPUT_PATH.write_text(data_str, encoding="utf-8")
    backup = OUTPUT_PATH.parent / f"collected_twitter_{datetime.now().strftime('%y%m%d%H%M')}.json"
    backup.write_text(data_str, encoding="utf-8")

    total = sum(len(v) for v in mention_counts.values())
    print(f"\n총 {total}개 장소 언급 저장 → {OUTPUT_PATH}")
    print(f"백업 → {backup.name}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--debug", action="store_true", help="브라우저 화면 표시 (로컬 디버깅용)")
    args = parser.parse_args()
    asyncio.run(run(debug=args.debug))
