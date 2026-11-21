"""FastAPI application factory."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import health
from app.core.config import load_settings_or_exit
from app.core.logging import configure_logging, get_logger
from app.core.middleware import REQUEST_ID_HEADER, RequestContextMiddleware
from app.database.session import dispose_engine


def create_app() -> FastAPI:
    settings = load_settings_or_exit()  # exits with a readable error if misconfigured
    configure_logging(settings.log_level, json_logs=True)
    logger = get_logger("app.startup")

    @asynccontextmanager
    async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
        logger.info(
            "service_starting",
            environment=settings.app_env.value,
            llm_provider=settings.llm_provider.value,
            gemini_configured=bool(settings.gemini_api_key),
        )
        yield
        await dispose_engine()
        logger.info("service_stopped")

    app = FastAPI(
        title="Sentinel AI API",
        version="0.1.0",
        description="Autonomous AI software testing and bug detection platform.",
        docs_url="/api/docs",
        openapi_url="/api/openapi.json",
        redoc_url=None,
        lifespan=lifespan,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PATCH", "DELETE"],
        allow_headers=["Authorization", "Content-Type", REQUEST_ID_HEADER],
        expose_headers=[REQUEST_ID_HEADER],
    )
    app.add_middleware(RequestContextMiddleware)  # outermost: wraps everything
    app.include_router(health.router)
    return app


app = create_app()
