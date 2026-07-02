"""Pure business rules for the Projects module — no database, no I/O.

Kept separate from :mod:`app.services.projects_service` so the rules can be
unit tested with plain Python objects and reused without pulling in a
database session.
"""
from __future__ import annotations

from datetime import date

from app.core.exceptions import ValidationError
from app.database.models.projects import ProjectStatus

_ALLOWED_TRANSITIONS: dict[ProjectStatus, set[ProjectStatus]] = {
    ProjectStatus.PLANNING: {ProjectStatus.ACTIVE, ProjectStatus.CANCELLED},
    ProjectStatus.ACTIVE: {ProjectStatus.ON_HOLD, ProjectStatus.COMPLETED, ProjectStatus.CANCELLED},
    ProjectStatus.ON_HOLD: {ProjectStatus.ACTIVE, ProjectStatus.CANCELLED},
    ProjectStatus.COMPLETED: set(),
    ProjectStatus.CANCELLED: set(),
}


def validate_budget(budget: float) -> None:
    if budget <= 0:
        raise ValidationError(f"Budget must be positive, got {budget}")


def validate_dates(start_date: date, target_end_date: date) -> None:
    if target_end_date <= start_date:
        raise ValidationError("Target end date must be after start date")


def completion_rate(tasks_done: int, tasks_total: int) -> float:
    if tasks_total == 0:
        return 0.0
    return round(tasks_done / tasks_total * 100, 2)


def can_transition(current: ProjectStatus, target: ProjectStatus) -> bool:
    return target in _ALLOWED_TRANSITIONS.get(current, set())


def assert_transition(current: ProjectStatus, target: ProjectStatus) -> None:
    if not can_transition(current, target):
        raise ValidationError(f"Cannot move project from {current.value} to {target.value}")
