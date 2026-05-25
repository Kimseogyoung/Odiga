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

## EC2 배포 (Amazon Linux)

**1. Docker 설치**
```bash
sudo yum update -y
sudo yum install -y docker
sudo systemctl enable --now docker
sudo usermod -aG docker $USER && newgrp docker

sudo curl -L "https://github.com/docker/compose/releases/download/v2.5.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
sudo ln -s /usr/local/bin/docker-compose /usr/bin/docker-compose
```

**2. 코드 받기**
```bash
git clone <repo-url> ~/Odiga && cd ~/Odiga
```

**3. 환경변수 파일 생성**

`~/Odiga/.env`:
```
VITE_KAKAO_MAP_KEY=카카오키
```

`~/Odiga/backend/.env`:
```
REDIS_URL=redis://redis:6379
ANTHROPIC_API_KEY=...
NAVER_CLIENT_ID=...
NAVER_CLIENT_SECRET=...
KAKAO_API_KEY=...
ALLOWED_ORIGINS=["http://odiga.sandbox.seogyoung.com"]
```

**4. Redis 실행 (독립)**
```bash
docker run -d --name redis --network host -v redis_data:/data redis:7-alpine redis-server --save 60 1
```

**5. 빌드 & 실행**
```bash
docker-compose up -d --build
```

**6. 상태 확인**
```bash
docker-compose ps
docker-compose logs -f backend
```

> host nginx 세팅은 [SeogyoungNetComInfra](../SeogyoungNetComInfra) 레포의 `setup.sh` 참고.

## 데이터 파이프라인

```bash
# 전체 파이프라인 실행
python scripts/pipeline.py all --storage redis

# 개별 실행
python scripts/pipeline.py collect-kakao
python scripts/pipeline.py embed-places --storage redis
```
