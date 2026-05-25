from pydantic import BaseModel, field_validator


# ── 요청 모델 ─────────────────────────────────────────────────────────────────

class CreateSessionRequest(BaseModel):
    region_id: int
    keyword_ids: list[int]
    start_time: str   # "HH:MM"
    end_time: str     # "HH:MM"
    headcount: int | None = None
    budget: int | None = None

    @field_validator("keyword_ids")
    @classmethod
    def keyword_ids_not_empty(cls, v: list[int]) -> list[int]:
        if not v:
            raise ValueError("keyword_ids는 최소 1개 이상이어야 합니다.")
        return v


class CandidatesRequest(BaseModel):
    category_id: int


class PickRequest(BaseModel):
    kakao_place_id: str


# ── 응답 조각 ─────────────────────────────────────────────────────────────────

class PlaceCandidate(BaseModel):
    kakao_place_id: str
    name: str
    address: str
    category_id: int
    lat: float
    lng: float
    kakao_url: str
    kakao_category: str = ""
    summary: str
    caution: str
    blog_review: str = ""
    photo_url: str | None = None
    walk_minutes_from_prev: int | None = None


class SlotInfo(BaseModel):
    slot_index: int      # 0-based
    scheduled_time: str  # "HH:MM"
    remaining_minutes: int


# ── 응답 모델 ─────────────────────────────────────────────────────────────────

class CreateSessionResponse(BaseModel):
    session_id: str
    total_slots: int
    slot: SlotInfo


class CandidatesResponse(BaseModel):
    candidates: list[PlaceCandidate]


class PickResponse(BaseModel):
    done: bool
    slot: SlotInfo | None = None          # done=False 일 때
    share_token: str | None = None        # done=True 일 때


class CourseItem(BaseModel):
    order: int
    scheduled_time: str
    stay_minutes: int
    travel_time_to_next_minutes: int
    place: PlaceCandidate


class CourseResponse(BaseModel):
    share_token: str
    region_id: int
    keyword_ids: list[int]
    start_time: str
    end_time: str
    headcount: int | None = None
    budget: int | None = None
    items: list[CourseItem]
