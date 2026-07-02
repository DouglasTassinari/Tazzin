"""People module service — orchestrates repositories + domain rules.

This is the only layer the Streamlit pages talk to for People data; pages
never import repositories or models directly.
"""
from __future__ import annotations

from datetime import date

from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.core.metrics import track
from app.database.models.people import (
    Employee,
    EmploymentStatus,
    TimeOffRequest,
    TimeOffStatus,
    TimeOffType,
)
from app.domain import people_rules
from app.repositories.people_repository import (
    DepartmentRepository,
    EmployeeRepository,
    TimeOffRequestRepository,
)

logger = get_logger("services.people")


class PeopleService:
    def __init__(self, session: Session):
        self.session = session
        self.employees = EmployeeRepository(session)
        self.departments = DepartmentRepository(session)
        self.time_off = TimeOffRequestRepository(session)

    @track("people.hire_employee")
    def hire_employee(
        self,
        employee_code: str,
        full_name: str,
        department_id: int,
        location_id: int,
        job_title: str,
        hire_date: date,
        base_salary: float,
    ) -> Employee:
        people_rules.validate_salary(base_salary)

        employee = Employee(
            employee_code=employee_code,
            full_name=full_name,
            department_id=department_id,
            location_id=location_id,
            job_title=job_title,
            hire_date=hire_date,
            employment_status=EmploymentStatus.ACTIVE,
            base_salary=base_salary,
        )
        self.employees.add(employee)
        logger.info("Hired employee %s (%s)", employee_code, full_name)
        return employee

    @track("people.request_time_off")
    def request_time_off(
        self,
        employee_id: int,
        request_type: TimeOffType,
        start_date: date,
        end_date: date,
    ) -> TimeOffRequest:
        people_rules.validate_date_range(start_date, end_date)

        request = TimeOffRequest(
            employee_id=employee_id,
            request_type=request_type,
            start_date=start_date,
            end_date=end_date,
            status=TimeOffStatus.PENDING,
        )
        self.time_off.add(request)
        logger.info("Employee %s requested %s time off", employee_id, request_type.value)
        return request

    @track("people.decide_time_off")
    def decide_time_off(self, request_id: int, approve: bool) -> TimeOffRequest:
        request = self.time_off.get(request_id)
        people_rules.assert_can_decide(request.status)
        request.status = TimeOffStatus.APPROVED if approve else TimeOffStatus.REJECTED
        self.session.flush()
        logger.info("Time off request %s %s", request_id, request.status.value)
        return request

    @track("people.headcount_report")
    def headcount_report(self) -> list[tuple[str, int]]:
        return self.employees.headcount_by_department()

    @track("people.time_off_utilization")
    def time_off_utilization(self, start: date, end: date) -> list[tuple[str, int]]:
        return self.time_off.approved_days_by_month(start, end)
