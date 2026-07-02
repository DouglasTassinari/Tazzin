"""Data access for the People module."""
from __future__ import annotations

from collections import defaultdict
from datetime import date

from sqlalchemy import func, select

from app.database.models.people import (
    Department,
    Employee,
    EmploymentStatus,
    TimeOffRequest,
    TimeOffStatus,
)
from app.repositories.base import BaseRepository


class DepartmentRepository(BaseRepository[Department]):
    model = Department


class EmployeeRepository(BaseRepository[Employee]):
    model = Employee

    def active_employees(self) -> list[Employee]:
        stmt = select(Employee).where(Employee.employment_status == EmploymentStatus.ACTIVE)
        return list(self.session.execute(stmt).scalars().all())

    def headcount_by_department(self) -> list[tuple[str, int]]:
        stmt = (
            select(Department.name, func.count(Employee.id))
            .join(Employee, Employee.department_id == Department.id)
            .where(Employee.employment_status == EmploymentStatus.ACTIVE)
            .group_by(Department.id)
            .order_by(func.count(Employee.id).desc())
        )
        return [(name, int(count)) for name, count in self.session.execute(stmt).all()]


class TimeOffRequestRepository(BaseRepository[TimeOffRequest]):
    model = TimeOffRequest

    def requests_between(self, start: date, end: date) -> list[TimeOffRequest]:
        stmt = select(TimeOffRequest).where(
            TimeOffRequest.start_date >= start, TimeOffRequest.start_date <= end
        )
        return list(self.session.execute(stmt).scalars().all())

    def pending_requests(self) -> list[TimeOffRequest]:
        stmt = select(TimeOffRequest).where(TimeOffRequest.status == TimeOffStatus.PENDING)
        return list(self.session.execute(stmt).scalars().all())

    def approved_days_by_month(self, start: date, end: date) -> list[tuple[str, int]]:
        """Total approved time off days per calendar month, keyed by request start date."""
        rows = self.requests_between(start, end)
        totals: dict[str, int] = defaultdict(int)
        for request in rows:
            if request.status != TimeOffStatus.APPROVED:
                continue
            month = request.start_date.strftime("%Y-%m")
            totals[month] += (request.end_date - request.start_date).days + 1
        return sorted(totals.items())
