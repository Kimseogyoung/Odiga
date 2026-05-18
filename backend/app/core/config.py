from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # DB
    DATABASE_URL: str

    # Redis
    REDIS_URL: str = "redis://localhost:6379"

    # OpenAI
    OPENAI_API_KEY: str

    # Google Places
    GOOGLE_PLACES_API_KEY: str

    # Naver Maps
    NAVER_CLIENT_ID: str
    NAVER_CLIENT_SECRET: str

    # Kakao
    KAKAO_API_KEY: str

    # CORS
    ALLOWED_ORIGINS: list[str] = ["http://localhost:5173"]

    model_config = {"env_file": ".env"}


settings = Settings()
