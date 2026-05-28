from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://retailiq:retailiq@localhost:5432/retailiq"
    SECRET_KEY: str = "changeme"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440
    REDIS_URL: str = "redis://localhost:6379"
    KAFKA_BOOTSTRAP_SERVERS: str = "localhost:9092"
    FORECAST_HORIZON_DAYS: int = 90
    REORDER_SERVICE_LEVEL: float = 0.95

    class Config:
        env_file = ".env"

settings = Settings()
