import json
import re

import pytest

from app.services import health_service as hs


def _ok(name, required=True):
    async def check(*_args, **_kwargs):
        return hs.CheckResult(name, "ok", required, 1.0)

    return check


def _down(name, required=True):
    async def check(*_args, **_kwargs):
        return hs.CheckResult(name, "error", required, 1.0, "ConnectionError: refused")

    return check


@pytest.fixture
def patch_checks(monkeypatch):
    def apply(db, redis, worker):
        monkeypatch.setattr(hs, "check_database", db)
        monkeypatch.setattr(hs, "check_redis", redis)
        monkeypatch.setattr(hs, "check_browser_worker", worker)

    return apply


async def test_liveness_ok_without_dependencies(client):
    r = await client.get("/api/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


async def test_readiness_ready_when_required_deps_up(client, patch_checks):
    patch_checks(_ok("database"), _ok("redis"), _ok("browser_worker", False))
    r = await client.get("/api/health/ready")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ready"
    assert {c["name"] for c in body["checks"]} == {"database", "redis", "browser_worker"}


@pytest.mark.parametrize("failing", ["database", "redis"])
async def test_readiness_503_when_required_dep_down(client, patch_checks, failing):
    patch_checks(
        _down("database") if failing == "database" else _ok("database"),
        _down("redis") if failing == "redis" else _ok("redis"),
        _ok("browser_worker", False),
    )
    r = await client.get("/api/health/ready")
    assert r.status_code == 503
    assert r.json()["status"] == "not_ready"


async def test_readiness_still_ready_when_only_worker_down(client, patch_checks):
    patch_checks(_ok("database"), _ok("redis"), _down("browser_worker", False))
    r = await client.get("/api/health/ready")
    assert r.status_code == 200
    worker = next(c for c in r.json()["checks"] if c["name"] == "browser_worker")
    assert worker["status"] == "error"


async def test_response_carries_generated_request_id(client):
    r = await client.get("/api/health")
    assert re.fullmatch(r"[0-9a-f]{32}", r.headers["x-request-id"])


async def test_valid_incoming_request_id_is_echoed(client):
    r = await client.get("/api/health", headers={"X-Request-ID": "trace-12345678"})
    assert r.headers["x-request-id"] == "trace-12345678"


async def test_malicious_request_id_is_replaced(client):
    r = await client.get("/api/health", headers={"X-Request-ID": "bad id\r\nX-Evil: 1"})
    assert r.headers["x-request-id"] != "bad id"
    assert re.fullmatch(r"[0-9a-f]{32}", r.headers["x-request-id"])


async def test_access_log_line_contains_request_id(capsys, client):
    # capsys must be requested first: the app binds its log handler to sys.stdout at creation.
    await client.get("/api/health", headers={"X-Request-ID": "trace-abcdef12"})
    records = [
        json.loads(line) for line in capsys.readouterr().out.splitlines() if line.startswith("{")
    ]
    completed = [r for r in records if r.get("event") == "request_completed"]
    assert completed and completed[-1]["request_id"] == "trace-abcdef12"
    assert completed[-1]["status_code"] == 200


async def test_openapi_documents_health_routes(client):
    r = await client.get("/api/openapi.json")
    assert r.status_code == 200
    assert "/api/health/ready" in r.json()["paths"]
