"""Pure business rules for the Inventory module — no database, no I/O."""
from __future__ import annotations

from app.core.exceptions import ValidationError
from app.database.models.inventory import MovementType

_SIGNED_TYPES = {MovementType.INBOUND, MovementType.OUTBOUND, MovementType.TRANSFER}


def validate_movement(movement_type: MovementType, quantity: int) -> None:
    if quantity == 0:
        raise ValidationError("Movement quantity cannot be zero")
    if movement_type in _SIGNED_TYPES and quantity < 0:
        raise ValidationError(f"{movement_type.value} quantity must be positive, got {quantity}")


def is_below_reorder_point(on_hand: int, reorder_point: int) -> bool:
    return on_hand < reorder_point
