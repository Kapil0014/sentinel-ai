"""Application configuration.

All settings come from environment variables (or a local ``.env`` file in
development). Validation happens at import/startup so a misconfigured service
fails immediately with a readable message instead of failing later at runtime.
"""

from __future__ import annotations

import sys
from enum import StrEnum
from functools import lru_cache
from typing import Annotated, Self
from urllib.parse import urlsplit, urlunsplit

from pydantic import Field, ValidationError, field_validator, model_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict

MIN_JWT_SECRET_LENGTH = 32
PLACEHOLDER_MARKERS = ("replace-with", "change-me", "changeme", "your-")


class AppEnv(StrEnum):
    DEVELOPMENT = "development"
    TEST = "test"
    PRODUCTION = "production"


class LLMProviderName(StrEnum):
    GEMINI = "gemini"
    MOCK = "mock"


def _csv(value: object) -> list[str]:
    if isinstance(value, str):
        return [item.strip() for item in value.split(",") if item.strip()]
    if isinstance(value, list | tuple | set):
        return [str(item).strip() for item in value if str(item).strip()]
    raise ValueError("expected a comma-separated string")


def redact_url(url: str) -> str:
    """Return ``url`` with any password replaced by ``***`` (safe to log/return)."""
    parts = urlsplit(url)
    if parts.password is None:
        return url
    host = parts.hostname or ""
    if parts.port:
        host = f"{host}:{parts.port}"
    user = parts.username or ""
    netloc = f"{user}:***@{host}" if user else f"***@{host}"
    return urlunsplit((parts.scheme, netloc, parts.path, parts.query, parts.fragment))


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    app_env: AppEnv = AppEnv.DEVELOPMENT
    log_level: str = "INFO"

    database_url: str
    redis_url: str
    browser_worker_url: str = "http://browser-worker:8081"
    artifacts_dir: str = "/artifacts"

    jwt_secret: str
    cors_origins: Annotated[list[str], NoDecode] = Field(
        default_factory=lambda: ["http://localhost:5173"]
    )

    llm_provider: LLMProviderName = LLMProviderName.MOCK
    gemini_api_key: str | None = None
    gemini_model: str = "gemini-2.5-flash"

    # Hosts allowed to resolve to private addresses (controlled demo only).
    allowed_private_hosts: Annotated[list[str], NoDecode] = Field(default_factory=list)

    health_check_timeout_seconds: float = Field(default=2.0, gt=0, le=30)

    @field_validator("cors_origins", "allowed_private_hosts", mode="before")
    @classmethod
    def _split_csv(cls, value: object) -> list[str]:
        return _csv(value)

    @field_validator("log_level")
    @classmethod
    def _valid_log_level(cls, value: str) -> str:
        level = value.upper()
        if level not in {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}:
            raise ValueError("LOG_LEVEL must be DEBUG, INFO, WARNING, ERROR or CRITICAL")
        return level

    @field_validator("database_url")
    @classmethod
    def _database_url_uses_psycopg(cls, value: str) -> str:
        if not value.startswith("postgresql+psycopg://"):
            raise ValueError(
                "DATABASE_URL must start with 'postgresql+psycopg://' (psycopg v3 driver)"
            )
        return value

    @field_validator("redis_url")
    @classmethod
    def _redis_url_scheme(cls, value: str) -> str:
        if not value.startswith(("redis://", "rediss://")):
            raise ValueError("REDIS_URL must start with 'redis://' or 'rediss://'")
        return value

    @field_validator("cors_origins")
    @classmethod
    def _no_wildcard_origin(cls, value: list[str]) -> list[str]:
        if "*" in value:
            raise ValueError("CORS_ORIGINS must list explicit origins, not '*'")
        return value

    @model_validator(mode="after")
    def _cross_field_rules(self) -> Self:
        if len(self.jwt_secret) < MIN_JWT_SECRET_LENGTH:
            raise ValueError(
                f"JWT_SECRET must be at least {MIN_JWT_SECRET_LENGTH} characters "
                '(generate one with: python -c "import secrets; print(secrets.token_hex(32))")'
            )
        if self.app_env is AppEnv.PRODUCTION:
            lowered = self.jwt_secret.lower()
            if any(marker in lowered for marker in PLACEHOLDER_MARKERS):
                raise ValueError("JWT_SECRET still looks like a placeholder; set a real secret")
            if self.allowed_private_hosts:
                raise ValueError("ALLOWED_PRIVATE_HOSTS must be empty in production")
        if self.llm_provider is LLMProviderName.GEMINI and not self.gemini_api_key:
            raise ValueError(
                "LLM_PROVIDER=gemini requires GEMINI_API_KEY "
                "(or set LLM_PROVIDER=mock for development without a key)"
            )
        return self

    @property
    def is_production(self) -> bool:
        return self.app_env is AppEnv.PRODUCTION


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]  # values come from the environment


def format_validation_error(exc: ValidationError) -> str:
    """Render a Pydantic error as one readable line per problem (no traceback)."""
    lines = ["Invalid configuration:"]
    for err in exc.errors():
        field = ".".join(str(part).upper() for part in err["loc"])
        message = str(err["msg"]).removeprefix("Value error, ")
        # Cross-field rules have no single field; their message already names the variable.
        lines.append(f"  - {field}: {message}" if field else f"  - {message}")
    lines.append("See .env.example for the expected variables.")
    return "\n".join(lines)


def load_settings_or_exit() -> Settings:
    """Startup entry point: print a readable error and exit(1) on bad configuration."""
    try:
        return get_settings()
    except ValidationError as exc:
        sys.stderr.write(format_validation_error(exc) + "\n")
        raise SystemExit(1) from None
