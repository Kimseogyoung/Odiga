# Odiga 서비스 설계 문서

> 실시간 설계 논의 기록. 구현 전 판단 기준으로 사용.

---

## 서비스 개요

지역 + 테마 입력 → AI가 혼잡도/이동시간 포함한 하루 코스 시간표 생성

---

## 서비스 플로우

### 플로우 A — 하나씩 고르기 (MVP, 무료)

```
유저 접속
  → 지역 선택
  → 테마 키워드 선택 (최대 3개)
  → 시작/종료 시간 선택
  → (선택) 인원수 / 예산
  → 코스 만들기 클릭
  → 세션 생성 + 첫 번째 시간대 장소 후보 3개 제시
  → 유저가 1개 선택
  → 다음 시간대 장소 후보 3개 제시 (이전 선택 반영)
  → 반복 → 시간이 다 채워지면 코스 완성
  → 공유 링크 생성
```

### 플로우 B — AI 자동 생성 (추후, 유료)

```
동일 입력
  → AI가 한 번에 최적 코스 자동 생성
  → 시간표 바로 출력
```

---

## 데이터 수집 파이프라인

### 구조
```
[수집 레이어 - 스케줄러]
  Twitter  → 장소명 언급 추출 (트렌드/버즈 감지)
  네이버   → 블로그 API (리뷰 텍스트)
  카카오   → 카카오맵 장소 검색 API (장소 기본 정보)
  Google   → Places API (좌표/영업시간 등)

[정규화 레이어]
  → 장소명 + 주소 기반으로 동일 장소 매핑
  → 카카오맵 ID를 기준 식별자로 통합

[저장 레이어]
  → places 테이블에 통합 저장
  → 각 소스 ID 함께 보관 (naver_id, kakao_id, google_id)
```

### 기준 식별자 — 카카오맵
- 카카오맵 딥링크(길찾기) 연동에 그대로 활용 가능
- 한국 서비스 특화, 공식 API 지원

### 각 소스 역할

| 소스 | 가져오는 것 | 방법 | 출력 파일 |
|------|------------|------|-----------|
| 카카오맵 | 장소명, 주소, 좌표, 카테고리 | 공식 API | collected_kakao.json |
| 네이버 블로그 | 리뷰 텍스트 | 공식 API | collected_naver.json |
| 인스타그램 | 핫플 언급, 해시태그 | 크롤링 | collected_instagram.json |
| Google Places | 영업시간, 평점, 사진 | 공식 API | collected_google.json |

### 수집 → 처리 파이프라인

```
[수집 스크립트 - 플랫폼별 독립 실행]
  scripts/collect_kakao.py      → data/collected_kakao.json
  scripts/collect_naver.py      → data/collected_naver.json
  scripts/collect_instagram.py  → data/collected_instagram.json
  scripts/collect_google.py     → data/collected_google.json

[Claude 처리 스크립트]
  scripts/process_with_claude.py
    → 4개 파일 전부 읽기
    → 카카오 ID 기준으로 중복 제거 + 통합
    → Claude: summary + caution + keyword_id 태깅
    → data/redis_data.json 생성

[사용자 확인]
  data/redis_data.json 검토

[Redis import]
  scripts/import_to_redis.py
    → redis_data.json → Redis 저장
```

---

## Step 1 — 장소 후보 수집

### 유저 입력
- 지역 1개 선택 (성수 / 홍대 / 한남 / 익선동 / 연남동)
- 테마 키워드 N개 선택 (최대 3개)
  - 예: 카페, 커피, 디저트, 맛집, 펍·바, 쇼핑, 전시 등

### 캐싱 전략 — 키워드 단위 쪼개기
- 스케줄러가 **매일 새벽** 지역 × 키워드 단위로 수집 후 Redis 저장
- 유저 요청 시 외부 API 호출 없이 **Redis에서만** 응답

```
[스케줄러 - 매일 새벽]
  지역 5개 × 키워드 N개 조합을 각각 수집
  → places:search:{지역}:{키워드}  TTL 24h

  예)
  places:search:성수:카페    → kakao_place_id 목록 20개
  places:search:성수:커피    → kakao_place_id 목록 20개
  places:search:성수:디저트  → kakao_place_id 목록 20개

[유저 요청 시]
  선택한 키워드별 Redis 목록 조회
  → 서버에서 kakao_place_id 중복 제거 후 합산
  → 외부 API 호출 0번
```

### 규모
- 지역 5개 × 키워드 15개 = **하루 75번** 호출로 모든 조합 커버
- 유저가 어떤 조합을 선택해도 항상 캐시 히트

---

## Step 2 — 장소 상세 + AI 요약

### 실행 주체
- **스케줄러** — Step 1 캐싱 직후 연속 실행 (매일 새벽)
- 유저 요청 시점에는 이미 완성된 요약만 사용

