from datetime import date

from app.database.models.people import (
    Department,
    Employee,
    EmploymentStatus,
    TimeOffRequest,
    TimeOffStatus,
    TimeOffType,
)
from app.repositories.people_repository import EmployeeRepository, TimeOffRequestRepository


def _make_department(session, code: str = "ENG") -> Department:
    department = Department(code=code, name="Engineering", cost_center="CC-100")
    session.add(department)
    session.flush()
    return department


def _make_employee(session, department, location, status=EmploymentStatus.ACTIVE, code="EMP-1") -> Employee:
    employee = Employee(
        employee_code=code,
        full_name="Jane Doe",
        department_id=department.id,
        location_id=location.id,
        job_title="Engineer",
        hire_date=date(2025, 1, 1),
        employment_status=status,
        base_salary=5000,
    )
    session.add(employee)
    session.flush()
    return employee


def test_active_employees_excludes_terminated(session, location):
    department = _make_department(session)
    active = _make_employee(session, department, location, code="EMP-1")
    _make_employee(session, department, location, status=EmploymentStatus.TERMINATED, code="EMP-2")

    repo = EmployeeRepository(session)
    result = repo.active_employees()

    assert [e.id for e in result] == [active.id]


def test_headcount_by_department_orders_desc(session, location):
    eng = _make_department(session, code="ENG")
    sales = Department(code="SLS", name="Sales", cost_center="CC-200")
    session.add(sales)
    session.flush()

    _make_employee(session, eng, location, code="EMP-1")
    _make_employee(session, eng, location, code="EMP-2")
    _make_employee(session, sales, location, code="EMP-3")

    repo = EmployeeRepository(session)
    rows = repo.headcount_by_department()

    assert rows == [("Engineering", 2), ("Sales", 1)]


def test_pending_requests_only_returns_pending(session, location):
    department = _make_department(session)
    employee = _make_employee(session, department, location)

    pending = TimeOffRequest(
        employee_id=employee.id,
        request_type=TimeOffType.VACATION,
        start_date=date(2026, 2, 1),
        end_date=date(2026, 2, 5),
        status=TimeOffStatus.PENDING,
    )
    approved = TimeOffRequest(
        employee_id=employee.id,
        request_type=TimeOffType.SICK,
        start_date=date(2026, 2, 10),
        end_date=date(2026, 2, 11),
        status=TimeOffStatus.APPROVED,
    )
    session.add_all([pending, approved])
    session.flush()

    repo = TimeOffRequestRepository(session)
    result = repo.pending_requests()

    assert [r.id for r in result] == [pending.id]


def test_approved_days_by_month_sums_inclusive_days(session, location):
    department = _make_department(session)
    employee = _make_employee(session, department, location)

    approved = TimeOffRequest(
        employee_id=employee.id,
        request_type=TimeOffType.VACATION,
        start_date=date(2026, 3, 1),
        end_date=date(2026, 3, 5),
        status=TimeOffStatus.APPROVED,
    )
    rejected = TimeOffRequest(
        employee_id=employee.id,
        request_type=TimeOffType.PERSONAL,
        start_date=date(2026, 3, 10),
        end_date=date(2026, 3, 12),
        status=TimeOffStatus.REJECTED,
    )
    session.add_all([approved, rejected])
    session.flush()

    repo = TimeOffRequestRepository(session)
    rows = repo.approved_days_by_month(date(2026, 3, 1), date(2026, 3, 31))

    assert rows == [("2026-03", 5)]  # Mar 1-5 inclusive
