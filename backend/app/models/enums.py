"""Domain enumerations shared by models, schemas and services."""

from __future__ import annotations

from enum import StrEnum


class UserRole(StrEnum):
    USER = "user"
    ADMIN = "admin"


class SessionMode(StrEnum):
    AUTONOMOUS = "autonomous"
    ASSISTED = "assisted"


class SessionState(StrEnum):
    """Workflow states. Must match the state machine in docs/architecture.md."""

    CREATED = "CREATED"
    INITIALIZED = "INITIALIZED"
    DISCOVERING = "DISCOVERING"
    ANALYZING = "ANALYZING"
    GENERATING_TESTS = "GENERATING_TESTS"
    VALIDATING_TESTS = "VALIDATING_TESTS"
    AWAITING_REVIEW = "AWAITING_REVIEW"
    AWAITING_APPROVAL = "AWAITING_APPROVAL"
    EXECUTING = "EXECUTING"
    OBSERVING = "OBSERVING"
    REPORTING = "REPORTING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
