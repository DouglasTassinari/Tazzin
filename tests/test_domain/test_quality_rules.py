import pytest

from app.core.exceptions import ValidationError
from app.database.models.quality import NonConformanceStatus
from app.domain import quality_rules


def test_validate_inspection_accepts_boundary_values():
    quality_rules.validate_inspection(10, 0)
    quality_rules.validate_inspection(10, 10)


def test_validate_inspection_rejects_non_positive_sample_size():
    with pytest.raises(ValidationError):
        quality_rules.validate_inspection(0, 0)
    with pytest.raises(ValidationError):
        quality_rules.validate_inspection(-1, 0)


def test_validate_inspection_rejects_out_of_range_defect_count():
    with pytest.raises(ValidationError):
        quality_rules.validate_inspection(10, -1)
    with pytest.raises(ValidationError):
        quality_rules.validate_inspection(10, 11)


def test_defect_rate_computes_percentage():
    assert quality_rules.defect_rate(200, 10) == 5.0


def test_defect_rate_returns_zero_for_zero_sample_size():
    assert quality_rules.defect_rate(0, 0) == 0.0


def test_allowed_transition_path():
    assert quality_rules.can_transition(NonConformanceStatus.OPEN, NonConformanceStatus.UNDER_REVIEW)
    assert quality_rules.can_transition(NonConformanceStatus.UNDER_REVIEW, NonConformanceStatus.RESOLVED)
    assert quality_rules.can_transition(NonConformanceStatus.RESOLVED, NonConformanceStatus.CLOSED)


def test_disallowed_transition_raises():
    with pytest.raises(ValidationError):
        quality_rules.assert_transition(NonConformanceStatus.OPEN, NonConformanceStatus.RESOLVED)
    with pytest.raises(ValidationError):
        quality_rules.assert_transition(NonConformanceStatus.CLOSED, NonConformanceStatus.OPEN)