### 흐름
```
[스케줄러 - Step 1 이후]
  캐싱된 place_id 목록 전체 순회
    → Redis ai:summary:{place_id} 존재 여부 확인
    → 없는 것만 처리 (이미 요약된 장소는 skip)

  없는 장소:
    1. Google Places Detail API 호출
       가져올 필드: reviews(5개), editorial_summary, photo_reference
    2. GPT 요약 생성
    3. Redis ai:summary:{place_id} 저장  TTL 7일
    4. Redis places:detail:{place_id} 업데이트
```

### GPT 호출 방식 — 개별 호출 + 병렬 처리
- 장소별로 개별 호출, `asyncio.gather`로 병렬 실행
- Rate Limit 대응: `asyncio.Semaphore(10)` — 동시 호출 최대 10개 제한
- 배치 묶기 방식은 파싱 복잡 + 에러 격리 불가로 제외

### GPT 입출력
```
입력: 장소명, 카테고리, 리뷰 5개 원문 (한국어)

출력 JSON:
{
  "summary": "성수 감성 가득한 카페. 사진 맛집으로 유명.",
  "caution": "주말 웨이팅 1시간 이상",
  "tags": ["포토스팟", "혼잡", "넓은 공간"]
}
```

### 비용 추산
- Claude Haiku 기준 장소 1개 ≈ $0.0001
- 75개 전체 ≈ 하루 **$0.008** (무시 가능)

---

## Step 3 — 코스 편성

### 방식 — 규칙 기반 (GPT 없음)
GPT 코스 편성 없이 규칙으로 처리. 추후 품질 업그레이드 시 GPT로 교체 가능.

### 편성 규칙
```
1. 후보 장소 필터링
   - rating 4.0 이상만
   - 현재 영업 중인 곳만 (opening_hours 기준)

2. 카테고리 균형 배분
   - 같은 카테고리 연속 2개 이상 금지
   - 유저가 선택한 키워드 비율 반영
     예: 카페 2개 + 맛집 1개 선택 → 카페 : 맛집 = 2 : 1 비율로 배치

3. 장소 수 결정
   - (종료시간 - 시작시간) ÷ 평균 체류시간으로 자동 계산
   - 카테고리별 기본 체류시간: 카페 90분 / 식당 60분 / 쇼핑 60분 / 전시 90분

4. 순서 결정
   - rating 높은 순으로 정렬 후 카테고리 균형 맞게 배치
```

### GPT 역할 — 코스 소개 문구 1개만
```
입력: 지역, 테마 키워드, 선정된 장소 목록

출력:
{
  "intro": "성수 감성 카페 투어. 브런치로 시작해 디저트로 마무리하는 여유로운 하루."
}
```

---

## Step 4 — 이동시간 계산

### 방식 — Haversine 직선거리 (MVP)
추후 네이버 Directions API로 교체 가능하도록 함수 단위로 분리.

```
두 장소의 위도/경도 → Haversine 공식으로 직선거리 계산
→ 도보 속도 4km/h 적용 → 분 단위 환산
→ 10% 보정값 추가 (골목/실제 경로 오차 보완)
```

### 추후 교체 계획
- 네이버 Directions API 도입 시 함수 내부만 교체
- UI/응답 구조 변경 없음

---

## Step 5 — 응답 조립 + 저장

### 공유 링크
- `odiga.com/course/{share_token}` 방식
- share_token: nanoid 8자리

### 저장 정책

| 구분 | MVP | 추후 (회원 도입 후) |
|------|-----|-------------------|
| 선택형 코스 생성 | 횟수 제한 없음 | 동일 |
| AI 자동생성 (유료) | 미구현 | 횟수 or 구독 제한 |
| 코스 저장 (비회원) | Redis TTL 7일 | 동일 |
| 코스 저장 (회원 무료) | - | DB 영구 보관, 최대 10개 |
| 코스 저장 (프리미엄) | - | DB 영구 보관, 무제한 |

### MVP 흐름 (Redis only)
```
코스 완성
  → share_token 발급 (nanoid 8자리)
  → Redis course:{token} 저장 TTL 7일
  → 응답 반환

공유 링크 접근 시:
  → Redis course:{token} 조회
  → 없으면 만료 안내
```

---

## DB 스키마

### 설계 원칙
- 카테고리/키워드는 문자열 대신 **int 저장**
- int ↔ 문자열 매핑은 서버 시작 시 메모리에 로드 (DB 조회 없음)
- 매핑 데이터는 `backend/app/core/constants.py`에 정의

---

### 매핑 상수 (constants.py)

