import pytest

from app.core.exceptions import ValidationError
from app.database.models.inventory import MovementType
from app.domain import inventory_rules


def test_validate_movement_rejects_zero_quantity():
    with pytest.raises(ValidationError):
        inventory_rules.validate_movement(MovementType.INBOUND, 0)


def test_validate_movement_rejects_negative_for_signed_types():
    with pytest.raises(ValidationError):
        inventory_rules.validate_movement(MovementType.INBOUND, -5)
    with pytest.raises(ValidationError):
        inventory_rules.validate_movement(MovementType.OUTBOUND, -5)
    with pytest.raises(ValidationError):
        inventory_rules.validate_movement(MovementType.TRANSFER, -5)


def test_validate_movement_allows_negative_adjustment():
    inventory_rules.validate_movement(MovementType.ADJUSTMENT, -5)
    inventory_rules.validate_movement(MovementType.ADJUSTMENT, 5)


def test_validate_movement_accepts_positive_signed_types():
    inventory_rules.validate_movement(MovementType.INBOUND, 10)
    inventory_rules.validate_movement(MovementType.OUTBOUND, 10)
    inventory_rules.validate_movement(MovementType.TRANSFER, 10)


def test_is_below_reorder_point():
    assert inventory_rules.is_below_reorder_point(5, 10) is True
    assert inventory_rules.is_below_reorder_point(10, 10) is False
    assert inventory_rules.is_below_reorder_point(20, 10) is False
