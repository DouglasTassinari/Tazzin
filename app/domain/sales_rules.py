"""Pure business rules for the Sales module — no database, no I/O.

Kept separate from :mod:`app.services.sales_service` so the rules can be
unit tested with plain Python objects and reused (e.g. by a future API
layer) without pulling in a database session.
"""
from __future__ import annotations

from app.core.exceptions import ValidationError
from app.database.models.sales import OrderStatus

MAX_DISCOUNT_PCT = 25.0

_ALLOWED_TRANSITIONS: dict[OrderStatus, set[OrderStatus]] = {
    OrderStatus.DRAFT: {OrderStatus.CONFIRMED, OrderStatus.CANCELLED},
    OrderStatus.CONFIRMED: {OrderStatus.SHIPPED, OrderStatus.CANCELLED},
    OrderStatus.SHIPPED: {OrderStatus.INVOICED},
    OrderStatus.INVOICED: set(),
    OrderStatus.CANCELLED: set(),
}


def validate_discount(discount_pct: float) -> None:
    if discount_pct < 0 or discount_pct > MAX_DISCOUNT_PCT:
        raise ValidationError(
            f"Discount must be between 0 and {MAX_DISCOUNT_PCT}%, got {discount_pct}%"
        )


def validate_line_item(quantity: int, unit_price: float) -> None:
    if quantity <= 0:
        raise ValidationError("Line item quantity must be positive")
    if unit_price <= 0:
        raise ValidationError("Line item unit price must be positive")


def can_transition(current: OrderStatus, target: OrderStatus) -> bool:
    return target in _ALLOWED_TRANSITIONS.get(current, set())


def assert_transition(current: OrderStatus, target: OrderStatus) -> None:
    if not can_transition(current, target):
        raise ValidationError(f"Cannot move order from {current.value} to {target.value}")


def calculate_net_amount(gross_amount: float, discount_pct: float) -> float:
    validate_discount(discount_pct)
    return round(gross_amount * (1 - discount_pct / 100), 2)
