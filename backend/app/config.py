from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql://insiderflow:insiderflow@db:5432/insiderflow"
    redis_url: str = "redis://redis:6379/0"
    sec_user_agent: str = "InsiderFlow admin@insiderflow.com"
    polling_interval_seconds: int = 300
    cors_origins: list[str] = ["http://localhost:3000"]

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
