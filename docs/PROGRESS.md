# Odiga 진행 상황

> 세션 간 이어서 작업하기 위한 현재 상태 기록.

---

## 현재 마일스톤: M2 — 플래너 API

---

## M1 완료 ✅

### 데이터 수집
- [x] `scripts/commands/collect_kakao.py` — 격자 분할 수집 (1622개)
- [x] `scripts/commands/collect_naver.py` — 블로그 리뷰 수집
- [x] `scripts/commands/collect_twitter.py` — Playwright 쿠키 인증 (수동)

### 데이터 파이프라인
- [x] `scripts/commands/merge_places.py` — 카카오+네이버 병합, Claude로 트윗 장소 추출
- [x] `scripts/commands/embed_places.py` — ko-sroberta 벡터 생성 + Redis 저장
- [x] `scripts/commands/embed_search_keywords.py` — 키워드 조합 4943개 벡터 생성 + Redis 저장

### 인프라
- [x] `scripts/pipeline.py` — Click CLI 진입점
- [x] `scripts/jenkins/Jenkinsfile` — Jenkins 파이프라인
- [x] Jenkins Docker 로컬 실행 + GitHub 연동 + 파이프라인 동작 확인

### 백엔드 기반
- [x] `backend/app/core/config.py` — Settings (REDIS_KEY_PREFIX)
- [x] `backend/app/core/redis.py` — PrefixedRedis 래퍼
- [x] `backend/app/services/place_store.py` — Redis CRUD

---

## 아키텍처 결정사항

### Redis 저장 구조
| 키 | 내용 |
|---|---|
| `odiga:places:detail:{pid}` | 장소 메타 |
| `odiga:places:vectors:{region_id}:{category_id}:ids` | 지역×카테고리 장소 ID 목록 |
| `odiga:places:vectors:{region_id}:{category_id}:matrix` | 벡터 flatten 배열 |
| `odiga:query:keyword:{sorted_ids}` | 키워드 조합 쿼리 벡터 |
| `odiga:ai:summary:{pid}` | AI 요약 (M2) |

### M2 검색 흐름
```
keyword_ids → query:keyword:{ids} 로드
region_id + category_id → places:vectors:{r}:{c} 로드 (~100개)
numpy cosine similarity → top 20
Claude Haiku로 하루 코스 생성
```

---

## 다음 할 일 (M2)

### 서비스 모드
- **모드 B (기본/무료)**: 시간대별 장소 선택지 3개 제시 → 사용자가 직접 선택하며 코스 완성
- **모드 A (유료)**: Claude Haiku가 한 번에 최적 코스 자동 생성

### 서비스 모드 확정
- **모드 B (기본/무료)**: 시간대별 장소 선택지 3개 제시 → 사용자가 직접 선택하며 코스 완성
- **모드 A (유료)**: Claude Haiku가 한 번에 최적 코스 자동 생성

### 1. 플래너 API 엔드포인트 (모드 B 기준)

**`POST /api/plan/init`**
- 입력: `region_id`, `keyword_ids`, `start_time`, `end_time`
- 출력: 예상 슬롯 수, 첫 슬롯 시작 시간
- 슬롯 수 계산: `(end_time - start_time) ÷ 평균 90분`

**`POST /api/plan/candidates`** (슬롯마다 반복)
- 입력: `region_id`, `keyword_ids`, `category_id`(사용자 선택), `current_time`, `selected_place_ids`
- 출력: 후보 장소 3개, 다음 슬롯 예상 시간, 남은 시간
- 로직: Redis 벡터 검색 → 이미 선택된 장소 제외 → top 3 반환
- Claude 호출 없음

**`POST /api/plan/finalize`**
- 입력: `selected_place_ids` (순서대로)
- 출력: 이동시간 포함 시간표 JSON
- 이동시간: 네이버 지도 API 연동 전까지 기본값 15분

**`POST /api/plan/auto`** (유료)
- Claude Haiku로 자동 코스 생성

### 슬롯 체류시간 (constants.py 기준)
| 카테고리 | 체류시간 |
|---|---|
| 음식점 | 60분 |
| 카페 | 90분 |
| 쇼핑 | 60분 |
| 바/펍 | 90분 |
| 전시/문화 | 90분 |

이동시간 기본값: 15분 (네이버 지도 API 연동 전)

### 2. FastAPI 라우터 연결
- `backend/app/api/plan.py` 작성
- `backend/app/services/planner.py` — 검색 + 슬롯 계산 로직
- `backend/app/main.py`에 라우터 등록

### 3. 프론트엔드 (M3)
- React 입력 폼 (지역 + 키워드 + 시작/종료 시간)
- 시간대별 카테고리 선택 + 장소 3개 선택 UI (모드 B)
- 코스 시간표 결과 UI

---

## 결정 사항

| 항목 | 결정 |
|------|------|
| Google Places API | 스킵 — 비용 문제 |
| Twitter 수집 | Jenkins 제외, 수동 실행 (쿠키 만료 이슈) |
| 임베딩 모델 | 로컬 ko-sroberta (무료, 768차원) |
| 벡터 DB | Redis (MVP) → Aurora pgvector (고도화) |
| 키워드 검색 | 조합 전체 사전 임베딩 (4943개) |
| 지역×카테고리 | 벡터 DB 분리 저장 (~100개씩 로드) |
| Redis prefix | `odiga:` — PrefixedRedis 래퍼 자동 처리 |
| 파이프라인 트리거 | Jenkins (Docker) + GitHub 연동 |

---

## 파일 구조 현황

```
backend/
  app/
    core/
      config.py       ✅
      constants.py    ✅
      redis.py        ✅ PrefixedRedis 래퍼
    services/
      place_store.py  ✅
      claude.py       ✅ (M2에서 수정 예정)
    api/              ⬜ M2에서 작성
  main.py             ✅ (라우터 미등록)

scripts/
  pipeline.py         ✅ Click CLI
  commands/
    collect_kakao.py  ✅
    collect_naver.py  ✅
    collect_twitter.py ✅
    merge_places.py   ✅
    embed_places.py   ✅
    embed_search_keywords.py ✅
  jenkins/
    Jenkinsfile       ✅
    run_pipeline.sh   ✅
    run_pipeline.ps1  ✅

data/
  collected_kakao.json  ✅
  collected_naver.json  ✅
  collected_twitter.json ✅
  merged_places.json    ✅
  place_vectors.json    ✅
```
