"""Pure business rules for the Purchasing module — no database, no I/O.

Kept separate from :mod:`app.services.purchasing_service` so the rules can
be unit tested with plain Python objects and reused (e.g. by a future API
layer) without pulling in a database session.
"""
from __future__ import annotations

from app.core.exceptions import ValidationError
from app.database.models.purchasing import PurchaseOrderStatus

MIN_RATING = 0.0
MAX_RATING = 5.0

_ALLOWED_TRANSITIONS: dict[PurchaseOrderStatus, set[PurchaseOrderStatus]] = {
    PurchaseOrderStatus.DRAFT: {PurchaseOrderStatus.SENT, PurchaseOrderStatus.CANCELLED},
    PurchaseOrderStatus.SENT: {PurchaseOrderStatus.CONFIRMED, PurchaseOrderStatus.CANCELLED},
    PurchaseOrderStatus.CONFIRMED: {PurchaseOrderStatus.RECEIVED, PurchaseOrderStatus.CANCELLED},
    PurchaseOrderStatus.RECEIVED: set(),
    PurchaseOrderStatus.CANCELLED: set(),
}


def validate_line_item(quantity: int, unit_cost: float) -> None:
    if quantity <= 0:
        raise ValidationError("Line item quantity must be positive")
    if unit_cost <= 0:
        raise ValidationError("Line item unit cost must be positive")


def validate_rating(rating: float) -> None:
    if rating < MIN_RATING or rating > MAX_RATING:
        raise ValidationError(
            f"Rating must be between {MIN_RATING} and {MAX_RATING}, got {rating}"
        )


def can_transition(current: PurchaseOrderStatus, target: PurchaseOrderStatus) -> bool:
    return target in _ALLOWED_TRANSITIONS.get(current, set())


def assert_transition(current: PurchaseOrderStatus, target: PurchaseOrderStatus) -> None:
    if not can_transition(current, target):
        raise ValidationError(
            f"Cannot move purchase order from {current.value} to {target.value}"
        )
