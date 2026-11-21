"""Week 1 tables: users, projects, websites, testing_sessions (see docs/database.md)."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, CreatedAtMixin, UpdatedAtMixin, UUIDPrimaryKeyMixin
from app.models.enums import SessionMode, SessionState, UserRole


def _enum(enum_cls: type, name: str) -> Enum:
    """Store enums as VARCHAR + CHECK (not native PG enums) for easy migrations."""
    return Enum(
        enum_cls,
        name=name,
        native_enum=False,
        create_constraint=True,
        length=24,
        values_callable=lambda e: [member.value for member in e],
    )


class User(UUIDPrimaryKeyMixin, CreatedAtMixin, UpdatedAtMixin, Base):
    __tablename__ = "users"
    __table_args__ = (Index("uq_users_email_lower", text("lower(email)"), unique=True),)

    email: Mapped[str] = mapped_column(String(320), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(
        _enum(UserRole, "user_role"), nullable=False, default=UserRole.USER, server_default="user"
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("true"))

    projects: Mapped[list[Project]] = relationship(
        back_populates="owner", cascade="all, delete-orphan"
    )


class Project(UUIDPrimaryKeyMixin, CreatedAtMixin, UpdatedAtMixin, Base):
    __tablename__ = "projects"
    __table_args__ = (UniqueConstraint("owner_id", "name", name="uq_projects_owner_id_name"),)

    owner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)

    owner: Mapped[User] = relationship(back_populates="projects")
    websites: Mapped[list[Website]] = relationship(
        back_populates="project", cascade="all, delete-orphan"
    )


class Website(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    __tablename__ = "websites"
    __table_args__ = (
        UniqueConstraint("project_id", "base_url", name="uq_websites_project_id_base_url"),
    )

    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    base_url: Mapped[str] = mapped_column(String(2048), nullable=False)
    hostname: Mapped[str] = mapped_column(String(255), nullable=False)
    allowed_domains: Mapped[list[str]] = mapped_column(
        JSONB, nullable=False, server_default=text("'[]'::jsonb")
    )
    is_authorized_target: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("false")
    )

    project: Mapped[Project] = relationship(back_populates="websites")
    sessions: Mapped[list[TestingSession]] = relationship(
        back_populates="website", cascade="all, delete-orphan"
    )


class TestingSession(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    __tablename__ = "testing_sessions"
    __test__ = False  # not a pytest test class despite the "Test" prefix
    __table_args__ = (
        Index("ix_testing_sessions_website_id_created_at", "website_id", text("created_at DESC")),
        Index("ix_testing_sessions_state", "state"),
    )

    website_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("websites.id", ondelete="CASCADE"), nullable=False
    )
    created_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    mode: Mapped[SessionMode] = mapped_column(_enum(SessionMode, "session_mode"), nullable=False)
    state: Mapped[SessionState] = mapped_column(
        _enum(SessionState, "session_state"),
        nullable=False,
        default=SessionState.CREATED,
        server_default="CREATED",
    )
    config: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, server_default=text("'{}'::jsonb")
    )
    cancel_requested: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("false")
    )
    error_message: Mapped[str | None] = mapped_column(Text)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    website: Mapped[Website] = relationship(back_populates="sessions")
