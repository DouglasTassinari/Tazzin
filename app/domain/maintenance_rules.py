"""Pure business rules for the Maintenance module — no database, no I/O."""
from __future__ import annotations

from app.core.exceptions import ValidationError
from app.database.models.maintenance import MaintenanceStatus

_ALLOWED_TRANSITIONS: dict[MaintenanceStatus, set[MaintenanceStatus]] = {
    MaintenanceStatus.OPEN: {MaintenanceStatus.SCHEDULED, MaintenanceStatus.CANCELLED},
    MaintenanceStatus.SCHEDULED: {MaintenanceStatus.IN_PROGRESS, MaintenanceStatus.CANCELLED},
    MaintenanceStatus.IN_PROGRESS: {MaintenanceStatus.COMPLETED, MaintenanceStatus.CANCELLED},
    MaintenanceStatus.COMPLETED: set(),
    MaintenanceStatus.CANCELLED: set(),
}


def validate_log(hours_spent: float, cost: float) -> None:
    if hours_spent <= 0:
        raise ValidationError("Hours spent must be positive")
    if cost < 0:
        raise ValidationError("Cost must be non-negative")


def can_transition(current: MaintenanceStatus, target: MaintenanceStatus) -> bool:
    return target in _ALLOWED_TRANSITIONS.get(current, set())


def assert_transition(current: MaintenanceStatus, target: MaintenanceStatus) -> None:
    if not can_transition(current, target):
        raise ValidationError(f"Cannot move request from {current.value} to {target.value}")
