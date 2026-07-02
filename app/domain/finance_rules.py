"""Pure business rules for the Finance module — no database, no I/O."""
from __future__ import annotations

from datetime import date

from app.core.exceptions import ValidationError
from app.database.models.finance import InvoiceStatus

_ALLOWED_TRANSITIONS: dict[InvoiceStatus, set[InvoiceStatus]] = {
    InvoiceStatus.OPEN: {InvoiceStatus.PAID, InvoiceStatus.OVERDUE, InvoiceStatus.CANCELLED},
    InvoiceStatus.OVERDUE: {InvoiceStatus.PAID, InvoiceStatus.CANCELLED},
    InvoiceStatus.PAID: set(),
    InvoiceStatus.CANCELLED: set(),
}


def validate_amount(amount: float) -> None:
    if amount <= 0:
        raise ValidationError(f"Amount must be positive, got {amount}")


def is_overdue(due_date: date, status: InvoiceStatus, as_of: date) -> bool:
    return due_date < as_of and status == InvoiceStatus.OPEN


def can_transition(current: InvoiceStatus, target: InvoiceStatus) -> bool:
    return target in _ALLOWED_TRANSITIONS.get(current, set())


def assert_transition(current: InvoiceStatus, target: InvoiceStatus) -> None:
    if not can_transition(current, target):
        raise ValidationError(f"Cannot move invoice from {current.value} to {target.value}")
