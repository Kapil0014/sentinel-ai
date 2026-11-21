"""Migration upgrade/downgrade and model-vs-migration drift."""

import pytest
from alembic.autogenerate import compare_metadata
from alembic.migration import MigrationContext
from sqlalchemy import create_engine, inspect

import app.models  # noqa: F401
from alembic import command
from app.database.base import Base

pytestmark = pytest.mark.integration

WEEK1_TABLES = {"users", "projects", "websites", "testing_sessions"}


def _tables(url: str) -> set[str]:
    engine = create_engine(url)
    try:
        return set(inspect(engine).get_table_names()) - {"alembic_version"}
    finally:
        engine.dispose()


def test_upgrade_creates_week1_tables(alembic_cfg, scratch_db):
    command.upgrade(alembic_cfg, "head")
    assert _tables(scratch_db) == WEEK1_TABLES


def test_downgrade_removes_everything(alembic_cfg, scratch_db):
    command.upgrade(alembic_cfg, "head")
    command.downgrade(alembic_cfg, "base")
    assert _tables(scratch_db) == set()


def test_upgrade_downgrade_upgrade_round_trip(alembic_cfg, scratch_db):
    command.upgrade(alembic_cfg, "head")
    command.downgrade(alembic_cfg, "base")
    command.upgrade(alembic_cfg, "head")
    assert _tables(scratch_db) == WEEK1_TABLES


def test_migrated_schema_matches_models(alembic_cfg, scratch_db):
    """Fails if someone edits a model without writing a migration."""
    command.upgrade(alembic_cfg, "head")
    engine = create_engine(scratch_db)
    try:
        with engine.connect() as conn:
            ctx = MigrationContext.configure(conn, opts={"compare_type": True})
            diff = compare_metadata(ctx, Base.metadata)
    finally:
        engine.dispose()
    assert diff == [], f"models and migrations have drifted: {diff}"
