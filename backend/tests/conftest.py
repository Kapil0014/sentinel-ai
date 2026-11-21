"""Shared fixtures.

Environment defaults are set *before* importing the app, because the app fails
fast on invalid configuration at import time (by design).
"""

from __future__ import annotations

import os

os.environ.setdefault("APP_ENV", "test")
# No credentials in source. Integration tests need DATABASE_URL from the environment (CI sets it).
os.environ.setdefault("DATABASE_URL", "postgresql+psycopg://sentinel@127.0.0.1:5432/sentinel")
os.environ.setdefault("REDIS_URL", "redis://127.0.0.1:6379/0")
os.environ.setdefault("JWT_SECRET", "test-only-secret-not-for-real-use-0123456789abcdef")
os.environ.setdefault("BROWSER_WORKER_URL", "http://127.0.0.1:59999")  # nothing listens here
os.environ["LLM_PROVIDER"] = "mock"  # automated tests must never call a paid API
os.environ.pop("GEMINI_API_KEY", None)

import httpx  # noqa: E402
import psycopg  # noqa: E402
import pytest  # noqa: E402
import redis  # noqa: E402
from sqlalchemy.engine import make_url  # noqa: E402

from app.core.config import get_settings  # noqa: E402
from app.main import create_app  # noqa: E402

REQUIRE_INTEGRATION = os.environ.get("REQUIRE_INTEGRATION") == "1"


@pytest.fixture
def app():
    get_settings.cache_clear()
    return create_app()


@pytest.fixture
async def client(app):
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


def _integration_skip_or_fail(reason: str) -> None:
    # In CI (REQUIRE_INTEGRATION=1) an unreachable service is a failure, not a skip.
    if REQUIRE_INTEGRATION:
        pytest.fail(reason)
    pytest.skip(reason)


@pytest.fixture(scope="session")
def pg_admin_dsn() -> str:
    """libpq DSN for the configured server (used to create scratch databases)."""
    url = make_url(os.environ["DATABASE_URL"])
    dsn = f"host={url.host} port={url.port or 5432} user={url.username} dbname={url.database}"
    if url.password:
        dsn += f" password={url.password}"
    try:
        with psycopg.connect(dsn, connect_timeout=3):
            pass
    except psycopg.OperationalError as exc:
        _integration_skip_or_fail(f"PostgreSQL not reachable: {exc}")
    return dsn


@pytest.fixture(scope="session")
def redis_available() -> None:
    try:
        redis.Redis.from_url(os.environ["REDIS_URL"], socket_connect_timeout=2).ping()
    except redis.RedisError as exc:
        _integration_skip_or_fail(f"Redis not reachable: {exc}")
