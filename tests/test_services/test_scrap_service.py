"""Tests for the Scrap service layer."""
from datetime import date

import pytest

from app.core.exceptions import ValidationError
from app.database.models.machining import Machine, Operator
from app.database.models.people import Department, Employee, EmploymentStatus
from app.database.models.production import ProductionLine
from app.services.scrap_service import ScrapService


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


def test_create_record(session, operator, machine):
    svc = ScrapService(session)
    rec = svc.create_record(
        record_date=date(2026, 6, 1),
        operator_id=operator.id,
        machine_id=machine.id,
        reason_1="Trinca na Fundição",
        quantity_1=3,
    )
    assert rec.id is not None
    assert rec.total_quantity == 3


def test_create_record_with_multiple_reasons(session, operator, machine):
    svc = ScrapService(session)
    rec = svc.create_record(
        record_date=date(2026, 6, 1),
        operator_id=operator.id,
        machine_id=machine.id,
        reason_1="Trinca na Fundição",
        quantity_1=3,
        reason_2="Porosidade",
        quantity_2=2,
    )
    assert rec.total_quantity == 5


def test_invalid_record_rejected(session, operator, machine):
    svc = ScrapService(session)
    with pytest.raises(ValidationError):
        svc.create_record(
            record_date=date(2026, 6, 1),
            operator_id=operator.id,
            machine_id=machine.id,
            reason_1="",
            quantity_1=1,
        )


def test_total_in_period(session, operator, machine):
    svc = ScrapService(session)
    svc.create_record(date(2026, 6, 1), operator.id, machine.id, "Trinca", 3)
    svc.create_record(date(2026, 6, 15), operator.id, machine.id, "Porosidade", 5)
    assert svc.total_in_period(date(2026, 6, 1), date(2026, 6, 30)) == 8


def test_by_reason(session, operator, machine):
    svc = ScrapService(session)
    svc.create_record(date(2026, 6, 1), operator.id, machine.id, "Trinca", 3)
    svc.create_record(date(2026, 6, 2), operator.id, machine.id, "Trinca", 2)
    svc.create_record(date(2026, 6, 3), operator.id, machine.id, "Porosidade", 1)
    reasons = dict(svc.by_reason(date(2026, 6, 1), date(2026, 6, 30)))
    assert reasons["Trinca"] == 5
    assert reasons["Porosidade"] == 1
