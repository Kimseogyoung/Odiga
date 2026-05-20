"""
Playwright으로 트위터 검색 → 장소 언급 수집.
로그인 없이 .env의 auth_token + ct0 쿠키로 세션 구성.

쿠키 얻는 법:
  Chrome → x.com 로그인 → F12 → Application → Cookies → https://x.com
  → auth_token, ct0 값을 .env에 복사

실행: python scripts/collect_twitter.py
      python scripts/collect_twitter.py --debug   (브라우저 화면 표시)
      python scripts/collect_twitter.py --resume  (중단된 지점부터 이어서)
의존성: pip install playwright && playwright install chromium
"""
import argparse
import asyncio
import json
import random
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


OUTPUT_PATH       = Path(__file__).parent.parent / "data" / "collected_twitter.json"
CHECKPOINT_PATH   = Path(__file__).parent.parent / "data" / "twitter_checkpoint.json"

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

TWEETS_PER_QUERY      = 30
SCROLL_COUNT          = 2
SLEEP_AFTER_SCROLL    = 1.5
SLEEP_BETWEEN_QUERIES = 8.0    # 쿼리 간 기본 대기 (+0~5s 랜덤)
SLEEP_ON_EMPTY        = 120.0  # 결과 0개 → 2분 대기
RATE_LIMIT_BACKOFF    = [120.0, 300.0, 600.0, 900.0]  # 지수 백오프 단계 (초)

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


class RateLimitError(Exception):
    pass


async def search_tweets(page: Page, query: str) -> list[str]:
    collected: list[str] = []
    rate_limited = False

    async def on_response(response):
        nonlocal rate_limited
        if "SearchTimeline" not in response.url:
            return
        if response.status == 429:
            rate_limited = True
            return
        try:
            data = await response.json()
            # Twitter가 rate limit 에러를 200으로 감싸서 보내는 경우
            errors = data.get("errors", [])
            if any(e.get("code") == 88 for e in errors):
                rate_limited = True
                return
            collected.extend(_parse_tweets_from_response(data))
        except Exception:
            pass

    page.on("response", on_response)
    encoded = urllib.parse.quote(query)
    await page.goto(
        f"https://x.com/search?q={encoded}&src=typed_query&f=top",
        wait_until="load",
    )
    await page.wait_for_timeout(1500)

    if rate_limited:
        page.remove_listener("response", on_response)
        raise RateLimitError("HTTP 429 / rate limit 코드 감지")

    for _ in range(SCROLL_COUNT):
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        await page.wait_for_timeout(int(SLEEP_AFTER_SCROLL * 1000))
        if rate_limited:
            break

    page.remove_listener("response", on_response)

    if rate_limited:
        raise RateLimitError("스크롤 중 rate limit 감지")

    return collected[:TWEETS_PER_QUERY]


def _load_checkpoint() -> tuple[dict[str, list[str]], set[str]]:
    if not CHECKPOINT_PATH.exists():
        return {}, set()
    try:
        cp = json.loads(CHECKPOINT_PATH.read_text(encoding="utf-8"))
        return defaultdict(list, cp["tweets"]), set(cp["done_queries"])
    except Exception:
        return {}, set()


