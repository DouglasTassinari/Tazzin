from datetime import date

import pytest

from app.core.exceptions import ValidationError
from app.database.models.finance import InvoiceStatus
from app.domain import finance_rules


def test_validate_amount_accepts_positive_values():
    finance_rules.validate_amount(0.01)
    finance_rules.validate_amount(1000)


def test_validate_amount_rejects_non_positive_values():
    with pytest.raises(ValidationError):
        finance_rules.validate_amount(0)
    with pytest.raises(ValidationError):
        finance_rules.validate_amount(-10)


def test_is_overdue_true_when_past_due_and_open():
    assert finance_rules.is_overdue(date(2026, 1, 1), InvoiceStatus.OPEN, date(2026, 2, 1))


def test_is_overdue_false_when_not_yet_due():
    assert not finance_rules.is_overdue(date(2026, 3, 1), InvoiceStatus.OPEN, date(2026, 2, 1))


def test_is_overdue_false_when_not_open():
    assert not finance_rules.is_overdue(date(2026, 1, 1), InvoiceStatus.PAID, date(2026, 2, 1))


def test_allowed_transition_path():
    assert finance_rules.can_transition(InvoiceStatus.OPEN, InvoiceStatus.PAID)
    assert finance_rules.can_transition(InvoiceStatus.OPEN, InvoiceStatus.OVERDUE)
    assert finance_rules.can_transition(InvoiceStatus.OVERDUE, InvoiceStatus.PAID)


def test_disallowed_transition_raises():
    with pytest.raises(ValidationError):
        finance_rules.assert_transition(InvoiceStatus.PAID, InvoiceStatus.OPEN)
    with pytest.raises(ValidationError):
        finance_rules.assert_transition(InvoiceStatus.CANCELLED, InvoiceStatus.PAID)
