"""Pure business rules for the Time Adjustments (Ajustes) module — no database, no I/O."""
from __future__ import annotations

from app.core.exceptions import ValidationError

MINIMUM_ADJUSTMENTS_OPERATOR = 3
MINIMUM_ADJUSTMENTS_MACHINE = 3
RECENT_WORSENING_THRESHOLD_PCT = 50.0


def validate_adjustment(
    previous_seconds: float,
    current_seconds: float,
    justification: str,
) -> None:
    if previous_seconds < 0 or current_seconds < 0:
        raise ValidationError("Time values must not be negative")
    if previous_seconds == current_seconds:
        raise ValidationError("Previous and current times must differ")
    if not justification or not justification.strip():
        raise ValidationError("Justification is required")


def difference_seconds(previous: float, current: float) -> float:
    """Positive = improvement (time saved), negative = worsening."""
    return previous - current


def is_improvement(previous: float, current: float) -> bool:
    return previous > current


def lot_impact_seconds(diff_seconds: float, lot_quantity: float) -> float:
    """Total time saved (or lost) across the lot."""
    return round(diff_seconds * lot_quantity, 2)


def operator_has_too_many_worsenings(improvements: int, worsenings: int) -> bool:
    if improvements + worsenings < MINIMUM_ADJUSTMENTS_OPERATOR:
        return False
    return worsenings > improvements


def machine_is_worsening(improvements: int, worsenings: int) -> bool:
    if improvements + worsenings < MINIMUM_ADJUSTMENTS_MACHINE:
        return False
    return worsenings > improvements


def recent_worsening_rate_alert(worsenings: int, total: int) -> bool:
    if total <= 0:
        return False
    return (worsenings / total) * 100 >= RECENT_WORSENING_THRESHOLD_PCT
