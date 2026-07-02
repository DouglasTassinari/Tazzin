"""Pure business rules for the People module — no database, no I/O.

Kept separate from :mod:`app.services.people_service` so the rules can be
unit tested with plain Python objects and reused (e.g. by a future API
layer) without pulling in a database session.
"""
from __future__ import annotations

from datetime import date

from app.core.exceptions import ValidationError
from app.database.models.people import TimeOffStatus


def validate_date_range(start_date: date, end_date: date) -> None:
    if end_date < start_date:
        raise ValidationError(f"End date {end_date} cannot be before start date {start_date}")


def validate_salary(base_salary: float) -> None:
    if base_salary <= 0:
        raise ValidationError(f"Base salary must be positive, got {base_salary}")


def assert_can_decide(status: TimeOffStatus) -> None:
    if status != TimeOffStatus.PENDING:
        raise ValidationError(f"Cannot decide a time off request in {status.value} status")
