"""Tests for scrap domain rules."""
from __future__ import annotations

import pytest

from app.core.exceptions import ValidationError
from app.domain.scrap_rules import (
    check_concentration,
    check_monthly_trend,
    exceeds_rnc_threshold,
    scrap_origin,
    total_quantity,
    validate_scrap_record,
)


class TestValidation:
    def test_empty_reason(self):
        with pytest.raises(ValidationError):
            validate_scrap_record("", 1, None, None, None, None)

    def test_zero_quantity(self):
        with pytest.raises(ValidationError):
            validate_scrap_record("Trinca", 0, None, None, None, None)

    def test_reason2_without_quantity(self):
        with pytest.raises(ValidationError):
            validate_scrap_record("Trinca", 1, "Porosidade", None, None, None)

    def test_valid(self):
        validate_scrap_record("Trinca", 3, "Porosidade", 2, None, None)


class TestTotalQuantity:
    def test_all_three(self):
        assert total_quantity(3, 2, 1) == 6

    def test_only_first(self):
        assert total_quantity(5, None, None) == 5


class TestScrapOrigin:
    def test_machining(self):
        assert scrap_origin("Dimensional Errado Usinagem") == "usinagem"

    def test_undefined(self):
        assert scrap_origin("Outros") == "indefinido"

    def test_supplier(self):
        assert scrap_origin("Trinca na Fundição") == "fornecedor"
        assert scrap_origin("Porosidade") == "fornecedor"


class TestRNC:
    def test_at_threshold(self):
        assert exceeds_rnc_threshold(5, 100) is True

    def test_below(self):
        assert exceeds_rnc_threshold(4, 100) is False


class TestConcentration:
    def test_above(self):
        counts = {"A": 50, "B": 30, "C": 20}
        assert check_concentration(counts, 40) == ["A"]

    def test_none(self):
        counts = {"A": 30, "B": 35, "C": 35}
        assert check_concentration(counts, 40) == []

    def test_empty(self):
        assert check_concentration({}, 40) == []


class TestMonthlyTrend:
    def test_above_threshold(self):
        assert check_monthly_trend(120, 100) is True

    def test_below(self):
        assert check_monthly_trend(110, 100) is False

    def test_zero_average(self):
        assert check_monthly_trend(1, 0) is True
