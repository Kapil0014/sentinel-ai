import pytest
from pydantic import ValidationError

from app.core.config import AppEnv, Settings, redact_url

VALID = {
    "database_url": "postgresql+psycopg://u:p@db:5432/x",
    "redis_url": "redis://redis:6379/0",
    "jwt_secret": "x" * 40,
}


def make(**overrides) -> Settings:
    return Settings(_env_file=None, **{**VALID, **overrides})


def test_valid_settings_load_with_defaults(monkeypatch):
    monkeypatch.delenv("APP_ENV", raising=False)  # conftest sets APP_ENV=test
    monkeypatch.delenv("CORS_ORIGINS", raising=False)
    s = make()
    assert s.app_env is AppEnv.DEVELOPMENT
    assert s.llm_provider.value == "mock"
    assert s.cors_origins == ["http://localhost:5173"]


def test_missing_required_values_name_the_fields(monkeypatch):
    for var in ("DATABASE_URL", "REDIS_URL", "JWT_SECRET"):
        monkeypatch.delenv(var, raising=False)
    with pytest.raises(ValidationError) as exc:
        Settings(_env_file=None)
    missing = {e["loc"][0] for e in exc.value.errors()}
    assert {"database_url", "redis_url", "jwt_secret"} <= missing


def test_short_jwt_secret_rejected():
    with pytest.raises(ValidationError, match="at least 32"):
        make(jwt_secret="short")


def test_database_url_must_use_psycopg_driver():
    with pytest.raises(ValidationError, match="psycopg"):
        make(database_url="postgresql://u:p@db/x")


def test_redis_url_scheme_checked():
    with pytest.raises(ValidationError, match="redis://"):
        make(redis_url="http://redis")


def test_gemini_requires_api_key():
    with pytest.raises(ValidationError, match="GEMINI_API_KEY"):
        make(llm_provider="gemini")


def test_gemini_with_key_is_accepted():
    assert make(llm_provider="gemini", gemini_api_key="k").gemini_api_key == "k"


def test_production_rejects_placeholder_secret():
    with pytest.raises(ValidationError, match="placeholder"):
        make(app_env="production", jwt_secret="replace-with-a-real-secret-value-0123456789")


def test_production_rejects_private_host_exceptions():
    with pytest.raises(ValidationError, match="ALLOWED_PRIVATE_HOSTS"):
        make(app_env="production", allowed_private_hosts="demo-site")


def test_development_allows_private_host_exceptions():
    assert make(allowed_private_hosts="demo-site, other").allowed_private_hosts == [
        "demo-site",
        "other",
    ]


def test_cors_wildcard_rejected():
    with pytest.raises(ValidationError, match="explicit origins"):
        make(cors_origins="*")


def test_cors_csv_parsed():
    s = make(cors_origins="http://a.test, http://b.test")
    assert s.cors_origins == ["http://a.test", "http://b.test"]


def test_invalid_log_level_rejected():
    with pytest.raises(ValidationError, match="LOG_LEVEL"):
        make(log_level="LOUD")


def test_redact_url_hides_password_only():
    assert redact_url("postgresql+psycopg://user:secret@host:5432/db") == (
        "postgresql+psycopg://user:***@host:5432/db"
    )
    assert redact_url("redis://redis:6379/0") == "redis://redis:6379/0"


def test_field_errors_are_formatted_per_variable(monkeypatch):
    from app.core.config import format_validation_error

    for var in ("DATABASE_URL", "REDIS_URL", "JWT_SECRET"):
        monkeypatch.delenv(var, raising=False)
    with pytest.raises(ValidationError) as exc:
        Settings(_env_file=None, jwt_secret="x" * 40, database_url="postgresql://x")
    text = format_validation_error(exc.value)
    assert text.startswith("Invalid configuration:")
    assert "DATABASE_URL" in text and "REDIS_URL" in text
    assert "Traceback" not in text


def test_cross_field_errors_are_formatted_without_a_field_prefix():
    from app.core.config import format_validation_error

    with pytest.raises(ValidationError) as exc:
        make(jwt_secret="short")
    text = format_validation_error(exc.value)
    assert "  - JWT_SECRET must be at least 32 characters" in text
    assert "settings:" not in text
