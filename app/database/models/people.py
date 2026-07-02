"""People (HR) module schema: Department, Employee, TimeOffRequest."""
from __future__ import annotations

import enum
from datetime import date

from sqlalchemy import Date, Enum, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base
from app.database.models.core import TimestampMixin


class EmploymentStatus(str, enum.Enum):
    ACTIVE = "active"
    ON_LEAVE = "on_leave"
    TERMINATED = "terminated"


class TimeOffType(str, enum.Enum):
    VACATION = "vacation"
    SICK = "sick"
    PERSONAL = "personal"
    UNPAID = "unpaid"


class TimeOffStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class Department(TimestampMixin, Base):
    __tablename__ = "people_departments"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(10), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(120))
    cost_center: Mapped[str] = mapped_column(String(20))


class Employee(TimestampMixin, Base):
    __tablename__ = "people_employees"

    id: Mapped[int] = mapped_column(primary_key=True)
    employee_code: Mapped[str] = mapped_column(String(15), unique=True, index=True)
    full_name: Mapped[str] = mapped_column(String(150))
    department_id: Mapped[int] = mapped_column(ForeignKey("people_departments.id"), index=True)
    location_id: Mapped[int] = mapped_column(ForeignKey("locations.id"))
    job_title: Mapped[str] = mapped_column(String(100))
    hire_date: Mapped[date] = mapped_column(Date)
    employment_status: Mapped[EmploymentStatus] = mapped_column(
        Enum(EmploymentStatus), default=EmploymentStatus.ACTIVE
    )
    base_salary: Mapped[float] = mapped_column(Numeric(10, 2))


class TimeOffRequest(Base):
    __tablename__ = "people_timeoff_requests"

    id: Mapped[int] = mapped_column(primary_key=True)
    employee_id: Mapped[int] = mapped_column(ForeignKey("people_employees.id"), index=True)
    request_type: Mapped[TimeOffType] = mapped_column(Enum(TimeOffType))
    start_date: Mapped[date] = mapped_column(Date)
    end_date: Mapped[date] = mapped_column(Date)
    status: Mapped[TimeOffStatus] = mapped_column(Enum(TimeOffStatus), default=TimeOffStatus.PENDING)
