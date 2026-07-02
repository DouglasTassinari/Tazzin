import pytest

from app.core.exceptions import ValidationError
from app.database.models.purchasing import PurchaseOrderStatus
from app.domain import purchasing_rules


def test_validate_line_item_rejects_non_positive_values():
    with pytest.raises(ValidationError):
        purchasing_rules.validate_line_item(0, 10)
    with pytest.raises(ValidationError):
        purchasing_rules.validate_line_item(5, 0)


def test_validate_rating_accepts_boundary_values():
    purchasing_rules.validate_rating(0)
    purchasing_rules.validate_rating(5)


def test_validate_rating_rejects_out_of_range():
    with pytest.raises(ValidationError):
        purchasing_rules.validate_rating(-0.01)
    with pytest.raises(ValidationError):
        purchasing_rules.validate_rating(5.01)


def test_allowed_transition_path():
    assert purchasing_rules.can_transition(PurchaseOrderStatus.DRAFT, PurchaseOrderStatus.SENT)
    assert purchasing_rules.can_transition(
        PurchaseOrderStatus.SENT, PurchaseOrderStatus.CONFIRMED
    )
    assert purchasing_rules.can_transition(
        PurchaseOrderStatus.CONFIRMED, PurchaseOrderStatus.RECEIVED
    )


def test_disallowed_transition_raises():
    with pytest.raises(ValidationError):
        purchasing_rules.assert_transition(PurchaseOrderStatus.DRAFT, PurchaseOrderStatus.RECEIVED)
    with pytest.raises(ValidationError):
        purchasing_rules.assert_transition(PurchaseOrderStatus.RECEIVED, PurchaseOrderStatus.DRAFT)
