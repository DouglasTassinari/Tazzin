"""Pure business rules for the Administration module — no database, no I/O."""
from __future__ import annotations

from app.core.exceptions import ValidationError

MIN_USERNAME_LENGTH = 3


def validate_username(username: str) -> None:
    if len(username) < MIN_USERNAME_LENGTH:
        raise ValidationError(f"Username must be at least {MIN_USERNAME_LENGTH} characters")


def validate_email(email: str) -> None:
    if "@" not in email or "." not in email.split("@")[-1]:
        raise ValidationError(f"Invalid email address: {email!r}")
