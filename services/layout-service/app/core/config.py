import os

from pydantic_settings import BaseSettings, SettingsConfigDict


def _b(k: str, d: bool = False) -> bool:
    v = os.getenv(k, "").strip().lower()
    if v == "":
        return d
    return v in ("1", "true", "yes")


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", protected_namespaces=("settings_",))

    host: str = "0.0.0.0"
    port: int = 8001
    log_level: str = "info"
    max_image_side: int = int(os.getenv("MAX_IMAGE_SIDE", "2048"))
    tile_size: int = int(os.getenv("TILE_SIZE", "512"))

    model_cache_dir: str = os.getenv("MODEL_CACHE_DIR", "/models_cache")
    model_startup_strict: bool = _b("MODEL_STARTUP_STRICT", True)
    layout_backend: str = os.getenv("LAYOUT_BACKEND", "yolov8n")
    layout_use_gpu: bool = _b("LAYOUT_USE_GPU", True)
    layout_model_name: str = os.getenv("LAYOUT_MODEL_NAME", "yolov8n_layout")
    layout_model_weights: str = os.getenv(
        "LAYOUT_MODEL_WEIGHTS",
        os.path.join(os.getenv("MODEL_CACHE_DIR", "/models_cache"), "layout", "yolov8n_layout.pt"),
    )


def load_settings() -> Settings:
    return Settings()
