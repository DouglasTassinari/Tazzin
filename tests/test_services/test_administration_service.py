import pytest

from app.core.exceptions import ValidationError
from app.services.administration_service import AdministrationService


def test_create_user_persists_and_validates(session):
    service = AdministrationService(session)
    role = service.create_role("VIEWER", "Viewer")

    user = service.create_user("analyst1", "analyst1@example.com", role.id)
    assert user.id is not None
    assert service.active_users() == [user]

    with pytest.raises(ValidationError):
        service.create_user("ab", "bad@example.com", role.id)


def test_record_audit_event_and_recent(session):
    service = AdministrationService(session)
    service.record_audit_event("create", "Project", 42, detail="seeded")

    events = service.recent_audit_events()
    assert len(events) == 1
    assert events[0].entity_name == "Project"


def test_system_health_and_metrics(session):
    service = AdministrationService(session)
    report = service.system_health()
    assert report.healthy is True
    assert {c.name for c in report.checks} == {"database", "log_directory"}

    snapshot = service.system_metrics()
    assert "uptime_seconds" in snapshot
    assert "operations" in snapshot
