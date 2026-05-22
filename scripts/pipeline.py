"""
데이터 파이프라인 CLI.

사용:
  python scripts/pipeline.py [--override KEY=VALUE] <command> [options]

예시:
  python scripts/pipeline.py collect-kakao
  python scripts/pipeline.py embed-places --storage redis
  python scripts/pipeline.py all --storage redis
  python scripts/pipeline.py --override KAKAO_API_KEY=xxx collect-kakao
"""
import asyncio
import os
import sys
from pathlib import Path

import click

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))


def _apply_overrides(overrides: tuple[str, ...]) -> None:
    for item in overrides:
        if "=" not in item:
            click.echo(f"경고: KEY=VALUE 형식 필요: {item}", err=True)
            continue
        key, value = item.split("=", 1)
        os.environ[key.strip()] = value.strip()


@click.group()
@click.option(
    "--override", multiple=True, metavar="KEY=VALUE",
    help=".env 항목 덮어쓰기. 여러 번 사용 가능.",
)
def cli(override: tuple[str, ...]) -> None:
    sys.path.insert(0, str(Path(__file__).parent / "commands"))
    _apply_overrides(override)


@cli.command("collect-kakao")
def collect_kakao() -> None:
    """카카오 장소 수집"""
    from collect_kakao import run
    asyncio.run(run())


@cli.command("collect-naver")
@click.option("-n", "--limit", type=int, default=None, help="처리할 장소 수 제한 (테스트용)")
def collect_naver(limit: int | None) -> None:
    """네이버 리뷰 수집"""
    from collect_naver import run
    asyncio.run(run(limit=limit))


@cli.command("collect-twitter")
@click.option("--debug",  is_flag=True, help="브라우저 화면 표시")
@click.option("--resume", is_flag=True, help="중단된 지점부터 이어서 실행")
def collect_twitter(debug: bool, resume: bool) -> None:
    """트위터 수집"""
    from collect_twitter import run
    asyncio.run(run(debug=debug, resume=resume))


@cli.command("merge")
def merge() -> None:
    """카카오+네이버+트위터 병합"""
    from merge_places import run
    asyncio.run(run())


@cli.command("embed-places")
@click.option("--storage", type=click.Choice(["json", "redis"]), required=True)
def embed_places(storage: str) -> None:
    """장소 임베딩 생성"""
    from embed_places import run
    run(storage=storage)


@cli.command("embed-search-keywords")
@click.option("--storage", type=click.Choice(["json", "redis"]), required=True)
def embed_search_keywords(storage: str) -> None:
    """키워드 조합 임베딩 생성"""
    from embed_search_keywords import run
    run(storage=storage)


@cli.command("all")
@click.option("--storage", type=click.Choice(["json", "redis"]), required=True)
def all_pipeline(storage: str) -> None:
    """전체 파이프라인 순차 실행"""
    from collect_kakao import run as kakao
    from collect_naver import run as naver
    from collect_twitter import run as twitter
    from merge_places import run as merge_run
    from embed_places import run as embed
    from embed_search_keywords import run as keywords

    steps = [
        ("1/6 카카오 수집",   lambda: asyncio.run(kakao())),
        ("2/6 네이버 수집",   lambda: asyncio.run(naver())),
        ("3/6 트위터 수집",   lambda: asyncio.run(twitter())),
        ("4/6 데이터 병합",   lambda: asyncio.run(merge_run())),
        ("5/6 장소 임베딩",   lambda: embed(storage=storage)),
        ("6/6 키워드 임베딩", lambda: keywords(storage=storage)),
    ]
    for label, fn in steps:
        click.echo(f"\n=== {label} ===")
        fn()


if __name__ == "__main__":
    cli()
