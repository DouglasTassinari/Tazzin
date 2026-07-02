"""Pure business rules for the Production module — no database, no I/O.

Kept separate from :mod:`app.services.production_service` so the rules can
be unit tested with plain Python objects and reused without pulling in a
database session.
"""
from __future__ import annotations

from app.core.exceptions import ValidationError
from app.database.models.production import WorkOrderStatus

OVERRUN_TOLERANCE = 1.05

_ALLOWED_TRANSITIONS: dict[WorkOrderStatus, set[WorkOrderStatus]] = {
    WorkOrderStatus.PLANNED: {WorkOrderStatus.IN_PROGRESS, WorkOrderStatus.CANCELLED},
    WorkOrderStatus.IN_PROGRESS: {WorkOrderStatus.COMPLETED, WorkOrderStatus.CANCELLED},
    WorkOrderStatus.COMPLETED: set(),
    WorkOrderStatus.CANCELLED: set(),
}


def validate_quantities(
    planned_quantity: int, produced_quantity: int, scrap_quantity: int
) -> None:
    if planned_quantity < 0 or produced_quantity < 0 or scrap_quantity < 0:
        raise ValidationError("Quantities must not be negative")
    if produced_quantity + scrap_quantity > planned_quantity * OVERRUN_TOLERANCE:
        raise ValidationError(
            "Produced plus scrap quantity exceeds planned quantity beyond the "
            f"{int((OVERRUN_TOLERANCE - 1) * 100)}% tolerance"
        )


def can_transition(current: WorkOrderStatus, target: WorkOrderStatus) -> bool:
    return target in _ALLOWED_TRANSITIONS.get(current, set())


def assert_transition(current: WorkOrderStatus, target: WorkOrderStatus) -> None:
    if not can_transition(current, target):
        raise ValidationError(f"Cannot move work order from {current.value} to {target.value}")
