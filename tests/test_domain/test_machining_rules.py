"""Tests for machining domain rules."""
from __future__ import annotations

import pytest

from app.core.exceptions import ValidationError
from app.domain.machining_rules import (
    EFFICIENCY_CAP_KPI,
    classify_occurrence,
    exceeds_rnc_threshold,
    idle_time_hours,
    meritocracy_index,
    monthly_weighted_yield,
    passes_meritocracy,
    setup_productivity,
    setup_standard_minutes,
    time_breakdown,
    validate_appointment,
    weighted_yield,
)


class TestClassifyOccurrence:
    def test_productive(self):
        assert classify_occurrence("PRODUCAO") == "productive"

    def test_semi_productive(self):
        assert classify_occurrence("SETUP 1H") == "semi_productive"
        assert classify_occurrence("SETUP 30MIN") == "semi_productive"

    def test_no_part(self):
        assert classify_occurrence("SEM PEÇA") == "no_part"
        assert classify_occurrence("ESPERANDO PEÇA") == "no_part"

    def test_unproductive(self):
        assert classify_occurrence("MANUTENCAO") == "unproductive"
        assert classify_occurrence("REUNIAO") == "unproductive"

    def test_strips_whitespace(self):
        assert classify_occurrence("  PRODUCAO  ") == "productive"


class TestWeightedYield:
    def test_empty(self):
        assert weighted_yield([]) == 0.0

    def test_single_record(self):
        result = weighted_yield([(100, 100, 95.0)])
        assert result == pytest.approx(95.0, abs=1)

    def test_capped_at_200(self):
        result = weighted_yield([(100, 100, 600.0)])
        assert result <= EFFICIENCY_CAP_KPI

    def test_zero_production(self):
        assert weighted_yield([(0, 0, 100.0)]) == 0.0


class TestMonthlyWeightedYield:
    def test_weighted(self):
        daily = [(80.0, 4.0), (100.0, 6.0)]
        result = monthly_weighted_yield(daily)
        expected = (80 * 4 + 100 * 6) / 10
        assert result == pytest.approx(expected, abs=0.1)

    def test_empty(self):
        assert monthly_weighted_yield([]) == 0.0


class TestTimeBreakdown:
    def test_normal(self):
        result = time_breakdown(300, 60, 30, 30, 480)
        assert result["production"] == pytest.approx(62.5, abs=0.1)
        assert result["setup"] == pytest.approx(12.5, abs=0.1)

    def test_zero_available(self):
        result = time_breakdown(0, 0, 0, 0, 0)
        assert all(v == 0 for v in result.values())


class TestSetup:
    def test_known_setup(self):
        assert setup_standard_minutes("SETUP 1H") == 60
        assert setup_standard_minutes("SETUP 30MIN") == 30

    def test_unknown(self):
        assert setup_standard_minutes("PRODUCAO") is None

    def test_productivity(self):
        result = setup_productivity(60, 51)
        assert result == pytest.approx(100.0, abs=1)


class TestMeritocracy:
    def test_index(self):
        result = meritocracy_index(2.0, 1.0, 44.0)
        assert result == pytest.approx(6.82, abs=0.1)

    def test_passes(self):
        assert passes_meritocracy(5.0) is True
        assert passes_meritocracy(8.0) is False


class TestIdleTime:
    def test_normal(self):
        result = idle_time_hours(8.0, 7.0)
        expected = 8.0 - 7.0 - 25 / 60
        assert result == pytest.approx(expected, abs=0.01)

    def test_floor_zero(self):
        assert idle_time_hours(1.0, 2.0) == 0.0


class TestRNC:
    def test_threshold(self):
        assert exceeds_rnc_threshold(5, 100) is True
        assert exceeds_rnc_threshold(4, 100) is False

    def test_zero_lot(self):
        assert exceeds_rnc_threshold(5, 0) is False


class TestValidation:
    def test_negative_duration(self):
        with pytest.raises(ValidationError):
            validate_appointment(-1, 0)

    def test_negative_quantity(self):
        with pytest.raises(ValidationError):
            validate_appointment(10, -1)

    def test_valid(self):
        validate_appointment(10, 5)
