import pytest

from app.core.exceptions import ValidationError
from app.domain import administration_rules


def test_validate_username_rejects_too_short():
    with pytest.raises(ValidationError):
        administration_rules.validate_username("ab")
    administration_rules.validate_username("abc")


def test_validate_email_rejects_malformed():
    with pytest.raises(ValidationError):
        administration_rules.validate_email("not-an-email")
    with pytest.raises(ValidationError):
        administration_rules.validate_email("user@nodot")
    administration_rules.validate_email("user@example.com")
