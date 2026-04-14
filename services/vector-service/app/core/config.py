import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    host: str = "0.0.0.0"
    port: int = 8003
    log_level: str = "info"
    max_image_side: int = int(os.getenv("MAX_IMAGE_SIDE", "2048"))
    tile_size: int = int(os.getenv("TILE_SIZE", "512"))

    class Config:
        env_file = ".env"


def load_settings() -> Settings:
    return Settings()
