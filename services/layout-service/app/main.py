import logging

from fastapi import FastAPI

from app.api.routes_health import router as health_router
from app.api.routes_layout import router as layout_router
from app.core.config import load_settings
from app.core.logging import setup_logging
from app.services.loader import load_layout_service


def create_app() -> FastAPI:
    settings = load_settings()
    setup_logging(settings.log_level)
    logging.getLogger(__name__).info("starting layout-service")
    layout_svc = load_layout_service(settings)
    app = FastAPI(title="Layout Service", version="0.1.0")
    app.state.layout_service = layout_svc
    app.include_router(health_router)
    app.include_router(layout_router)
    return app


app = create_app()
