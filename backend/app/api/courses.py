from fastapi import APIRouter, HTTPException

from app.api.schemas import (
    CandidatesRequest,
    CandidatesResponse,
    CourseResponse,
    CreateSessionRequest,
    CreateSessionResponse,
    PickRequest,
    PickResponse,
)
from app.core.constants import KEYWORD_LABEL, PLACE_CATEGORY_LABEL, REGION_LABEL
from app.services import place_store, planner

router = APIRouter(prefix="/api")


@router.get("/constants")
async def get_constants():
    return {
        "regions":    {k: v for k, v in REGION_LABEL.items()},
        "categories": {k: v for k, v in PLACE_CATEGORY_LABEL.items()},
        "keywords":   {k: v for k, v in KEYWORD_LABEL.items()},
    }


@router.post("/courses/session", response_model=CreateSessionResponse)
async def create_session(req: CreateSessionRequest):
    session_id, slot = await planner.create_session(
        region_id=req.region_id,
        keyword_ids=req.keyword_ids,
        start_time=req.start_time,
        end_time=req.end_time,
        headcount=req.headcount,
        budget=req.budget,
    )
    total_slots = planner.calculate_total_slots(req.start_time, req.end_time)
    return CreateSessionResponse(session_id=session_id, total_slots=total_slots, slot=slot)


@router.post("/courses/session/{session_id}/candidates", response_model=CandidatesResponse)
async def get_candidates(session_id: str, req: CandidatesRequest):
    session = await planner.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="세션이 없거나 만료되었습니다.")

    exclude_ids = {s["kakao_place_id"] for s in session["selected"]}

    candidates = await planner.search_candidates(
        region_id=session["region_id"],
        keyword_ids=session["keyword_ids"],
        category_id=req.category_id,
        exclude_ids=exclude_ids,
    )
    if not candidates:
        raise HTTPException(status_code=503, detail="해당 조건의 장소 데이터가 없습니다.")

    return CandidatesResponse(candidates=candidates)


@router.post("/courses/session/{session_id}/pick", response_model=PickResponse)
async def pick_place(session_id: str, req: PickRequest):
    session = await planner.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="세션이 없거나 만료되었습니다.")

    detail = await place_store.get_detail(req.kakao_place_id)
    if not detail:
        raise HTTPException(status_code=404, detail="장소를 찾을 수 없습니다.")

    done, slot = await planner.pick_place(
        session_id=session_id,
        session=session,
        kakao_place_id=req.kakao_place_id,
        category_id=detail["category_id"],
    )

    if done:
        share_token = await planner.finalize_course(session)
        return PickResponse(done=True, share_token=share_token)

    return PickResponse(done=False, slot=slot)


@router.get("/courses/{share_token}", response_model=CourseResponse)
async def get_course(share_token: str):
    course = await planner.get_course(share_token)
    if not course:
        raise HTTPException(status_code=404, detail="코스가 없거나 만료되었습니다.")
    return course
