from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI

from .config import Settings
from .routes import router
from .service import DdddOcrService


def create_app(
        settings: Settings | None = None,
        service: DdddOcrService | None = None,
) -> FastAPI:
    service_settings = settings or Settings.from_env()
    ocr_service = service or DdddOcrService(service_settings)

    @asynccontextmanager
    async def lifespan(_: FastAPI):
        ocr_service.initialize()
        try:
            yield
        finally:
            ocr_service.close()

    application = FastAPI(
        title="DdddOcr API",
        description="HTTP API service for DdddOcr",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )
    application.state.settings = service_settings
    application.state.ocr_service = ocr_service
    application.include_router(router)
    return application


app = create_app()
