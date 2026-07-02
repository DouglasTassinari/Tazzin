import pytest

from app.core.exceptions import ValidationError
from app.database.models.maintenance import MaintenanceStatus
from app.domain import maintenance_rules


def test_validate_log_accepts_valid_values():
    maintenance_rules.validate_log(1.5, 0)
    maintenance_rules.validate_log(0.5, 250.0)


def test_validate_log_rejects_non_positive_hours():
    with pytest.raises(ValidationError):
        maintenance_rules.validate_log(0, 10)
    with pytest.raises(ValidationError):
        maintenance_rules.validate_log(-1, 10)


def test_validate_log_rejects_negative_cost():
    with pytest.raises(ValidationError):
        maintenance_rules.validate_log(1, -0.01)


def test_allowed_transition_path():
    assert maintenance_rules.can_transition(MaintenanceStatus.OPEN, MaintenanceStatus.SCHEDULED)
    assert maintenance_rules.can_transition(MaintenanceStatus.SCHEDULED, MaintenanceStatus.IN_PROGRESS)
    assert maintenance_rules.can_transition(MaintenanceStatus.IN_PROGRESS, MaintenanceStatus.COMPLETED)
    assert maintenance_rules.can_transition(MaintenanceStatus.OPEN, MaintenanceStatus.CANCELLED)


def test_disallowed_transition_raises():
    with pytest.raises(ValidationError):
        maintenance_rules.assert_transition(MaintenanceStatus.OPEN, MaintenanceStatus.COMPLETED)
    with pytest.raises(ValidationError):
        maintenance_rules.assert_transition(MaintenanceStatus.COMPLETED, MaintenanceStatus.OPEN)
    with pytest.raises(ValidationError):
        maintenance_rules.assert_transition(MaintenanceStatus.CANCELLED, MaintenanceStatus.SCHEDULED)
