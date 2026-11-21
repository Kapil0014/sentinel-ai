"""Scratch-database fixtures: tests never touch the developer's real data."""

from __future__ import annotations

import uuid
from collections.abc import Iterator

import psycopg
import pytest
from alembic.config import Config
from sqlalchemy import create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session

from alembic import command


def _sqlalchemy_url(dsn: str, dbname: str) -> str:
    parts = dict(p.split("=", 1) for p in dsn.split())
    auth = parts["user"] + (f":{parts['password']}" if "password" in parts else "")
    return f"postgresql+psycopg://{auth}@{parts['host']}:{parts['port']}/{dbname}"


@pytest.fixture
def scratch_db(pg_admin_dsn: str) -> Iterator[str]:
    """Create an empty throwaway database and yield its SQLAlchemy URL."""
    name = f"sentinel_test_{uuid.uuid4().hex[:10]}"
    with psycopg.connect(pg_admin_dsn, autocommit=True) as conn:
        conn.execute(f'CREATE DATABASE "{name}"')
    try:
        yield _sqlalchemy_url(pg_admin_dsn, name)
    finally:
        with psycopg.connect(pg_admin_dsn, autocommit=True) as conn:
            conn.execute(f'DROP DATABASE IF EXISTS "{name}" WITH (FORCE)')


@pytest.fixture
def alembic_cfg(scratch_db: str) -> Config:
    cfg = Config("alembic.ini")
    cfg.set_main_option("sqlalchemy.url", scratch_db.replace("%", "%%"))
    return cfg


@pytest.fixture
def migrated_session(alembic_cfg: Config, scratch_db: str) -> Iterator[Session]:
    command.upgrade(alembic_cfg, "head")
    engine = create_engine(scratch_db)
    with Session(engine) as session:
        yield session
    engine.dispose()


__all__ = ["make_url"]
