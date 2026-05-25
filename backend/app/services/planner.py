import asyncio
import json
import math
import random
import secrets
import time
from datetime import datetime, timedelta

import numpy as np

from app.api.schemas import CourseItem, CourseResponse, PlaceCandidate, SlotInfo
from app.core.config import settings
from app.core.constants import STAY_MINUTES
from app.core.redis import get_redis
from app.services import place_store
from app.services.scorer import get_scorer


# ── 인메모리 벡터 캐시 ────────────────────────────────────────────────────────
# key: (region_id, category_id)
# value: (cached_at, ids, matrix)  ← cached_at: time.monotonic() 기준
_VEC_CACHE_TTL = 60 * 60 * 24  # 1일
_vec_cache: dict[tuple[int, int], tuple[float, list[str], np.ndarray]] = {}


async def _get_vectors(
    region_id: int,
    category_id: int,
) -> tuple[list[str], np.ndarray] | None:
    key = (region_id, category_id)
    now = time.monotonic()

    if key in _vec_cache:
        cached_at, ids, matrix = _vec_cache[key]
        if now - cached_at < _VEC_CACHE_TTL:
            return ids, matrix

    result = await place_store.get_region_category_vectors(region_id, category_id)
    if not result:
        return None
    ids, matrix_flat = result
    matrix = np.array(matrix_flat, dtype=np.float32).reshape(-1, 768)
    _vec_cache[key] = (now, ids, matrix)
    return ids, matrix


# ── 내부 헬퍼 ─────────────────────────────────────────────────────────────────

def _build_candidate(detail: dict, summary_data: dict | None) -> PlaceCandidate:
    summary = summary_data.get("summary", "") if summary_data else ""
    caution = summary_data.get("caution", "") if summary_data else ""
    raw_review = detail.get("blog_reviews", "")
    return PlaceCandidate(
        kakao_place_id=detail["kakao_place_id"],
        name=detail["name"],
        address=detail["address"],
        category_id=detail["category_id"],
        lat=detail["lat"],
        lng=detail["lng"],
        kakao_url=detail.get("kakao_url", ""),
        kakao_category=detail.get("kakao_category", ""),
        summary=summary,
        caution=caution,
        blog_review=raw_review[:150] if raw_review else "",
        photo_url=None,
    )


_CANDIDATE_POOL_SIZE = 15  # 유사도 상위 N개에서 랜덤 추출


def _cosine_top_k(
    query_vec: np.ndarray,
    ids: list[str],
    matrix: np.ndarray,
    exclude_ids: set[str],
    top_k: int,
) -> list[str]:
    """유사도 상위 pool에서 랜덤 top_k 반환. 같은 조건도 매번 다른 결과."""
    norms = np.linalg.norm(matrix, axis=1) * np.linalg.norm(query_vec)
    norms = np.where(norms == 0, 1e-9, norms)
    scores = (matrix @ query_vec) / norms

    ranked = sorted(zip(ids, scores.tolist()), key=lambda x: -x[1])
    filtered = [pid for pid, _ in ranked if pid not in exclude_ids]

    pool = filtered[:_CANDIDATE_POOL_SIZE]
    return random.sample(pool, min(top_k, len(pool)))


# ── 슬롯 계산 ─────────────────────────────────────────────────────────────────

_AVG_SLOT_MINUTES = 90   # 슬롯 수 계산용 평균 체류시간
_TRAVEL_MINUTES   = 15   # 이동시간 기본값 (네이버 API 연동 전)
_MIN_STAY_MINUTES = 60   # 코스 완료 판단 기준 (이 미만이면 done)
_TIME_FMT = "%H:%M"


def _parse_time(t: str) -> datetime:
    return datetime.strptime(t, _TIME_FMT)


def _fmt_time(dt: datetime) -> str:
    return dt.strftime(_TIME_FMT)


