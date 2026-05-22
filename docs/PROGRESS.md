# Odiga 진행 상황

> 세션 간 이어서 작업하기 위한 현재 상태 기록.

---

## 현재 마일스톤: M2 — 플래너 API

---

## 완료된 것

### 설계
- [x] `docs/DESIGN.md` — 전체 서비스 설계 문서
- [x] `PROJECT.md` — 마일스톤 정의

### 백엔드 기반
- [x] `backend/app/core/config.py` — Settings 클래스
- [x] `backend/app/core/constants.py` — Region / PlaceCategory / Keyword 상수
- [x] `backend/app/core/redis.py` — Redis 연결
- [x] `backend/.env` — API 키 세팅

### 데이터 수집 스크립트
- [x] `scripts/collect_kakao.py` — 격자 분할 수집 (1622개)
- [x] `scripts/collect_naver.py` — 블로그 리뷰 수집
- [x] `scripts/collect_twitter.py` — Playwright 쿠키 인증, 트윗 원문 저장
- [x] `scripts/collect_google.py` — 작성 완료 (비용 문제로 실행 스킵)

### 데이터 파이프라인
- [x] `scripts/merge_places.py` — 카카오+네이버 병합 + Claude로 트윗에서 신규 장소 추출 + 카카오 검색
- [x] `scripts/generate_embeddings.py` — 로컬 한국어 임베딩 모델(ko-sroberta)로 벡터 생성
- [x] `scripts/test_search.py` — 임베딩 검색 테스트 (동작 확인 완료)
- [x] `data/merged_places.json` — 병합된 장소 데이터
- [x] `data/place_vectors.json` — 임베딩 벡터 포함 장소 데이터

---

## 아키텍처 결정사항

### 임베딩 기반 검색으로 전환
- **기존 설계**: Claude로 장소마다 요약 생성 → Redis 저장
- **변경**: 임베딩 벡터 기반 유사도 검색 → Claude는 최종 코스 구성에만 사용
- **이유**: 키워드 매칭 한계 극복, 지역 추가 시 비용 선형 증가 방지, Claude 활용 목적 명확화

### Claude 역할 재정의
| 역할 | 내용 |
|------|------|
| 트윗 장소명 추출 | 비정형 텍스트에서 상호명 파싱 (지역당 1회 호출) |
| 코스 생성 (M2) | 임베딩 검색 결과 20개 → 하루 일정 구성 |

### 임베딩 모델
- `jhgan/ko-sroberta-multitask` — 한국어 특화, 로컬 실행, 무료
- 벡터 차원: 768

---

## 다음 할 일 (M1 미완료)

### 1. Redis 저장 구조 구현
- 설계된 테이블 구조로 Redis에 장소 데이터 저장 (메타 + 임베딩 벡터 포함)
- `scripts/import_to_redis.py` 재작성 — place_vectors.json → Redis (구설계 대체)
- 저장 옵션: `storage: "redis" | "json"` request body 파라미터로 선택 가능하게

### 2. 쿼리 벡터 사전 생성 및 검색 캐싱
- `scripts/generate_query_vectors.py` — 지역×테마 조합(~25개) 쿼리 벡터 사전 생성
- Redis에 `query_vector:{region}:{theme}` 키로 저장
- 검색 결과(top 20)도 `search_result:{region}:{theme}` 키로 캐싱
- 런타임에 ko-sroberta 모델 실행 불필요

### 3. 데이터 수집 파이프라인 FastAPI 연동
- 각 수집 스크립트를 FastAPI POST 엔드포인트로 래핑
- long-running 작업은 `BackgroundTasks`로 처리
- 엔드포인트: `/admin/collect/kakao`, `/admin/collect/naver`, `/admin/collect/twitter`, `/admin/pipeline/merge`, `/admin/pipeline/embed`

### 4. CI/CD 트리거 파이프라인
- TeamCity 또는 Jenkins로 파이프라인 구성
- 트리거 → 데이터 수집 → 병합/임베딩 → Redis 저장 자동화

---

## 다음 할 일 (M2)

### 1. 플래너 API 구현
- `POST /api/plan` — region + theme 입력
- Redis에서 쿼리 벡터 로드 → numpy 코사인 유사도 → 후보 20개 추출
- Claude Haiku로 하루 코스 생성 (이동시간 포함)
- 응답: 시간표 JSON

### 2. 프론트엔드 (M3)
- React 입력 폼 (지역 + 테마)
- 코스 시간표 UI

---

## 결정 사항

| 항목 | 결정 |
|------|------|
| Google Places API | 스킵 — 비용 문제 |
| Instagram | 트위터로 교체 |
| 트위터 인증 | 쿠키 방식 |
| 사전처리 방식 | Claude 요약 → 임베딩 벡터로 전환 |
| 임베딩 모델 | OpenAI 대신 로컬 ko-sroberta (무료) |
| 벡터 DB | MVP 단계는 Redis — Aurora pgvector는 고도화 단계에서 |
| 런타임 모델 실행 | 지역×테마 조합 쿼리 벡터 사전 생성 → Redis 캐싱으로 모델 실행 불필요 |
| 데이터 파이프라인 트리거 | CI/CD(TeamCity or Jenkins) 연동 예정 |

---

## API 키 현황

| 서비스 | 상태 |
|--------|------|
| 카카오 REST API | 완료 |
| 네이버 검색 API | 완료 |
| Anthropic (Claude) | 완료 |
| Google Places API | 완료 (미사용) |
| Twitter 쿠키 | 완료 |

---

## 파일 구조 현황

```
backend/
  app/
    core/
      config.py         ✅
      constants.py      ✅
      redis.py          ✅
    services/
      kakao.py          ✅
      naver.py          ✅
      claude.py         ✅ (M2에서 코스 생성용으로 수정 예정)
      place_store.py    ✅
  .env                  ✅

scripts/
  collect_kakao.py      ✅ 실행완료 (1622개)
  collect_naver.py      ✅ 실행완료
  collect_twitter.py    ✅ 실행완료
  collect_google.py     ✅ 작성완료 (스킵)
  merge_places.py       ✅ 실행완료
  embed_places.py        ✅ 실행완료 (구 generate_embeddings.py — --save-to-redis 플래그 추가)
  test_search.py         ✅ 동작확인
  process_with_claude.py ⚠️ 구설계 잔존 — 제거 예정

data/
  collected_kakao.json    ✅
  collected_naver.json    ✅
  collected_twitter.json  ✅
  merged_places.json      ✅
  place_vectors.json      ✅
  redis_data.json         ⬜ 미생성 (불필요, pgvector로 대체)
```
