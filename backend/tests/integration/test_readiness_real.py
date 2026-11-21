"""Readiness against real PostgreSQL and Redis (no mocks)."""

import os

import httpx
import pytest
from sqlalchemy.ext.asyncio import create_async_engine

from app.core.config import get_settings
from app.database.session import get_engine
from app.main import create_app

pytestmark = pytest.mark.integration


async def test_ready_with_real_database_and_redis(client, pg_admin_dsn, redis_available):
    r = await client.get("/api/health/ready")
    assert r.status_code == 200, r.text
    checks = {c["name"]: c for c in r.json()["checks"]}
    assert checks["database"]["status"] == "ok"
    assert checks["redis"]["status"] == "ok"
    # The worker is not running in this test and is optional, so ready stays true.
    assert checks["browser_worker"]["status"] == "error"


async def test_not_ready_when_database_is_unreachable(redis_available):
    get_settings.cache_clear()
    app = create_app()
    dead = create_async_engine("postgresql+psycopg://x:y@127.0.0.1:1/none")
    app.dependency_overrides[get_engine] = lambda: dead
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as c:
        r = await c.get("/api/health/ready")
    await dead.dispose()
    assert r.status_code == 503
    body = r.json()
    db = next(x for x in body["checks"] if x["name"] == "database")
    assert db["status"] == "error"
    assert "y@" not in (db["detail"] or "")  # no credentials leak
    assert os.environ["DATABASE_URL"] not in r.text
