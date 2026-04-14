import logging

from fastapi import FastAPI

from app.api.routes_health import router as health_router
from app.api.routes_vector import router as vector_router
from app.core.config import load_settings
from app.core.logging import setup_logging
from app.services.vector_service import VectorService


def create_app() -> FastAPI:
    settings = load_settings()
    setup_logging(settings.log_level)
    logging.getLogger(__name__).info("starting vector-service")
    app = FastAPI(title="Vector Service", version="0.1.0")
    app.state.vector_service = VectorService(settings)
    app.include_router(health_router)
    app.include_router(vector_router)
    return app


app = create_app()
