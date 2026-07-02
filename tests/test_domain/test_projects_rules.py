from datetime import date

import pytest

from app.core.exceptions import ValidationError
from app.database.models.projects import ProjectStatus
from app.domain import projects_rules


def test_validate_budget_accepts_positive():
    projects_rules.validate_budget(1000)


def test_validate_budget_rejects_non_positive():
    with pytest.raises(ValidationError):
        projects_rules.validate_budget(0)
    with pytest.raises(ValidationError):
        projects_rules.validate_budget(-1)


def test_validate_dates_requires_end_after_start():
    projects_rules.validate_dates(date(2026, 1, 1), date(2026, 2, 1))
    with pytest.raises(ValidationError):
        projects_rules.validate_dates(date(2026, 1, 1), date(2026, 1, 1))
    with pytest.raises(ValidationError):
        projects_rules.validate_dates(date(2026, 2, 1), date(2026, 1, 1))


def test_completion_rate_avoids_division_by_zero():
    assert projects_rules.completion_rate(0, 0) == 0.0


def test_completion_rate_computes_percentage():
    assert projects_rules.completion_rate(1, 4) == 25.0


def test_allowed_transition_path():
    assert projects_rules.can_transition(ProjectStatus.PLANNING, ProjectStatus.ACTIVE)
    assert projects_rules.can_transition(ProjectStatus.ACTIVE, ProjectStatus.ON_HOLD)
    assert projects_rules.can_transition(ProjectStatus.ON_HOLD, ProjectStatus.ACTIVE)


def test_disallowed_transition_raises():
    with pytest.raises(ValidationError):
        projects_rules.assert_transition(ProjectStatus.PLANNING, ProjectStatus.COMPLETED)
    with pytest.raises(ValidationError):
        projects_rules.assert_transition(ProjectStatus.COMPLETED, ProjectStatus.ACTIVE)
