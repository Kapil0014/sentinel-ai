from app.services import health_service as hs


def test_is_ready_ignores_optional_failures():
    results = [
        hs.CheckResult("database", "ok", True, 1),
        hs.CheckResult("redis", "ok", True, 1),
        hs.CheckResult("browser_worker", "error", False, 1, "x"),
    ]
    assert hs.is_ready(results) is True


def test_is_ready_false_when_required_fails():
    results = [
        hs.CheckResult("database", "error", True, 1, "x"),
        hs.CheckResult("redis", "ok", True, 1),
    ]
    assert hs.is_ready(results) is False


async def test_unreachable_redis_returns_error_result_without_leaking_password():
    result = await hs.check_redis("redis://:topsecret@127.0.0.1:1/0", timeout=0.5)
    assert result.status == "error"
    assert "topsecret" not in (result.detail or "")


async def test_unreachable_worker_returns_error_result():
    result = await hs.check_browser_worker("http://127.0.0.1:1", timeout=0.5)
    assert result.status == "error" and result.required is False
