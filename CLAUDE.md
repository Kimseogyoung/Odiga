# Odiga — Claude Code 설정

## 프로젝트
서울 핫플 하루 일정 플래너. 지역 + 테마 입력 → AI가 혼잡도/이동시간 포함한 하루 코스 시간표 생성.
개인 사이드 프로젝트. 실서비스 운영 목표. 인스타그램 자동 운영 병행 예정.

## 기술 스택
- 백엔드: Python 3.12 + FastAPI
- 프론트: React 18 + TypeScript + Tailwind CSS + Vite
- DB: Aurora Serverless v2 (MySQL 호환) — SQLAlchemy ORM
- 캐시: Redis (EC2 self-hosted)
- AI: OpenAI GPT-4o mini
- 지도: 카카오맵 SDK
- 장소: Google Places API
- 이동시간: 네이버 지도 API
- 인프라: AWS (EC2 t4g + CloudFront + S3)

## 디렉토리 구조
```
Odiga/
├── backend/          # FastAPI 앱
│   ├── app/
│   │   ├── api/      # 라우터
│   │   ├── services/ # 비즈니스 로직
│   │   ├── models/   # SQLAlchemy 모델
│   │   └── core/     # 설정, DB, Redis 연결
│   └── tests/
├── frontend/         # React 앱
│   └── src/
│       ├── components/
│       ├── pages/
│       └── api/      # API 호출 레이어
└── infra/            # AWS 설정, docker-compose
```

## 핵심 원칙
- **캐싱 우선**: 외부 API(GPT, Google Places) 결과는 Redis에 캐싱. 동일 요청 중복 호출 금지
- **API 키는 환경변수**: 코드에 하드코딩 절대 금지. `.env` 파일 사용
- **GPT 응답**: 항상 한국어 + JSON 형태로 강제
- **에러 시 graceful degradation**: 빈 화면/빈 응답 금지. 항상 fallback 데이터 제공
- **비용 절감**: 불필요한 외부 API 호출 최소화

## 코딩 컨벤션
- Python: snake_case, type hint 필수, Pydantic 모델로 요청/응답 정의
- TypeScript: camelCase, any 타입 사용 금지
- 환경변수: `Settings` 클래스(pydantic-settings)로 관리
- DB 쿼리: Raw SQL 대신 SQLAlchemy ORM 사용

## 금지 사항
- API 키, 시크릿 하드코딩
- `any` 타입 남용 (TypeScript)
- 캐싱 없이 GPT/Places API 직접 호출
- 주석 없는 복잡한 비즈니스 로직