def calculate_total_slots(start_time: str, end_time: str) -> int:
    total = (_parse_time(end_time) - _parse_time(start_time)).seconds // 60
    return max(1, total // _AVG_SLOT_MINUTES)


def _advance_time(current_time: str, category_id: int) -> tuple[str, int]:
    """장소 선택 후 current_time 갱신. (다음 시각, 소요 분) 반환."""
    stay = STAY_MINUTES.get(category_id, _AVG_SLOT_MINUTES)
    dt = _parse_time(current_time) + timedelta(minutes=stay + _TRAVEL_MINUTES)
    return _fmt_time(dt), stay


def _remaining(current_time: str, end_time: str) -> int:
    delta = _parse_time(end_time) - _parse_time(current_time)
    return max(0, delta.seconds // 60)


# ── 세션 Redis CRUD ───────────────────────────────────────────────────────────

def _session_key(session_id: str) -> str:
    return f"session:{session_id}"


async def create_session(
    region_id: int,
    keyword_ids: list[int],
    start_time: str,
    end_time: str,
    headcount: int | None,
    budget: int | None,
) -> tuple[str, SlotInfo]:
    """세션 생성. (session_id, 첫 SlotInfo) 반환."""
    session_id = secrets.token_urlsafe(12)
    total_slots = calculate_total_slots(start_time, end_time)

    data = {
        "region_id": region_id,
        "keyword_ids": keyword_ids,
        "start_time": start_time,
        "end_time": end_time,
        "headcount": headcount,
        "budget": budget,
        "total_slots": total_slots,
        "slot_index": 0,
        "current_time": start_time,
        "remaining_minutes": _remaining(start_time, end_time),
        "selected": [],
    }

    redis = await get_redis()
    await redis.set(
        _session_key(session_id),
        json.dumps(data, ensure_ascii=False),
        ex=settings.SESSION_TTL_SECONDS,
    )

    slot = SlotInfo(
        slot_index=0,
        scheduled_time=start_time,
        remaining_minutes=data["remaining_minutes"],
    )
    return session_id, slot


async def get_session(session_id: str) -> dict | None:
    redis = await get_redis()
    data = await redis.get(_session_key(session_id))
    return json.loads(data) if data else None


async def pick_place(session_id: str, session: dict, kakao_place_id: str, category_id: int) -> tuple[bool, SlotInfo | None]:
    """
    장소 선택 처리 후 세션 업데이트.
    반환: (done, 다음 SlotInfo)  done=True 이면 SlotInfo=None
    """
    next_time, stay = _advance_time(session["current_time"], category_id)
    remaining = _remaining(next_time, session["end_time"])
    next_index = session["slot_index"] + 1

    session["selected"].append({
        "kakao_place_id": kakao_place_id,
        "category_id": category_id,
        "scheduled_time": session["current_time"],
        "stay_minutes": stay,
    })
    session["current_time"] = next_time
    session["remaining_minutes"] = remaining
    session["slot_index"] = next_index

    done = remaining < _MIN_STAY_MINUTES or next_index >= session["total_slots"]

    redis = await get_redis()
    await redis.set(
        _session_key(session_id),
        json.dumps(session, ensure_ascii=False),
        ex=settings.SESSION_TTL_SECONDS,
    )

    if done:
        return True, None

    slot = SlotInfo(
        slot_index=next_index,
        scheduled_time=next_time,
        remaining_minutes=remaining,
    )
    return False, slot


# ── 코스 완성 ─────────────────────────────────────────────────────────────────

_WALK_SPEED_KMH   = 4.0  # 도보 속도
_ROUTE_CORRECTION = 1.1  # 직선거리 → 실제 경로 보정 (골목길 10%)


def haversine_minutes(lat1: float, lng1: float, lat2: float, lng2: float) -> int:
    """두 좌표 간 도보 이동시간(분). 계산 불가 시 기본값 15분."""
    try:
        r = 6371  # 지구 반지름 km
        dlat = math.radians(lat2 - lat1)
        dlng = math.radians(lng2 - lng1)
        a = math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlng / 2) ** 2
        km = r * 2 * math.asin(math.sqrt(a))
        minutes = (km * _ROUTE_CORRECTION / _WALK_SPEED_KMH) * 60
        return max(1, round(minutes))
    except Exception:
        return _TRAVEL_MINUTES


async def finalize_course(session: dict) -> str:
    """
    세션의 selected 목록 → 시간표 조립 → Redis 저장 → share_token 반환.
    """
    selected = session["selected"]

    # 장소 상세 전체 병렬 조회
    details = await asyncio.gather(*[
        place_store.get_detail(s["kakao_place_id"]) for s in selected
    ])

    items: list[CourseItem] = []
    for i, (sel, detail) in enumerate(zip(selected, details)):
        if not detail:
            continue

        # 다음 장소와의 이동시간 계산
        if i < len(details) - 1 and details[i + 1]:
            nxt = details[i + 1]
            travel = haversine_minutes(detail["lat"], detail["lng"], nxt["lat"], nxt["lng"])
        else:
            travel = 0  # 마지막 장소는 이동시간 없음

        items.append(CourseItem(
            order=i,
            scheduled_time=sel["scheduled_time"],
            stay_minutes=sel["stay_minutes"],
            travel_time_to_next_minutes=travel,
            place=PlaceCandidate(
                kakao_place_id=detail["kakao_place_id"],
                name=detail["name"],
                address=detail["address"],
                category_id=detail["category_id"],
                lat=detail["lat"],
                lng=detail["lng"],
                kakao_url=detail.get("kakao_url", ""),
                kakao_category=detail.get("kakao_category", ""),
                summary="",
                caution="",
                blog_review="",
                photo_url=None,
            ),
        ))

    share_token = secrets.token_urlsafe(6)  # 8자리 URL-safe 문자열

    course = CourseResponse(
        share_token=share_token,
        region_id=session["region_id"],
        keyword_ids=session["keyword_ids"],
        start_time=session["start_time"],
        end_time=session["end_time"],
        headcount=session.get("headcount"),
        budget=session.get("budget"),
        items=items,
    )

    redis = await get_redis()
    await redis.set(
        f"course:{share_token}",
        course.model_dump_json(),
        ex=settings.TTL_COURSE_SECONDS,
    )

    return share_token


async def get_course(share_token: str) -> CourseResponse | None:
    redis = await get_redis()
    data = await redis.get(f"course:{share_token}")
    if not data:
        return None
    return CourseResponse.model_validate_json(data)


# ── 공개 인터페이스 ────────────────────────────────────────────────────────────

async def search_candidates(
    region_id: int,
    keyword_ids: list[int],
    category_id: int,
    exclude_ids: set[str],
    top_k: int = 3,
) -> list[PlaceCandidate]:
    """
    1. 코사인 유사도 상위 pool 추출
    2. detail 병렬 조회 → scorer로 재정렬 (blog_count 기반)
    3. 재정렬된 pool에서 랜덤 top_k 추출
    4. summary 병렬 조회 후 PlaceCandidate 조립
    """
    query_raw, vec_result = await asyncio.gather(
        place_store.get_keyword_vector(keyword_ids),
        _get_vectors(region_id, category_id),
    )
    if not query_raw or not vec_result:
        return []

    query_vec = np.array(query_raw, dtype=np.float32)
    ids, matrix = vec_result
    pool_ids = _cosine_top_k(query_vec, ids, matrix, exclude_ids, _CANDIDATE_POOL_SIZE)
    if not pool_ids:
        return []

    # pool 전체 detail 병렬 조회 → scorer 재정렬
    details = await asyncio.gather(*[place_store.get_detail(pid) for pid in pool_ids])
    scorer = get_scorer()
    scored = sorted(
        [(detail, scorer.score(detail)) for detail in details if detail],
        key=lambda x: -x[1],
    )

    # 재정렬된 pool에서 랜덤 top_k
    picked_details = random.sample(
        [d for d, _ in scored],
        min(top_k, len(scored)),
    )

    # 선택된 장소의 summary만 병렬 조회
    summaries = await asyncio.gather(*[
        place_store.get_summary(d["kakao_place_id"]) for d in picked_details
    ])

    return [_build_candidate(d, s) for d, s in zip(picked_details, summaries)]
