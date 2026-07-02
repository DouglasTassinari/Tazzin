from datetime import date

import pytest

from app.core.exceptions import ValidationError
from app.database.models.people import TimeOffStatus
from app.domain import people_rules


def test_validate_date_range_accepts_same_day():
    people_rules.validate_date_range(date(2026, 1, 1), date(2026, 1, 1))


def test_validate_date_range_rejects_end_before_start():
    with pytest.raises(ValidationError):
        people_rules.validate_date_range(date(2026, 1, 10), date(2026, 1, 1))


def test_validate_salary_accepts_positive_value():
    people_rules.validate_salary(1000)


def test_validate_salary_rejects_non_positive_value():
    with pytest.raises(ValidationError):
        people_rules.validate_salary(0)
    with pytest.raises(ValidationError):
        people_rules.validate_salary(-100)


def test_assert_can_decide_accepts_pending():
    people_rules.assert_can_decide(TimeOffStatus.PENDING)


def test_assert_can_decide_rejects_non_pending():
    with pytest.raises(ValidationError):
        people_rules.assert_can_decide(TimeOffStatus.APPROVED)
    with pytest.raises(ValidationError):
        people_rules.assert_can_decide(TimeOffStatus.REJECTED)
