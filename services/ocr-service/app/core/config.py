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
    port: int = 8002
    log_level: str = "info"

    model_cache_dir: str = os.getenv("MODEL_CACHE_DIR", "/models_cache")
    model_auto_download: bool = _b("MODEL_AUTO_DOWNLOAD", True)
    model_startup_strict: bool = _b("MODEL_STARTUP_STRICT", True)

    ocr_backend: str = os.getenv("OCR_BACKEND", "paddleocr")
    ocr_use_gpu: bool = _b("OCR_USE_GPU", True)
    ocr_lang: str = os.getenv("OCR_LANG", "ru")
    ocr_det_model_name: str = os.getenv("OCR_DET_MODEL_NAME", "ppocrv4_det")
    ocr_rec_model_name: str = os.getenv("OCR_REC_MODEL_NAME", "ppocrv4_rec")
    ocr_cls_model_name: str = os.getenv("OCR_CLS_MODEL_NAME", "ppocrv4_cls")

    table_backend: str = os.getenv("TABLE_BACKEND", "paddle_table")
    table_use_gpu: bool = _b("TABLE_USE_GPU", True)
    table_model_name: str = os.getenv("TABLE_MODEL_NAME", "ppstructure_slanet")
    vlm_backend: str = os.getenv("VLM_BACKEND", "qwen2_5_vl_3b")
    vlm_enabled: bool = _b("VLM_ENABLED", True)
    vlm_device: str = os.getenv("VLM_DEVICE", "cuda")
    vlm_use_fp16: bool = _b("VLM_USE_FP16", True)
    vlm_max_batch: int = int(os.getenv("VLM_MAX_BATCH", "1"))
    vlm_model_id: str = os.getenv("VLM_MODEL_ID", "Qwen/Qwen2.5-VL-3B-Instruct")
    vlm_max_new_tokens: int = int(os.getenv("VLM_MAX_NEW_TOKENS", "512"))
    vlm_quantization: str = os.getenv("VLM_QUANTIZATION", "4bit")
    vlm_use_flash_attention: bool = _b("VLM_USE_FLASH_ATTENTION", False)

    sheet_classifier_backend: str = os.getenv("SHEET_CLASSIFIER_BACKEND", "rules")
    enable_model_sheet_classifier: bool = _b("ENABLE_MODEL_SHEET_CLASSIFIER", False)

    symbol_detection_backend: str = os.getenv("SYMBOL_DETECTION_BACKEND", "heuristic")
    enable_symbol_detection: bool = _b("ENABLE_SYMBOL_DETECTION", True)
    symbol_model_auto_download: bool = _b("SYMBOL_MODEL_AUTO_DOWNLOAD", False)

    review_backend: str = os.getenv("REVIEW_BACKEND", "rules")
    enable_low_confidence_review: bool = _b("ENABLE_LOW_CONFIDENCE_REVIEW", True)
    enable_llm_review_fallback: bool = _b("ENABLE_LLM_REVIEW_FALLBACK", False)

    fp16_enabled: bool = _b("FP16_ENABLED", True)


def load_settings() -> Settings:
    s = Settings()
    # PaddleOCR resolves ~/.paddleocr; in Docker, put that on the shared MODEL_CACHE_DIR volume.
    os.environ.setdefault("HOME", s.model_cache_dir.rstrip("/"))
    return s
