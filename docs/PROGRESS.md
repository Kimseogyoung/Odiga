# Odiga 진행 상황

> 세션 간 이어서 작업하기 위한 현재 상태 기록.

---

## 현재 마일스톤: M1 — 데이터 수집 파이프라인 완성

---

## 완료된 것

### 설계
- [x] `docs/DESIGN.md` — 전체 서비스 설계 문서 완성
- [x] `PROJECT.md` — 마일스톤 업데이트 (선택형 MVP, AI자동생성 유료 등)

### 백엔드 기반 세팅
- [x] `backend/app/core/config.py` — Settings (DATABASE_URL, GOOGLE_PLACES_API_KEY optional 처리)
- [x] `backend/app/core/constants.py` — Region / PlaceCategory / Keyword 상수 + 매핑 테이블
- [x] `backend/app/core/redis.py` — Redis 연결
- [x] `backend/.env` — 카카오 / 네이버 / Anthropic API 키 세팅 완료

### 서비스 코드
- [x] `backend/app/services/kakao.py` — 지역 기반 장소 검색 (category_group_code 사용)
- [x] `backend/app/services/naver.py` — 블로그 리뷰 수집
- [x] `backend/app/services/claude.py` — 요약 생성 + 키워드 태깅
- [x] `backend/app/services/place_store.py` — Redis 저장/조회

### 테스트
- [x] `backend/test_run.py` — 카카오 검색 → 네이버 리뷰 → Claude 요약 1회 테스트
  - 카카오 검색: 동작 확인 (category_group_code 방식)
  - 네이버 블로그: 동작 확인
  - Claude 요약: 동작 확인 (프롬프트 보강 필요)

---

## 다음 할 일 (M1 완성까지)

### 1. 수집 스크립트 4개 작성
각 플랫폼에서 장소 데이터를 최대한 많이 수집. 특정 장소 쏠림 없이 다양하게.

- [ ] `scripts/collect_kakao.py`
  - 지역 × 카테고리 코드로 전체 수집
  - 출력: `data/collected_kakao.json`

- [ ] `scripts/collect_naver.py`
  - 지역 키워드로 블로그 포스트 수집 (장소명 + 리뷰 텍스트)
  - 출력: `data/collected_naver.json`

- [ ] `scripts/collect_instagram.py`
  - 지역 해시태그 기반 크롤링 (장소명, 언급 수)
  - 출력: `data/collected_instagram.json`

- [ ] `scripts/collect_google.py`
  - Google Places API (영업시간, 평점, 사진)
  - Google Places API 키 필요 (미발급)
  - 출력: `data/collected_google.json`

### 2. Claude 처리 스크립트
- [ ] `scripts/process_with_claude.py`
  - 4개 collected_*.json 읽기
  - 카카오 ID 기준 중복 제거 + 통합
  - Claude: summary + caution + keyword_id 배열 생성
  - 출력: `data/redis_data.json`

### 3. 사용자 검토
- [ ] `data/redis_data.json` 내용 확인

### 4. Redis import
- [ ] `scripts/import_to_redis.py`
  - redis_data.json → Redis 저장

---

## 미결 사항

| 항목 | 내용 |
|------|------|
| Google Places API 키 | ~~미발급~~ 완료 |
| 인스타 크롤링 방식 | **instaloader** 확정 (해시태그 기반 장소 수집 용도) |
| Claude 요약 프롬프트 | 장소명만 반환하는 케이스 발생 → 추가 튜닝 필요 |

---

## API 키 현황

| 서비스 | 상태 |
|--------|------|
| 카카오 REST API | 완료 |
| 네이버 검색 API | 완료 |
| Anthropic (Claude) | 완료 |
| Google Places API | 완료 |

---

## 파일 구조 현황

```
backend/
  app/
    core/
      config.py       ✅
      constants.py    ✅
      redis.py        ✅
    services/
      kakao.py        ✅
      naver.py        ✅
      claude.py       ✅
      place_store.py  ✅
  test_run.py         ✅
  scheduler.py        (추후 자동화용, 현재 미사용)
  .env                ✅

scripts/              (미작성)
  collect_kakao.py
  collect_naver.py
  collect_instagram.py
  collect_google.py
  process_with_claude.py
  import_to_redis.py

data/                 (미생성)
  collected_kakao.json
  collected_naver.json
  collected_instagram.json
  collected_google.json
  redis_data.json
```
