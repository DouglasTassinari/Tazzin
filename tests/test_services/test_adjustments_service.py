"""Tests for the Adjustments service layer."""
from datetime import date, datetime

import pytest

from app.core.exceptions import ValidationError
from app.database.models.machining import Machine, Operator
from app.database.models.people import Department, Employee, EmploymentStatus
from app.database.models.production import ProductionLine
from app.services.adjustments_service import AdjustmentsService


@pytest.fixture()
def department(session):
    dept = Department(code="MFG", name="Manufacturing", cost_center="CC-200")
    session.add(dept)
    session.flush()
    return dept


@pytest.fixture()
def employee(session, location, department):
    emp = Employee(
        employee_code="EMP-00001", full_name="Test Op",
        department_id=department.id, location_id=location.id,
        job_title="Operator", hire_date=date(2020, 1, 1),
        employment_status=EmploymentStatus.ACTIVE, base_salary=3500,
    )
    session.add(emp)
    session.flush()
    return emp


@pytest.fixture()
def production_line(session, location):
    line = ProductionLine(code="LINE-1", name="Line 1", location_id=location.id, capacity_units_per_hour=100)
    session.add(line)
    session.flush()
    return line


@pytest.fixture()
def machine(session, production_line):
    m = Machine(code="CNC-01", name="Torno CNC 01", production_line_id=production_line.id)
    session.add(m)
    session.flush()
    return m


@pytest.fixture()
def operator(session, employee):
    op = Operator(employee_id=employee.id, code="OP-01", name="Test Op", shift=1)
    session.add(op)
    session.flush()
    return op


def test_create_improvement(session, operator, machine):
    svc = AdjustmentsService(session)
    adj = svc.create_adjustment(
        record_date=datetime(2026, 6, 1, 10, 0),
        operator_id=operator.id,
        machine_id=machine.id,
        operation="Lado 1",
        previous_time_seconds=120,
        current_time_seconds=90,
        justification="Better tooling",
    )
    assert adj.id is not None
    assert adj.is_improvement is True
    assert adj.difference_seconds == 30


def test_create_worsening(session, operator, machine):
    svc = AdjustmentsService(session)
    adj = svc.create_adjustment(
        record_date=datetime(2026, 6, 1, 10, 0),
        operator_id=operator.id,
        machine_id=machine.id,
        operation="Furação",
        previous_time_seconds=90,
        current_time_seconds=120,
        justification="Harder material",
    )
    assert adj.is_improvement is False


def test_reject_same_time(session, operator, machine):
    svc = AdjustmentsService(session)
    with pytest.raises(ValidationError):
        svc.create_adjustment(
            record_date=datetime(2026, 6, 1, 10, 0),
            operator_id=operator.id,
            machine_id=machine.id,
            operation="Lado 1",
            previous_time_seconds=100,
            current_time_seconds=100,
            justification="test",
        )


def test_by_operator(session, operator, machine):
    svc = AdjustmentsService(session)
    svc.create_adjustment(datetime(2026, 6, 1, 10, 0), operator.id, machine.id, "Op1", 120, 90, "Better")
    svc.create_adjustment(datetime(2026, 6, 2, 10, 0), operator.id, machine.id, "Op2", 100, 110, "Worse")
    rows = svc.by_operator(date(2026, 6, 1), date(2026, 6, 30))
    assert len(rows) == 1
    name, imp, wor, net = rows[0]
    assert name == "Test Op"
    assert imp == 1
    assert wor == 1
    assert net == 20.0  # 30 saved - 10 lost
