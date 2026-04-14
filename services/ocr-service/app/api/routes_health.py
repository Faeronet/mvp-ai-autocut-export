from fastapi import APIRouter, Response

from app.core.config import load_settings
from app.model_registry.state import REGISTRY

router = APIRouter()


def _degraded() -> bool:
    if not REGISTRY.models:
        return True
    for m in REGISTRY.models.values():
        if m.last_error:
            return True
        if not m.loaded:
            return True
    return False


@router.get("/health")
def health(response: Response) -> dict:
    settings = load_settings()
    models = REGISTRY.to_list()
    degraded = _degraded()
    body = {
        "status": "degraded" if degraded else "ok",
        "service": "ocr-service",
        "models": models,
        "ocr_backend": settings.ocr_backend,
        "table_backend": settings.table_backend,
    }
    if degraded:
        response.status_code = 503
    return body


@router.get("/health/models")
def health_models() -> dict:
    return {"models": REGISTRY.to_list()}
