from datetime import date

import pytest

from app.core.exceptions import EntityNotFoundError, ValidationError
from app.database.models.people import Department, TimeOffStatus, TimeOffType
from app.services.people_service import PeopleService


def _make_department(session) -> Department:
    department = Department(code="ENG", name="Engineering", cost_center="CC-100")
    session.add(department)
    session.flush()
    return department


def test_hire_employee_persists_as_active(session, location):
    department = _make_department(session)
    service = PeopleService(session)

    employee = service.hire_employee(
        employee_code="EMP-100",
        full_name="John Smith",
        department_id=department.id,
        location_id=location.id,
        job_title="Engineer",
        hire_date=date(2026, 1, 1),
        base_salary=6000,
    )

    assert employee.id is not None
    assert employee.employment_status.value == "active"


def test_hire_employee_rejects_non_positive_salary(session, location):
    department = _make_department(session)
    service = PeopleService(session)

    with pytest.raises(ValidationError):
        service.hire_employee(
            employee_code="EMP-101",
            full_name="Jane Roe",
            department_id=department.id,
            location_id=location.id,
            job_title="Engineer",
            hire_date=date(2026, 1, 1),
            base_salary=0,
        )


def test_request_time_off_persists_as_pending(session, location):
    department = _make_department(session)
    service = PeopleService(session)
    employee = service.hire_employee(
        employee_code="EMP-102",
        full_name="Ana Lima",
        department_id=department.id,
        location_id=location.id,
        job_title="Engineer",
        hire_date=date(2026, 1, 1),
        base_salary=6000,
    )

    request = service.request_time_off(
        employee_id=employee.id,
        request_type=TimeOffType.VACATION,
        start_date=date(2026, 4, 1),
        end_date=date(2026, 4, 5),
    )

    assert request.id is not None
    assert request.status == TimeOffStatus.PENDING


def test_request_time_off_rejects_invalid_range(session, location):
    department = _make_department(session)
    service = PeopleService(session)
    employee = service.hire_employee(
        employee_code="EMP-103",
        full_name="Bob King",
        department_id=department.id,
        location_id=location.id,
        job_title="Engineer",
        hire_date=date(2026, 1, 1),
        base_salary=6000,
    )

    with pytest.raises(ValidationError):
        service.request_time_off(
            employee_id=employee.id,
            request_type=TimeOffType.SICK,
            start_date=date(2026, 4, 10),
            end_date=date(2026, 4, 1),
        )


def test_decide_time_off_approves_pending_request(session, location):
    department = _make_department(session)
    service = PeopleService(session)
    employee = service.hire_employee(
        employee_code="EMP-104",
        full_name="Cara Diaz",
        department_id=department.id,
        location_id=location.id,
        job_title="Engineer",
        hire_date=date(2026, 1, 1),
        base_salary=6000,
    )
    request = service.request_time_off(
        employee_id=employee.id,
        request_type=TimeOffType.PERSONAL,
        start_date=date(2026, 5, 1),
        end_date=date(2026, 5, 2),
    )

    decided = service.decide_time_off(request.id, approve=True)
    assert decided.status == TimeOffStatus.APPROVED

    with pytest.raises(ValidationError):
        service.decide_time_off(request.id, approve=False)


def test_decide_time_off_unknown_request_raises_not_found(session):
    service = PeopleService(session)
    with pytest.raises(EntityNotFoundError):
        service.decide_time_off(999, approve=True)
