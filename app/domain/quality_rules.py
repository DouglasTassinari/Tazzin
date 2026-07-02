"""Pure business rules for the Quality module — no database, no I/O.

Kept separate from :mod:`app.services.quality_service` so the rules can be
unit tested with plain Python objects and reused without pulling in a
database session.
"""
from __future__ import annotations

from app.core.exceptions import ValidationError
from app.database.models.quality import NonConformanceStatus

_ALLOWED_TRANSITIONS: dict[NonConformanceStatus, set[NonConformanceStatus]] = {
    NonConformanceStatus.OPEN: {NonConformanceStatus.UNDER_REVIEW, NonConformanceStatus.CLOSED},
    NonConformanceStatus.UNDER_REVIEW: {NonConformanceStatus.RESOLVED, NonConformanceStatus.CLOSED},
    NonConformanceStatus.RESOLVED: {NonConformanceStatus.CLOSED},
    NonConformanceStatus.CLOSED: set(),
}


def validate_inspection(sample_size: int, defect_count: int) -> None:
    if sample_size <= 0:
        raise ValidationError(f"Sample size must be positive, got {sample_size}")
    if defect_count < 0 or defect_count > sample_size:
        raise ValidationError(
            f"Defect count must be between 0 and {sample_size}, got {defect_count}"
        )


def defect_rate(sample_size: int, defect_count: int) -> float:
    if sample_size == 0:
        return 0.0
    return round(100.0 * defect_count / sample_size, 2)


def can_transition(current: NonConformanceStatus, target: NonConformanceStatus) -> bool:
    return target in _ALLOWED_TRANSITIONS.get(current, set())


def assert_transition(current: NonConformanceStatus, target: NonConformanceStatus) -> None:
    if not can_transition(current, target):
        raise ValidationError(
            f"Cannot move nonconformance from {current.value} to {target.value}"
        )
