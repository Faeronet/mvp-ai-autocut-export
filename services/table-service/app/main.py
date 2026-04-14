import logging

from fastapi import FastAPI

from app.api.routes_health import router as health_router
from app.api.routes_table import router as table_router
from app.services.table_service import TableService


def create_app() -> FastAPI:
    logging.basicConfig(level=logging.INFO)
    app = FastAPI(title="Table Service", version="0.1.0")
    app.state.table_service = TableService()
    app.include_router(health_router)
    app.include_router(table_router)
    return app


app = create_app()
