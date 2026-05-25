from pathlib import Path
from pydantic_settings import BaseSettings

_ENV_PATH = Path(__file__).parent.parent.parent / ".env"


class Settings(BaseSettings):
    # Redis
    REDIS_URL: str = "redis://localhost:6379"
    REDIS_KEY_PREFIX: str = "odiga"

    # Anthropic
    ANTHROPIC_API_KEY: str

    # Naver
    NAVER_CLIENT_ID: str
    NAVER_CLIENT_SECRET: str

    # Kakao
    KAKAO_API_KEY: str

    # Twitter (쿠키 기반 — 수동 수집용)
    TWITTER_AUTH_TOKEN: str = ""
    TWITTER_CT0: str = ""

    # Redis TTL
    TTL_PLACE_DETAIL_SECONDS: int = 60 * 60 * 24 * 30   # 30일
    TTL_PLACE_VECTOR_SECONDS: int = 60 * 60 * 24 * 30   # 30일
    TTL_COURSE_SECONDS:       int = 60 * 60 * 24 * 7    # 7일
    # TTL_SUMMARY 없음 — 장소 요약은 파이프라인 실행 시에만 변경되므로 만료 없이 유지

    # Session
    SESSION_TTL_SECONDS: int = 1800  # 30분

    # CORS
    ALLOWED_ORIGINS: list[str] = ["http://localhost:5173"]

    model_config = {"env_file": str(_ENV_PATH), "extra": "ignore"}


settings = Settings()
