import logging

from fastapi import FastAPI

from app.api.routes_health import router as health_router
from app.api.routes_ocr import router as ocr_router
from app.api.routes_page_understanding import router as page_router
from app.api.routes_table import router as table_router
from app.core.config import load_settings
from app.core.logging import setup_logging
from app.services.loader import load_services


def create_app() -> FastAPI:
    settings = load_settings()
    setup_logging(settings.log_level)
    logging.getLogger(__name__).info("starting ocr-service")
    ocr_svc, table_svc, page_understanding_svc = load_services(settings)
    app = FastAPI(title="OCR Service", version="0.1.0")
    app.state.ocr_service = ocr_svc
    app.state.table_service = table_svc
    app.state.page_understanding_service = page_understanding_svc
    app.include_router(health_router)
    app.include_router(ocr_router)
    app.include_router(page_router)
    app.include_router(table_router)
    return app


app = create_app()
