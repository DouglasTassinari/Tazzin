"""Tests for adjustments domain rules."""
from __future__ import annotations

import pytest

from app.core.exceptions import ValidationError
from app.domain.adjustments_rules import (
    difference_seconds,
    is_improvement,
    lot_impact_seconds,
    machine_is_worsening,
    operator_has_too_many_worsenings,
    recent_worsening_rate_alert,
    validate_adjustment,
)


class TestValidation:
    def test_negative_previous(self):
        with pytest.raises(ValidationError):
            validate_adjustment(-1, 100, "test")

    def test_same_values(self):
        with pytest.raises(ValidationError):
            validate_adjustment(100, 100, "test")

    def test_empty_justification(self):
        with pytest.raises(ValidationError):
            validate_adjustment(100, 80, "")

    def test_valid(self):
        validate_adjustment(100, 80, "Changed tooling")


class TestDifference:
    def test_improvement(self):
        assert difference_seconds(100, 80) == 20

    def test_worsening(self):
        assert difference_seconds(80, 100) == -20


class TestIsImprovement:
    def test_yes(self):
        assert is_improvement(100, 80) is True

    def test_no(self):
        assert is_improvement(80, 100) is False


class TestLotImpact:
    def test_positive(self):
        assert lot_impact_seconds(20, 100) == 2000.0

    def test_negative(self):
        assert lot_impact_seconds(-10, 50) == -500.0


class TestOperatorAlert:
    def test_too_few(self):
        assert operator_has_too_many_worsenings(1, 1) is False

    def test_more_worsenings(self):
        assert operator_has_too_many_worsenings(1, 3) is True

    def test_balanced(self):
        assert operator_has_too_many_worsenings(3, 3) is False


class TestMachineAlert:
    def test_worsening(self):
        assert machine_is_worsening(1, 4) is True

    def test_ok(self):
        assert machine_is_worsening(5, 2) is False


class TestRecentAlert:
    def test_above(self):
        assert recent_worsening_rate_alert(6, 10) is True

    def test_below(self):
        assert recent_worsening_rate_alert(3, 10) is False

    def test_empty(self):
        assert recent_worsening_rate_alert(0, 0) is False
