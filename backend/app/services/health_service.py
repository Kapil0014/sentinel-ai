"""Dependency health checks used by the readiness endpoint.

Each check returns a :class:`CheckResult` and never raises: a failing dependency
is a *result*, not an exception. Error text is sanitised so credentials embedded
in connection strings can never leak through the API.
"""

from __future__ import annotations

import asyncio
import time
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Literal

import httpx
import redis.asyncio as redis_asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

from app.core.logging import URL_PASSWORD, get_logger

logger = get_logger(__name__)

CheckStatus = Literal["ok", "error"]


@dataclass(frozen=True)
class CheckResult:
    name: str
    status: CheckStatus
    required: bool
    latency_ms: float
    detail: str | None = None


def _sanitize(exc: BaseException) -> str:
    message = f"{type(exc).__name__}: {exc}".replace("\n", " ")
    return URL_PASSWORD.sub(r"\1***\3", message)[:200]


async def _timed(
    name: str, required: bool, timeout: float, probe: Callable[[], Awaitable[None]]
) -> CheckResult:
    started = time.perf_counter()
    try:
        await asyncio.wait_for(probe(), timeout=timeout)
    except Exception as exc:  # noqa: BLE001 - a health check must never raise
        logger.warning("health_check_failed", check=name, error=_sanitize(exc))
        return CheckResult(
            name,
            "error",
            required,
            round((time.perf_counter() - started) * 1000, 2),
            _sanitize(exc),
        )
    return CheckResult(name, "ok", required, round((time.perf_counter() - started) * 1000, 2))


async def check_database(engine: AsyncEngine, timeout: float) -> CheckResult:
    async def probe() -> None:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))

    return await _timed("database", True, timeout, probe)


async def check_redis(redis_url: str, timeout: float) -> CheckResult:
    async def probe() -> None:
        client = redis_asyncio.from_url(redis_url, socket_connect_timeout=timeout)
        try:
            await client.ping()
        finally:
            await client.aclose()

    return await _timed("redis", True, timeout, probe)


async def check_browser_worker(base_url: str, timeout: float) -> CheckResult:
    """The worker is informational: the API can serve requests without it."""

    async def probe() -> None:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.get(f"{base_url.rstrip('/')}/health")
            response.raise_for_status()

    return await _timed("browser_worker", False, timeout, probe)


def is_ready(results: list[CheckResult]) -> bool:
    """Ready means every *required* dependency is healthy."""
    return all(r.status == "ok" for r in results if r.required)
