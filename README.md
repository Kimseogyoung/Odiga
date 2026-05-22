# Odiga (어디가)

핫플 하루 일정 플래너.

지역이랑 테마 고르면 AI가 오늘 하루 코스 짜주는 서비스. 혼잡도, 이동시간, 리뷰 요약까지 포함해서 실제로 따라갈 수 있는 일정을 만들어줌.

## 주요 기능

- 지역 + 키워드 선택 → 시간대별 장소 추천
- 마음에 드는 장소 직접 고르면서 코스 완성
- 카카오맵 길찾기 연동
- 코스 공유 링크 생성

## 기술 스택

- **백엔드**: Python + FastAPI
- **프론트**: React + TypeScript + Vite
- **DB**: Redis / Aurora Serverless
- **AI**: Claude Haiku
- **인프라**: AWS EC2 + CloudFront + S3

## 로컬 실행

```bash
# 의존성 설치
python -m venv venv
venv/bin/pip install -r requirements.txt

# 환경변수 설정
cp .env.example .env  # API 키 입력

# 백엔드 실행
uvicorn backend.app.main:app --reload

# 프론트 실행
cd frontend && npm install && npm run dev
```

## 데이터 파이프라인

```bash
# 전체 파이프라인 실행
python scripts/pipeline.py all --storage redis

# 개별 실행
python scripts/pipeline.py collect-kakao
python scripts/pipeline.py embed-places --storage redis
```
