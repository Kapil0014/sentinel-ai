import json
import logging

import structlog

from app.core.logging import configure_logging, redact_processor


def test_sensitive_keys_are_masked():
    out = redact_processor(
        None, "info", {"event": "x", "api_key": "AIza123", "password": "p", "ok": "v"}
    )
    assert out["api_key"] == "***"
    assert out["password"] == "***"
    assert out["ok"] == "v"


def test_url_passwords_are_masked_in_values_and_nested_dicts():
    out = redact_processor(
        None,
        "info",
        {
            "event": "x",
            "target": "postgresql://u:hunter2@h/db",
            "ctx": {"authorization": "Bearer t"},
        },
    )
    assert "hunter2" not in out["target"]
    assert out["ctx"]["authorization"] == "***"


def test_log_lines_are_json_and_carry_bound_context(capsys):
    configure_logging("INFO", json_logs=True)
    structlog.contextvars.clear_contextvars()
    structlog.contextvars.bind_contextvars(request_id="abc12345")
    logging.getLogger("t").info("hello", extra={})
    structlog.get_logger("t2").info("structured", token="should-not-appear")
    lines = [json.loads(line) for line in capsys.readouterr().out.strip().splitlines()]
    structured = next(line for line in lines if line["event"] == "structured")
    assert structured["request_id"] == "abc12345"
    assert structured["token"] == "***"
    assert structured["level"] == "info"
    structlog.contextvars.clear_contextvars()
