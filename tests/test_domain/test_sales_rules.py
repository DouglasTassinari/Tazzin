import pytest

from app.core.exceptions import ValidationError
from app.database.models.sales import OrderStatus
from app.domain import sales_rules


def test_validate_discount_accepts_boundary_values():
    sales_rules.validate_discount(0)
    sales_rules.validate_discount(sales_rules.MAX_DISCOUNT_PCT)


def test_validate_discount_rejects_out_of_range():
    with pytest.raises(ValidationError):
        sales_rules.validate_discount(-1)
    with pytest.raises(ValidationError):
        sales_rules.validate_discount(sales_rules.MAX_DISCOUNT_PCT + 0.01)


def test_validate_line_item_rejects_non_positive_values():
    with pytest.raises(ValidationError):
        sales_rules.validate_line_item(0, 10)
    with pytest.raises(ValidationError):
        sales_rules.validate_line_item(5, 0)


def test_allowed_transition_path():
    assert sales_rules.can_transition(OrderStatus.DRAFT, OrderStatus.CONFIRMED)
    assert sales_rules.can_transition(OrderStatus.CONFIRMED, OrderStatus.SHIPPED)
    assert sales_rules.can_transition(OrderStatus.SHIPPED, OrderStatus.INVOICED)


def test_disallowed_transition_raises():
    with pytest.raises(ValidationError):
        sales_rules.assert_transition(OrderStatus.DRAFT, OrderStatus.INVOICED)
    with pytest.raises(ValidationError):
        sales_rules.assert_transition(OrderStatus.INVOICED, OrderStatus.DRAFT)


def test_calculate_net_amount_applies_discount():
    assert sales_rules.calculate_net_amount(1000, 10) == 900.0
