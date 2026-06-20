from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "BondView API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    DATABASE_URL: str = "postgresql+asyncpg://bondview:bondview123@db:5432/bondview"
    REDIS_URL: str = "redis://redis:6379/0"

    SECRET_KEY: str = "please-change-this-in-production-for-security"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440

    CORS_ORIGINS: list[str] = ["http://localhost:3000", "http://frontend:80"]

    model_config = {"env_prefix": "BONDVIEW_"}


settings = Settings()
