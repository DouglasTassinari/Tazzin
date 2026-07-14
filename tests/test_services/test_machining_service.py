"""Tests for the Machining service layer."""
from datetime import date, time

import pytest

from app.core.exceptions import ValidationError
from app.database.models.machining import Machine, OccurrenceCategory, OccurrenceType, Operator
from app.database.models.people import Department, Employee, EmploymentStatus
from app.database.models.production import ProductionLine
from app.services.machining_service import MachiningService


@pytest.fixture()
def department(session):
    dept = Department(code="MFG", name="Manufacturing", cost_center="CC-200")
    session.add(dept)
    session.flush()
    return dept


@pytest.fixture()
def employee(session, location, department):
    emp = Employee(
        employee_code="EMP-00001", full_name="Test Operator",
        department_id=department.id, location_id=location.id,
        job_title="CNC Operator", hire_date=date(2020, 1, 1),
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
    op = Operator(employee_id=employee.id, code="OP-01", name="Test Operator", shift=1)
    session.add(op)
    session.flush()
    return op


@pytest.fixture()
def prod_occurrence(session):
    occ = OccurrenceType(
        code="PRODUCAO", description="Produção",
        category=OccurrenceCategory.PRODUCTIVE, impacts_efficiency=True, impacts_oee=True,
    )
    session.add(occ)
    session.flush()
    return occ


@pytest.fixture()
def setup_occurrence(session):
    occ = OccurrenceType(
        code="SETUP_1H", description="Setup 1h",
        category=OccurrenceCategory.SEMI_PRODUCTIVE,
    )
    session.add(occ)
    session.flush()
    return occ


def test_create_appointment(session, machine, operator, prod_occurrence):
    svc = MachiningService(session)
    appt = svc.create_appointment(
        appointment_date=date(2026, 6, 1),
        machine_id=machine.id,
        operator_id=operator.id,
        occurrence_type_id=prod_occurrence.id,
        start_time=time(8, 0),
        end_time=time(9, 30),
        duration_minutes=90,
        quantity=50,
        efficiency_pct=95.0,
        total_production=50,
    )
    assert appt.id is not None
    assert appt.quantity == 50


def test_create_appointment_rejects_negative(session, machine, operator, prod_occurrence):
    svc = MachiningService(session)
    with pytest.raises(ValidationError):
        svc.create_appointment(
            appointment_date=date(2026, 6, 1),
            machine_id=machine.id,
            operator_id=operator.id,
            occurrence_type_id=prod_occurrence.id,
            start_time=time(8, 0),
            end_time=time(9, 0),
            duration_minutes=-10,
            quantity=0,
        )


def test_operator_yield_ranking(session, machine, operator, prod_occurrence):
    svc = MachiningService(session)
    svc.create_appointment(
        appointment_date=date(2026, 6, 1),
        machine_id=machine.id,
        operator_id=operator.id,
        occurrence_type_id=prod_occurrence.id,
        start_time=time(8, 0),
        end_time=time(10, 0),
        duration_minutes=120,
        quantity=80,
        efficiency_pct=92.0,
        total_production=80,
    )
    ranking = svc.operator_yield_ranking(date(2026, 6, 1), date(2026, 6, 30))
    assert len(ranking) == 1
    assert ranking[0][0] == "Test Operator"
    assert ranking[0][2] == 80


def test_time_by_category(session, machine, operator, prod_occurrence, setup_occurrence):
    svc = MachiningService(session)
    svc.create_appointment(
        appointment_date=date(2026, 6, 1),
        machine_id=machine.id, operator_id=operator.id,
        occurrence_type_id=prod_occurrence.id,
        start_time=time(8, 0), end_time=time(10, 0),
        duration_minutes=120, quantity=50, total_production=50,
    )
    svc.create_appointment(
        appointment_date=date(2026, 6, 1),
        machine_id=machine.id, operator_id=operator.id,
        occurrence_type_id=setup_occurrence.id,
        start_time=time(10, 0), end_time=time(11, 0),
        duration_minutes=60,
    )
    cats = dict(svc.time_by_category(date(2026, 6, 1), date(2026, 6, 30)))
    assert cats["productive"] == 2.0
    assert cats["semi_productive"] == 1.0
