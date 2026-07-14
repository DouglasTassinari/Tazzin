"""Pure business rules for the Scrap (Refugo) module — no database, no I/O.

Alert thresholds and origin classification from the Acriflex industrial BI.
"""
from __future__ import annotations

from app.core.exceptions import ValidationError

RNC_LOT_THRESHOLD_PCT = 5.0
CONCENTRATION_REASON_PCT = 40.0
CONCENTRATION_MACHINE_PCT = 40.0
CONCENTRATION_SUPPLIER_PCT = 60.0
MONTHLY_TREND_PCT = 20.0

MACHINING_REASONS = {"Dimensional Errado Usinagem"}
UNDEFINED_REASONS = {"Outros"}


def validate_scrap_record(
    reason_1: str, quantity_1: int,
    reason_2: str | None, quantity_2: int | None,
    reason_3: str | None, quantity_3: int | None,
) -> None:
    if not reason_1 or not reason_1.strip():
        raise ValidationError("At least one scrap reason is required")
    if quantity_1 < 1:
        raise ValidationError("Quantity for reason 1 must be at least 1")
    if reason_2 and (quantity_2 is None or quantity_2 < 1):
        raise ValidationError("Quantity for reason 2 must be at least 1 when reason is provided")
    if reason_3 and (quantity_3 is None or quantity_3 < 1):
        raise ValidationError("Quantity for reason 3 must be at least 1 when reason is provided")


def total_quantity(q1: int, q2: int | None, q3: int | None) -> int:
    return q1 + (q2 or 0) + (q3 or 0)


def scrap_origin(reason: str) -> str:
    """R34: classify a scrap reason as usinagem, fornecedor or indefinido."""
    r = reason.strip()
    if r in MACHINING_REASONS:
        return "usinagem"
    if r in UNDEFINED_REASONS:
        return "indefinido"
    return "fornecedor"


def exceeds_rnc_threshold(scrap_qty: int, lot_qty: int) -> bool:
    if lot_qty <= 0:
        return False
    return (scrap_qty / lot_qty) * 100 >= RNC_LOT_THRESHOLD_PCT


def check_concentration(counts: dict[str, int], threshold_pct: float) -> list[str]:
    """Return items whose share >= threshold_pct of the total."""
    total = sum(counts.values())
    if total <= 0:
        return []
    return [k for k, v in counts.items() if (v / total) * 100 >= threshold_pct]


def check_monthly_trend(current_month_qty: int, average_qty: float) -> bool:
    """True if current month is >= MONTHLY_TREND_PCT above average."""
    if average_qty <= 0:
        return current_month_qty > 0
    return ((current_month_qty - average_qty) / average_qty) * 100 >= MONTHLY_TREND_PCT
