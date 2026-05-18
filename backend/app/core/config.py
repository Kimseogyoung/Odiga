from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # DB (M3 이후 필요)
    DATABASE_URL: str = ""

    # Redis
    REDIS_URL: str = "redis://localhost:6379"

    # Anthropic
    ANTHROPIC_API_KEY: str

    # Google Places (M5 이후 필요)
    GOOGLE_PLACES_API_KEY: str = ""

    # Naver
    NAVER_CLIENT_ID: str
    NAVER_CLIENT_SECRET: str

    # Kakao
    KAKAO_API_KEY: str

    # CORS
    ALLOWED_ORIGINS: list[str] = ["http://localhost:5173"]

    model_config = {"env_file": ".env"}


settings = Settings()
