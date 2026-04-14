import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    host: str = "0.0.0.0"
    port: int = 8004
    log_level: str = "info"

    class Config:
        env_file = ".env"


def load_settings() -> Settings:
    return Settings()
