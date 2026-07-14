"""Pure business rules for the Machining (Usinagem) module — no database, no I/O.

Core formulas from the industrial BI: weighted yield, time breakdown,
occurrence classification, setup productivity and meritocracy index.
"""
from __future__ import annotations

from app.core.exceptions import ValidationError

DAILY_SHIFT_HOURS = 8.8
YIELD_TARGET_PCT = 85.0
EFFICIENCY_CAP_RECORD = 500.0
EFFICIENCY_CAP_KPI = 200.0
SETUP_META_FACTOR = 0.85
MERITOCRACY_LIMIT_PCT = 7.0
COFFEE_BREAK_MINUTES = 25
RNC_LOT_THRESHOLD_PCT = 5.0

PRODUCTIVE_OCCURRENCES = {"PRODUCAO"}
SEMI_PRODUCTIVE_OCCURRENCES = {
    "SETUP 30MIN", "SETUP 1H", "SETUP 1H30", "SETUP 2H",
    "SETUP 2H30", "SETUP 3H", "SETUP 5H",
}
NO_PART_OCCURRENCES = {"SEM PEÇA", "ESPERANDO PEÇA"}

SETUP_STANDARD_MINUTES: dict[str, float] = {
    "SETUP 30MIN": 30, "SETUP 1H": 60, "SETUP 1H30": 90,
    "SETUP 2H": 120, "SETUP 2H30": 150, "SETUP 3H": 180, "SETUP 5H": 300,
}


def classify_occurrence(description: str) -> str:
    desc = description.strip().upper()
    if desc in PRODUCTIVE_OCCURRENCES:
        return "productive"
    if desc in SEMI_PRODUCTIVE_OCCURRENCES:
        return "semi_productive"
    if desc in NO_PART_OCCURRENCES:
        return "no_part"
    return "unproductive"


def weighted_yield(records: list[tuple[float, float, float]]) -> float:
    """Weighted yield from (quantity, total_production_day, efficiency_pct) tuples.

    R17: weight = quantity / total_production_day
         result = min(efficiency, 500) * weight
         yield  = sum(result) / 100
    """
    if not records:
        return 0.0
    total = 0.0
    for quantity, total_prod, efficiency in records:
        if total_prod <= 0:
            continue
        weight = quantity / total_prod
        total += min(efficiency, EFFICIENCY_CAP_RECORD) * weight
    return min(round(total / 100, 4) * 100, EFFICIENCY_CAP_KPI)


def monthly_weighted_yield(daily: list[tuple[float, float]]) -> float:
    """Monthly yield weighted by production hours. R17 step 4.

    daily = list of (daily_yield_pct, production_hours)
    """
    total_weight = sum(h for _, h in daily)
    if total_weight <= 0:
        return 0.0
    weighted = sum(y * h for y, h in daily)
    return min(round(weighted / total_weight, 2), EFFICIENCY_CAP_KPI)


def time_breakdown(
    production_min: float,
    setup_min: float,
    no_part_min: float,
    stops_min: float,
    available_min: float,
) -> dict[str, float]:
    """Five-slice time breakdown as percentages of available time."""
    if available_min <= 0:
        return {"production": 0, "setup": 0, "no_part": 0, "stops": 0, "operator_loss": 0}
    accounted = production_min + setup_min + no_part_min + stops_min
    operator_loss = max(available_min - accounted, 0)
    return {
        "production": round(100 * production_min / available_min, 1),
        "setup": round(100 * setup_min / available_min, 1),
        "no_part": round(100 * no_part_min / available_min, 1),
        "stops": round(100 * stops_min / available_min, 1),
        "operator_loss": round(100 * operator_loss / available_min, 1),
    }


def setup_standard_minutes(occurrence_desc: str) -> float | None:
    return SETUP_STANDARD_MINUTES.get(occurrence_desc.strip().upper())


def setup_productivity(standard_min: float, actual_min: float) -> float:
    """Setup productivity with the 85% meta factor applied to the standard."""
    if actual_min <= 0:
        return 0.0
    adjusted = standard_min * SETUP_META_FACTOR
    return round(100 * adjusted / actual_min, 1)


def meritocracy_index(idle_hours: float, unjustified_absence_hours: float, expected_hours: float) -> float:
    """R38: (idle + unjustified_absence) / expected * 100."""
    if expected_hours <= 0:
        return 0.0
    return round(100 * (idle_hours + unjustified_absence_hours) / expected_hours, 2)


def passes_meritocracy(index: float) -> bool:
    return index <= MERITOCRACY_LIMIT_PCT


def idle_time_hours(presence_hours: float, covered_hours: float) -> float:
    """R36: idle = presence - covered - coffee_break, floor 0."""
    coffee_hours = COFFEE_BREAK_MINUTES / 60
    return max(presence_hours - covered_hours - coffee_hours, 0.0)


def validate_appointment(duration_minutes: float, quantity: int) -> None:
    if duration_minutes < 0:
        raise ValidationError("Duration must not be negative")
    if quantity < 0:
        raise ValidationError("Quantity must not be negative")


def exceeds_rnc_threshold(scrap_qty: int, lot_qty: int) -> bool:
    """R33: scrap >= 5% of lot estimate triggers RNC."""
    if lot_qty <= 0:
        return False
    return (scrap_qty / lot_qty) * 100 >= RNC_LOT_THRESHOLD_PCT
