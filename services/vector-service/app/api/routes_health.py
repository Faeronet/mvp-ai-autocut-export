import os

from fastapi import APIRouter

from app.core.model_env import model_status_rows

router = APIRouter()


@router.get("/health")
def health() -> dict:
    return {
        "status": "ok",
        "service": "vector-service",
        "geometry_backend": "opencv",
        "models": model_status_rows(),
        "enable_sheet_classifier_nn": os.getenv("ENABLE_MODEL_SHEET_CLASSIFIER", "false").lower() == "true",
        "enable_symbol_yolo": os.getenv("SYMBOL_MODEL_AUTO_DOWNLOAD", "false").lower() == "true",
    }


@router.get("/health/models")
def health_models() -> dict:
    return {"models": model_status_rows()}
