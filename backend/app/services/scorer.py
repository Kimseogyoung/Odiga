"""
장소 인기도 점수 계산 인터페이스 (Strategy 패턴).

현재 구현체: BlogCountScorer (네이버 블로그 검색 결과 수 기반)
교체 방법: get_scorer()가 반환하는 인스턴스만 바꾸면 됨.

향후 교체 예시:
    class NaverRatingScorer(PlaceScorer):
        def score(self, place: dict) -> float:
            return place.get("naver_rating", 0.0)

    # get_scorer()에서 NaverRatingScorer() 반환하도록 수정
"""
from abc import ABC, abstractmethod


class PlaceScorer(ABC):
    @abstractmethod
    def score(self, place: dict) -> float:
        """place detail dict를 받아 인기도 점수 반환. 높을수록 우선."""
        ...


class BlogCountScorer(PlaceScorer):
    """네이버 블로그 검색 결과 수(blog_count)를 인기도 점수로 사용."""

    def score(self, place: dict) -> float:
        return float(place.get("blog_count", 0))


# ── 현재 사용 중인 scorer ─────────────────────────────────────────────────────
# 교체 시 이 한 줄만 수정.
def get_scorer() -> PlaceScorer:
    return BlogCountScorer()
