# Odiga 진행 상황

> 세션 간 이어서 작업하기 위한 현재 상태 기록.

---

## 현재 마일스톤: M4 — 배포 / 고도화

---

## M4 진행 중 🔧

### 배포 인프라
- [x] `backend/Dockerfile` — FastAPI 서버 컨테이너 (포트 11000)
- [x] `frontend/Dockerfile` — React 빌드 + nginx 서빙 (포트 12000)
- [x] `docker-compose.yml` — backend/frontend, host 네트워크 모드
- [x] `scripts/Dockerfile` — 파이프라인 전용 이미지 (sentence-transformers 포함)
- [x] `scripts/jenkins/Jenkinsfile` — REDIS_URL 파라미터로 로컬/원격 대상 선택
- [x] Redis 독립 컨테이너 분리 (`docker run` 직접 실행, 볼륨 별도 관리)
- [x] EC2 (Amazon Linux, t4g) 배포 완료 — `http://odiga.sandbox.seogyoung.com`
- [x] host nginx (SeogyoungNetComInfra) — 서브도메인 라우팅 (80포트)
  - `odiga.sandbox.seogyoung.com` → 12000 (frontend)
  - `odiga-server.sandbox.seogyoung.com` → 11000 (backend)
- [x] Jenkins 원격 Redis 배포 옵션 추가 (REDIS_URL 파라미터)

### 기능 고도화
- [x] 서브카테고리 int ID 도입 (101=한식, 201=베이커리 등)
- [x] 서브카테고리 pre-indexing — Redis에 ID 목록 저장, 필터링 성능 개선
- [x] 장소 사진 수집 — `collect-kakao` 단계에서 og:image 스크래핑
- [x] PlaceCard / CoursePage 타임라인에 사진 썸네일 노출

### 남은 작업
- [ ] HTTPS 전환 (Let's Encrypt + certbot)
- [ ] `frontend/.env` EC2에 생성 (VITE_KAKAO_MAP_KEY)
- [ ] Jenkins `EC2_REDIS_URL` credential 등록 후 원격 파이프라인 1회 실행

---

## M3 완료 ✅

### 프론트엔드 (React + TypeScript + Tailwind CSS v4)
- [x] `frontend/src/types.ts` — 백엔드 스키마 대응 TypeScript 타입 전체 정의
- [x] `frontend/src/api/courses.ts` — API 호출 레이어 (constants, session, candidates, pick, course)
- [x] `frontend/src/pages/HomePage.tsx` — 지역/키워드/시간 입력 폼
- [x] `frontend/src/pages/PlannerPage.tsx` — 슬롯별 카테고리 선택 + 장소 3개 카드 선택 UI
- [x] `frontend/src/pages/CoursePage.tsx` — 시간표 결과 + 공유 링크 복사
- [x] `frontend/src/components/PlaceCard.tsx` — 장소 카드 컴포넌트
- [x] `frontend/src/App.tsx` — React Router 라우팅 (/, /planner/:sessionId, /course/:shareToken)

### 아키텍처 결정사항 (M3)
| 항목 | 결정 |
|---|---|
| 라우팅 | React Router v7 (`BrowserRouter`) |
| 상태 전달 | `useNavigate` state로 session_id + slot 전달 |
| 카테고리 기본값 | 하드코딩 fallback + `/api/constants`로 덮어쓰기 |
| 사진 | `photo_url` 있으면 노출, 없으면 카테고리별 이모지 |
| 공유 | `navigator.clipboard.writeText(window.location.href)` |

---

## M2 완료 ✅

### 플래너 API
- [x] `backend/app/api/schemas.py` — 요청/응답 Pydantic 모델
- [x] `backend/app/services/planner.py` — 벡터 검색, 세션 CRUD, 슬롯 계산, 코스 완성
- [x] `backend/app/api/courses.py` — FastAPI 라우터 4개 엔드포인트
- [x] `backend/app/core/config.py` — .env 경로 수정, SESSION_TTL_SECONDS 추가
- [x] `backend/app/main.py` — 라우터 등록
- [x] `run.py` — 어느 경로에서든 서버 실행 가능한 진입점
- [x] `test_api.py` — 전체 플로우 통합 테스트 스크립트

### 아키텍처 결정사항 (M2)
| 항목 | 결정 |
|---|---|
| API 방식 | 세션 기반 (Redis TTL 30분) |
| 후보 선정 | 유사도 상위 15개 풀에서 랜덤 3개 |
| 카테고리 선택 | 사용자가 직접 선택 (자동 결정 아님) |
| 이동시간 | Haversine 공식 (네이버 API 연동 전) |
| 벡터 캐시 | 서버 인메모리 TTL 1일 (JSON 파싱 비용 제거) |
| 코스 저장 | Redis TTL 7일, share_token 8자리 |

---

## M1 완료 ✅

### 데이터 수집
- [x] `scripts/commands/collect_kakao.py` — 격자 분할 수집 (1622개) + og:image 스크래핑
- [x] `scripts/commands/collect_naver.py` — 블로그 리뷰 수집
- [x] `scripts/commands/collect_twitter.py` — Playwright 쿠키 인증 (수동)

### 데이터 파이프라인
- [x] `scripts/commands/merge_places.py` — 카카오+네이버 병합, Claude로 트윗 장소 추출
- [x] `scripts/commands/embed_places.py` — ko-sroberta 벡터 생성 + Redis 저장 + 서브카테고리 pre-indexing
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

### 배포 구조
| 컴포넌트 | 방식 | 포트 |
|---|---|---|
| Redis | 독립 docker run (볼륨: redis_data) | 6379 |
| Backend | docker-compose, host 네트워크 | 11000 |
| Frontend | docker-compose, nginx 컨테이너 | 12000 |
| host nginx | 직접 설치 (SeogyoungNetComInfra) | 80 |

### Redis 저장 구조
| 키 | 내용 |
|---|---|
| `odiga:places:detail:{pid}` | 장소 메타 (photo_url 포함) |
| `odiga:places:vectors:{region_id}:{category_id}:ids` | 지역×카테고리 장소 ID 목록 |
| `odiga:places:vectors:{region_id}:{category_id}:matrix` | 벡터 flatten 배열 |
| `odiga:places:vectors:{region_id}:{category_id}:{sub_id}:ids` | 서브카테고리별 ID 목록 |
| `odiga:query:keyword:{sorted_ids}` | 키워드 조합 쿼리 벡터 |

### 결정 사항
| 항목 | 결정 |
|------|------|
| Google Places API | 스킵 — 비용 문제 |
| Twitter 수집 | Jenkins 제외, 수동 실행 (쿠키 만료 이슈) |
| 임베딩 모델 | 로컬 ko-sroberta (무료, 768차원) |
| 벡터 DB | Redis (MVP) → Aurora pgvector (고도화) |
| 키워드 검색 | 조합 전체 사전 임베딩 (4943개) |
| Redis prefix | `odiga:` — PrefixedRedis 래퍼 자동 처리 |
| 파이프라인 트리거 | Jenkins (Docker) + GitHub 연동, REDIS_URL 파라미터로 대상 선택 |
| 사진 수집 | collect-kakao 단계에서 og:image 스크래핑 |
| 서브카테고리 | int ID (category_id * 100 + seq), Redis pre-indexing |