def _save_checkpoint(region_tweets: dict, done_queries: set) -> None:
    CHECKPOINT_PATH.write_text(
        json.dumps({"tweets": dict(region_tweets), "done_queries": list(done_queries)},
                   ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def _save_results(region_tweets: dict) -> None:
    results: list[dict] = []
    for region_label, tweets in region_tweets.items():
        unique_tweets = list(dict.fromkeys(tweets))
        results.append({"region_label": region_label, "tweets": unique_tweets})

    data_str = json.dumps(results, ensure_ascii=False, indent=2)
    OUTPUT_PATH.write_text(data_str, encoding="utf-8")
    backup = OUTPUT_PATH.parent / f"collected_twitter_{datetime.now().strftime('%y%m%d%H%M')}.json"
    backup.write_text(data_str, encoding="utf-8")

    total = sum(len(r["tweets"]) for r in results)
    print(f"\n총 {total}개 트윗 저장 → {OUTPUT_PATH}")
    print(f"백업 → {backup.name}")


async def _wait(seconds: float, label: str) -> None:
    print(f"    {label} — {int(seconds)}초 대기 중...", flush=True)
    await asyncio.sleep(seconds)


async def run(debug: bool = False, resume: bool = False) -> None:
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    if not settings.TWITTER_AUTH_TOKEN or not settings.TWITTER_CT0:
        print("오류: .env에 TWITTER_AUTH_TOKEN / TWITTER_CT0 설정 필요")
        print("Chrome → x.com 로그인 → F12 → Application → Cookies → https://x.com")
        sys.exit(1)

    region_tweets: dict[str, list[str]] = defaultdict(list)
    done_queries: set[str] = set()

    if resume:
        region_tweets, done_queries = _load_checkpoint()
        if done_queries:
            print(f"체크포인트 로드 — 완료된 쿼리 {len(done_queries)}개, 이어서 실행")

    total_queries = sum(len(q) for q in REGION_QUERIES.values())
    done_count = len(done_queries)
    backoff_step = 0

    async with async_playwright() as p:
        launch_opts: dict = {
            "headless": not debug,
            "slow_mo": 300 if debug else 0,
            "args": ["--no-sandbox", "--disable-dev-shm-usage"],
        }
        try:
            browser = await p.chromium.launch(**launch_opts, channel="chrome")
        except Exception:
            browser = await p.chromium.launch(**launch_opts)

        context = await browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
        )
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

        await page.goto("https://x.com/home", wait_until="load")
        await page.wait_for_timeout(random.randint(2000, 4000))
        if "login" in page.url:
            print("오류: 쿠키 만료. .env의 auth_token / ct0를 다시 복사하세요.")
            await browser.close()
            sys.exit(1)
        print("세션 확인 완료\n")

        for region_label, queries in REGION_QUERIES.items():
            print(f"[{region_label}] 검색 시작")
            for query in queries:
                if query in done_queries:
                    print(f"  SKIP '{query}' (이미 완료)")
                    continue

                done_count += 1
                print(f"  [{done_count}/{total_queries}] '{query}' ...", end=" ", flush=True)

                try:
                    tweets = await search_tweets(page, query)
                    backoff_step = 0  # 성공하면 백오프 리셋

                    if len(tweets) == 0:
                        print(f"0개 (빈 결과)")
                        await _wait(SLEEP_ON_EMPTY, "빈 결과")
                    else:
                        region_tweets[region_label].extend(tweets)
                        done_queries.add(query)
                        _save_checkpoint(region_tweets, done_queries)
                        print(f"{len(tweets)}개 트윗")

                except RateLimitError as e:
                    wait = RATE_LIMIT_BACKOFF[min(backoff_step, len(RATE_LIMIT_BACKOFF) - 1)]
                    backoff_step += 1
                    print(f"RATE LIMIT — {e}")
                    await _wait(wait, f"백오프 {backoff_step}단계")
                    # rate limit 후 동일 쿼리 재시도
                    print(f"  재시도 '{query}' ...", end=" ", flush=True)
                    try:
                        tweets = await search_tweets(page, query)
                        region_tweets[region_label].extend(tweets)
                        done_queries.add(query)
                        _save_checkpoint(region_tweets, done_queries)
                        print(f"{len(tweets)}개 트윗")
                        backoff_step = 0
                    except Exception as e2:
                        print(f"재시도 실패 — {e2}")

                except Exception as e:
                    print(f"실패 — {e}")

                # 쿼리 간 랜덤 딜레이 (사람처럼 보이게)
                jitter = random.uniform(0, 5)
                await asyncio.sleep(SLEEP_BETWEEN_QUERIES + jitter)

        await browser.close()

    # 체크포인트 삭제 (완료)
    if CHECKPOINT_PATH.exists():
        CHECKPOINT_PATH.unlink()

    _save_results(region_tweets)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--debug",  action="store_true", help="브라우저 화면 표시")
    parser.add_argument("--resume", action="store_true", help="중단된 지점부터 이어서 실행")
    args = parser.parse_args()
    asyncio.run(run(debug=args.debug, resume=args.resume))