```python
# 지역
REGION = {
    1: "성수",
    2: "홍대",
    3: "연남",
}

# 장소 카테고리 — 큰 분류 (카카오맵 원본 카테고리 → 매핑)
PLACE_CATEGORY = {
    1: "음식점",
    2: "카페",
    3: "쇼핑",
    4: "바/펍",
    5: "전시/문화",
}

# 키워드 — 분위기/특징 태그 (유저가 선택하는 값)
KEYWORD = {
    1:  "빈티지",
    2:  "힙한",
    3:  "키치한",
    4:  "오타쿠",
    5:  "귀여운",
    6:  "디저트",
    7:  "감성",
    8:  "존맛",
    9:  "핫플",
    10: "웨이팅 맛집",
    11: "사진찍기 좋은",
    # 분위기
    12: "조용한",
    13: "넓은",
    14: "주차장",
    15: "포토스팟",
}
```

---

### 테이블 구조

```
places
  id
  kakao_place_id      (unique)
  naver_place_id      (nullable)
  google_place_id     (nullable)

  name
  address
  region              (int) → { 1: 성수, 2: 홍대, 3: 한남, ... }
  category_id         (int) → PLACE_CATEGORY
  lat, lng

  kakao_category      (varchar, 원본값 보관용)
  google_rating       (float, nullable)
  google_photo_url    (nullable)

  ai_summary
  ai_caution
  created_at, updated_at

place_keywords          ← 장소 ↔ 키워드 N:M
  place_id → places
  keyword_id          (int) → KEYWORD

courses
  id
  share_token         (unique, nanoid 8자리)
  region              (int)
  user_id             (nullable, 회원만)
  extra_data          (JSON)  ← 유연한 확장 필드
  created_at

  -- extra_data 예시
  -- {
  --   "keywords": [1, 3, 5],
  --   "headcount": 2,
  --   "budget": 50000,
  --   "start_time": "10:00",
  --   "end_time": "18:00",
  --   "intro": "성수 감성 카페 투어..."   ← GPT 생성 소개문구
  -- }

course_items
  id
  course_id → courses
  place_id  → places
  order
  scheduled_time
  stay_minutes
  travel_time_to_next_minutes

users                   ← M6
  id
  kakao_user_id       (unique)
  nickname
  created_at
```

---

## Redis 캐시 구조

### MVP 구현 원칙
- **DB 없이 Redis만 사용** (설계 변경 여지가 많으므로)
- DB 스키마는 설계 확정 후 별도 마이그레이션

### 키 구조

```
places:search:{region_id}:{keyword_id}
  → kakao_place_id 목록 (JSON 배열)
  → TTL 24h
  → 스케줄러가 매일 새벽 갱신

places:detail:{kakao_place_id}
  → 장소 상세 정보 (JSON)
  → { kakao_place_id, name, address, region, category_id,
      lat, lng, google_rating, photo_url }
  → TTL 24h

ai:summary:{kakao_place_id}
  → GPT 생성 요약 (JSON)
  → { summary, caution, tags: [keyword_id, ...] }
  → TTL 7일

course:{share_token}
  → 코스 전체 (JSON)
  → { share_token, region, extra_data, items: [...] }
  → TTL 7일 (비회원 기준)
```

### 저장 흐름 요약
```
스케줄러 (매일 새벽)
  → places:search 갱신
  → places:detail 갱신
  → ai:summary 없는 것만 생성

유저 요청 시
  → Redis에서 search + detail + summary 조회
  → 규칙 기반 코스 편성
  → GPT 소개문구 생성
  → course:{token} 저장
  → 응답 반환
```

---

## API 명세

### MVP 엔드포인트

```
GET  /api/constants
  → 지역/카테고리/키워드 매핑 전체 반환 (프론트 초기 로드용)

POST /api/courses/session
  body: { region_id, keyword_ids, start_time, end_time, headcount?, budget? }
  → session_id 발급
  → 첫 번째 시간대 장소 후보 3개 반환

POST /api/courses/session/{session_id}/pick
  body: { kakao_place_id }
  → 선택 저장
  → 다음 시간대 장소 후보 3개 반환
  → 코스 완성 시: { done: true, share_token }

GET  /api/courses/{share_token}
  → 완성된 코스 전체 조회
```

### 세션 상태 (Redis)

```
session:{session_id}
  {
    region_id, keyword_ids,
    start_time, end_time,
    headcount, budget,
    selected: [
      { kakao_place_id, scheduled_time, stay_minutes, travel_time_to_next }
    ],
    current_time: "12:30",       ← 현재까지 채워진 시간
    remaining_minutes: 150       ← 남은 시간
  }
  TTL 30분 (세션 만료)
```

### 후보 제시 로직
```
남은 시간 기반으로 카테고리 자동 결정
  예: 남은 시간 90분 이상 → 카페 or 식당
      남은 시간 60분 이하 → 카페 or 디저트

이미 선택된 장소 제외
연속 같은 카테고리 제외
후보 추출: rating 상위 풀에서 랜덤 4개 (매번 다른 결과)
  → rating 상위 15개 추출 → 그 중 랜덤 4개 선택
```

### 추후 (유료)
```
POST /api/courses/generate
  → AI가 한 번에 전체 코스 자동 생성
```
