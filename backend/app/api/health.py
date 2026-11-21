"""Liveness and readiness endpoints."""

from __future__ import annotations

import asyncio
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Response, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncEngine

from app.core.config import Settings, get_settings
from app.database.session import get_engine
from app.services import health_service as hs

router = APIRouter(prefix="/api/health", tags=["health"])


class LivenessResponse(BaseModel):
    status: Literal["ok"]


class CheckModel(BaseModel):
    name: str
    status: Literal["ok", "error"]
    required: bool
    latency_ms: float
    detail: str | None = None


class ReadinessResponse(BaseModel):
    status: Literal["ready", "not_ready"]
    environment: str
    checks: list[CheckModel]


@router.get("", response_model=LivenessResponse, summary="Liveness probe")
async def liveness() -> LivenessResponse:
    """Is the process up? Checks no dependencies, so it never flaps with them."""
    return LivenessResponse(status="ok")


@router.get(
    "/ready",
    response_model=ReadinessResponse,
    summary="Readiness probe",
    responses={503: {"model": ReadinessResponse, "description": "A required dependency is down"}},
)
async def readiness(
    response: Response,
    settings: Annotated[Settings, Depends(get_settings)],
    engine: Annotated[AsyncEngine, Depends(get_engine)],
) -> ReadinessResponse:
    """Are the required dependencies (PostgreSQL, Redis) reachable?"""
    timeout = settings.health_check_timeout_seconds
    results = await asyncio.gather(
        hs.check_database(engine, timeout),
        hs.check_redis(settings.redis_url, timeout),
        hs.check_browser_worker(settings.browser_worker_url, timeout),
    )
    ready = hs.is_ready(list(results))
    if not ready:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return ReadinessResponse(
        status="ready" if ready else "not_ready",
        environment=settings.app_env.value,
        checks=[CheckModel(**r.__dict__) for r in results],
    )
