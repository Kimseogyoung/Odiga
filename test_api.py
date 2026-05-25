"""
M2 통합 테스트 — 전체 플로우 자동 실행
실행 전 서버를 먼저 띄울 것: python run.py
"""
import httpx

BASE = "http://localhost:8000/api"


def section(title: str):
    print(f"\n{'='*50}")
    print(f"  {title}")
    print('='*50)


def ok(label: str, value):
    print(f"  [OK] {label}: {value}")


def fail(label: str, res: httpx.Response):
    print(f"  [FAIL] {label}: {res.status_code} {res.text}")
    raise SystemExit(1)


def main():
    client = httpx.Client(timeout=10)

    # ── 1. constants ──────────────────────────────────────────
    section("1. GET /api/constants")
    res = client.get(f"{BASE}/constants")
    if res.status_code != 200:
        fail("constants", res)
    data = res.json()
    ok("지역 수",    len(data["regions"]))
    ok("카테고리 수", len(data["categories"]))
    ok("키워드 수",  len(data["keywords"]))

    # ── 2. 세션 생성 ──────────────────────────────────────────
    section("2. POST /api/courses/session")
    res = client.post(f"{BASE}/courses/session", json={
        "region_id":   1,
        "keyword_ids": [1, 7],
        "start_time":  "10:00",
        "end_time":    "18:00",
        "headcount":   2,
    })
    if res.status_code != 200:
        fail("session", res)
    session_data = res.json()
    session_id  = session_data["session_id"]
    total_slots = session_data["total_slots"]
    ok("session_id",  session_id)
    ok("total_slots", total_slots)
    ok("첫 슬롯 시간", session_data["slot"]["scheduled_time"])
    ok("남은 시간(분)", session_data["slot"]["remaining_minutes"])

    # ── 3~5. candidates → pick 반복 ──────────────────────────
    # 홀수 슬롯: 카페(2), 짝수 슬롯: 음식점(1) 번갈아 선택
    category_cycle = [2, 1, 2, 1, 2, 1, 2]

    for turn in range(total_slots + 2):  # 혹시 슬롯 초과돼도 안전하게
        section(f"3-{turn+1}. candidates 요청 (슬롯 {turn})")
        category_id = category_cycle[turn % len(category_cycle)]
        res = client.post(
            f"{BASE}/courses/session/{session_id}/candidates",
            json={"category_id": category_id},
        )
        if res.status_code != 200:
            fail("candidates", res)
        candidates = res.json()["candidates"]
        ok("후보 수",    len(candidates))
        ok("카테고리 확인", all(c["category_id"] == category_id for c in candidates))
        for c in candidates:
            print(f"     - {c['name']} ({c['address'][:15]})")

        # 첫 번째 후보 선택
        picked = candidates[0]["kakao_place_id"]
        section(f"4-{turn+1}. pick → {candidates[0]['name']}")
        res = client.post(
            f"{BASE}/courses/session/{session_id}/pick",
            json={"kakao_place_id": picked},
        )
        if res.status_code != 200:
            fail("pick", res)
        pick_data = res.json()
        ok("done", pick_data["done"])

        if pick_data["done"]:
            share_token = pick_data["share_token"]
            ok("share_token", share_token)
            break
        else:
            slot = pick_data["slot"]
            ok("다음 슬롯 시간",  slot["scheduled_time"])
            ok("남은 시간(분)",  slot["remaining_minutes"])
    else:
        print("\n[FAIL] done=True가 반환되지 않았습니다.")
        raise SystemExit(1)

    # ── 6. 코스 조회 ──────────────────────────────────────────
    section(f"5. GET /api/courses/{share_token}")
    res = client.get(f"{BASE}/courses/{share_token}")
    if res.status_code != 200:
        fail("get_course", res)
    course = res.json()
    ok("share_token",  course["share_token"])
    ok("지역",         course["region_id"])
    ok("코스 장소 수", len(course["items"]))
    print()
    for item in course["items"]:
        travel = item["travel_time_to_next_minutes"]
        travel_str = f"→ 이동 {travel}분" if travel else "→ (마지막)"
        print(f"  [{item['scheduled_time']}] {item['place']['name']} "
              f"({item['stay_minutes']}분 체류) {travel_str}")

    section("통합 테스트 완료")


if __name__ == "__main__":
    main()
