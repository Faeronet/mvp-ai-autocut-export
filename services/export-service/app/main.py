import logging

from fastapi import FastAPI

from app.api.routes_export import router as export_router
from app.api.routes_health import router as health_router
from app.core.config import load_settings
from app.services.export_service import ExportService


def create_app() -> FastAPI:
    settings = load_settings()
    logging.basicConfig(level=logging.INFO)
    app = FastAPI(title="Export Service", version="0.1.0")
    app.state.export_service = ExportService()
    app.include_router(health_router)
    app.include_router(export_router)
    return app


app = create_app()
