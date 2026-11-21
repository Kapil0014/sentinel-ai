"""Constraint behaviour of the Week 1 schema, against real PostgreSQL."""

import pytest
from sqlalchemy import select, text
from sqlalchemy.exc import IntegrityError

from app.models import Project, SessionMode, SessionState, TestingSession, User, Website

pytestmark = pytest.mark.integration


def _seed(session):
    user = User(email="Alice@Example.com", password_hash="x")
    project = Project(owner=user, name="Shop")
    website = Website(project=project, base_url="http://demo-site", hostname="demo-site")
    session.add_all([user, project, website])
    session.commit()
    return user, project, website


def test_defaults_are_applied(migrated_session):
    user, _, website = _seed(migrated_session)
    ts = TestingSession(website_id=website.id, created_by=user.id, mode=SessionMode.ASSISTED)
    migrated_session.add(ts)
    migrated_session.commit()
    migrated_session.refresh(ts)
    assert ts.state is SessionState.CREATED
    assert ts.cancel_requested is False
    assert ts.config == {}
    assert ts.created_at is not None and user.role.value == "user" and user.is_active is True
    assert website.allowed_domains == [] and website.is_authorized_target is False


def test_email_is_unique_case_insensitively(migrated_session):
    migrated_session.add(User(email="bob@example.com", password_hash="x"))
    migrated_session.commit()
    migrated_session.add(User(email="BOB@example.com", password_hash="x"))
    with pytest.raises(IntegrityError):
        migrated_session.commit()


def test_project_name_unique_per_owner(migrated_session):
    user, _, _ = _seed(migrated_session)
    migrated_session.add(Project(owner_id=user.id, name="Shop"))
    with pytest.raises(IntegrityError):
        migrated_session.commit()


def test_invalid_state_rejected_by_check_constraint(migrated_session):
    user, _, website = _seed(migrated_session)
    with pytest.raises(IntegrityError):
        migrated_session.execute(
            text(
                "INSERT INTO testing_sessions (website_id, created_by, mode, state) "
                "VALUES (:w, :u, 'assisted', 'NOT_A_STATE')"
            ),
            {"w": website.id, "u": user.id},
        )
        migrated_session.commit()


def test_deleting_user_cascades_to_everything_below(migrated_session):
    user, _, website = _seed(migrated_session)
    migrated_session.add(
        TestingSession(website_id=website.id, created_by=user.id, mode=SessionMode.AUTONOMOUS)
    )
    migrated_session.commit()
    migrated_session.execute(text("DELETE FROM users WHERE id = :id"), {"id": user.id})
    migrated_session.commit()
    for table in ("projects", "websites", "testing_sessions"):
        assert migrated_session.execute(text(f"SELECT count(*) FROM {table}")).scalar_one() == 0
    assert migrated_session.execute(select(User)).first() is None
