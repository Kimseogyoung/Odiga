# Odiga 진행 상황

> 세션 간 이어서 작업하기 위한 현재 상태 기록.

---

## 현재 마일스톤: M1 — 데이터 파이프라인

---

## 완료된 것

### 설계
- [x] `docs/DESIGN.md` — 전체 서비스 설계 문서
- [x] `PROJECT.md` — 마일스톤 정의

### 백엔드 기반
- [x] `backend/app/core/config.py` — Settings 클래스 (REDIS_KEY_PREFIX 포함)
- [x] `backend/app/core/constants.py` — Region / PlaceCategory / Keyword 상수
- [x] `backend/app/core/redis.py` — PrefixedRedis 래퍼 (odiga: 자동 prefix)
- [x] `backend/app/services/place_store.py` — Redis CRUD (detail / 지역×카테고리 벡터 / 키워드 벡터)
- [x] `backend/.env` — API 키 세팅

### 데이터 수집 스크립트
- [x] `scripts/collect_kakao.py` — 격자 분할 수집 (1622개)
- [x] `scripts/collect_naver.py` — 블로그 리뷰 수집
- [x] `scripts/collect_twitter.py` — Playwright 쿠키 인증, 트윗 원문 저장
- [x] `scripts/collect_google.py` — 작성 완료 (비용 문제로 실행 스킵)

### 데이터 파이프라인
- [x] `scripts/merge_places.py` — 카카오+네이버 병합 + Claude로 트윗에서 신규 장소 추출
- [x] `scripts/embed_places.py` — ko-sroberta 벡터 생성, `--storage json|redis` 선택
- [x] `scripts/embed_search_keywords.py` — 키워드 조합 4943개 벡터 생성, `--storage json|redis` 선택
- [x] `scripts/verify_embedding_strategy.py` — 임베딩 전략 검증 스크립트
- [x] `data/merged_places.json` — 병합된 장소 데이터
- [x] `data/place_vectors.json` — 임베딩 벡터 포함 장소 데이터

---

## 아키텍처 결정사항

### Redis 저장 구조
| 키 | 내용 |
|---|---|
| `odiga:places:detail:{pid}` | 장소 메타 (embedding 제외) |
| `odiga:places:vectors:{region_id}:{category_id}:ids` | 해당 조합 장소 ID 목록 |
| `odiga:places:vectors:{region_id}:{category_id}:matrix` | 벡터 flatten 배열 |
| `odiga:query:keyword:{sorted_ids}` | 키워드 조합 쿼리 벡터 |
| `odiga:ai:summary:{pid}` | AI 요약 (M2) |

### 검색 흐름 (M2)
```
keyword_ids → query:keyword:{ids} 로드
region_id + category_id → places:vectors:{r}:{c} 로드 (~100개)
numpy cosine similarity → top 20
Claude Haiku로 하루 코스 생성
```

### 임베딩 모델
- `jhgan/ko-sroberta-multitask` — 한국어 특화, 로컬 실행, 무료
- 벡터 차원: 768

---

## 다음 할 일 (M1 미완료)

### 3. CI/CD 파이프라인
- Jenkins 또는 TeamCity 구성
- SSH로 서버 접속 후 스크립트 직접 순차 실행 (HTTP API 경유 없음)
- 파이프라인 순서:
  ```
  collect_kakao.py
  → collect_naver.py
  → collect_twitter.py
  → merge_places.py
  → embed_places.py --storage redis
  → embed_search_keywords.py --storage redis
  ```

---

## 다음 할 일 (M2)

### 1. 플래너 API 구현
- `POST /api/plan` — region + category + keyword_ids 입력
- 키워드 벡터 + 지역×카테고리 벡터 DB → numpy cosine similarity → 후보 20개
- Claude Haiku로 하루 코스 생성 (이동시간 포함)
- 응답: 시간표 JSON

### 2. 프론트엔드 (M3)
- React 입력 폼 (지역 + 카테고리 + 키워드)
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
| 키워드 검색 | 컴포넌트 평균(43% 겹침) 대신 키워드 조합 전체 사전 임베딩 |
| 지역×카테고리 | 벡터 DB 분리 저장 — 검색 시 ~100개만 로드 |
| 데이터 파이프라인 트리거 | CI/CD에서 SSH 직접 스크립트 실행 (FastAPI 경유 X) |
| Redis prefix | `odiga:` — PrefixedRedis 래퍼로 자동 처리 |

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
      config.py         ✅ REDIS_KEY_PREFIX 포함
      constants.py      ✅
      redis.py          ✅ PrefixedRedis 래퍼
    services/
      place_store.py    ✅ detail / 지역×카테고리 벡터 / 키워드 벡터 CRUD
      claude.py         ✅ (M2에서 코스 생성용으로 수정 예정)
  .env                  ✅

scripts/
  collect_kakao.py           ✅ 실행완료 (1622개)
  collect_naver.py           ✅ 실행완료
  collect_twitter.py         ✅ 실행완료
  collect_google.py          ✅ 작성완료 (스킵)
  merge_places.py            ✅ 실행완료
  embed_places.py            ✅ --storage json|redis
  embed_search_keywords.py   ✅ --storage json|redis
  verify_embedding_strategy.py ✅ 검증용
  process_with_claude.py     ⚠️ 구설계 잔존 — 제거 예정

data/
  collected_kakao.json    ✅
  collected_naver.json    ✅
  collected_twitter.json  ✅
  merged_places.json      ✅
  place_vectors.json      ✅
  search_keywords.json    ⬜ embed_search_keywords.py --storage json 실행 시 생성
```
