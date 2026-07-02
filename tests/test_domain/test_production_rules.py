import pytest

from app.core.exceptions import ValidationError
from app.database.models.production import WorkOrderStatus
from app.domain import production_rules


def test_validate_quantities_accepts_within_tolerance():
    production_rules.validate_quantities(100, 95, 5)
    production_rules.validate_quantities(100, 100, 5)  # 5% overrun tolerance


def test_validate_quantities_rejects_negative_values():
    with pytest.raises(ValidationError):
        production_rules.validate_quantities(-1, 0, 0)
    with pytest.raises(ValidationError):
        production_rules.validate_quantities(100, -1, 0)
    with pytest.raises(ValidationError):
        production_rules.validate_quantities(100, 0, -1)


def test_validate_quantities_rejects_overrun_beyond_tolerance():
    with pytest.raises(ValidationError):
        production_rules.validate_quantities(100, 100, 10)


def test_allowed_transition_path():
    assert production_rules.can_transition(WorkOrderStatus.PLANNED, WorkOrderStatus.IN_PROGRESS)
    assert production_rules.can_transition(WorkOrderStatus.PLANNED, WorkOrderStatus.CANCELLED)
    assert production_rules.can_transition(WorkOrderStatus.IN_PROGRESS, WorkOrderStatus.COMPLETED)
    assert production_rules.can_transition(WorkOrderStatus.IN_PROGRESS, WorkOrderStatus.CANCELLED)


def test_disallowed_transition_raises():
    with pytest.raises(ValidationError):
        production_rules.assert_transition(WorkOrderStatus.PLANNED, WorkOrderStatus.COMPLETED)
    with pytest.raises(ValidationError):
        production_rules.assert_transition(WorkOrderStatus.COMPLETED, WorkOrderStatus.PLANNED)
    with pytest.raises(ValidationError):
        production_rules.assert_transition(WorkOrderStatus.CANCELLED, WorkOrderStatus.PLANNED)
