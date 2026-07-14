"""Machining (Usinagem) module schema: Machine, Operator, OccurrenceType, Appointment."""
from __future__ import annotations

import enum
from datetime import date, datetime, time

from sqlalchemy import DateTime, Enum, ForeignKey, Numeric, String, Time
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.database.models.core import TimestampMixin


class OccurrenceCategory(str, enum.Enum):
    PRODUCTIVE = "productive"
    SEMI_PRODUCTIVE = "semi_productive"
    UNPRODUCTIVE = "unproductive"


class ShiftNumber(int, enum.Enum):
    MORNING = 1
    AFTERNOON = 2


class Machine(TimestampMixin, Base):
    __tablename__ = "machining_machines"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(120))
    production_line_id: Mapped[int] = mapped_column(
        ForeignKey("production_lines.id"), index=True
    )
    active: Mapped[bool] = mapped_column(default=True)

    appointments: Mapped[list["Appointment"]] = relationship(
        back_populates="machine", cascade="all, delete-orphan"
    )


class OccurrenceType(Base):
    __tablename__ = "machining_occurrence_types"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(40), unique=True, index=True)
    description: Mapped[str] = mapped_column(String(120))
    category: Mapped[OccurrenceCategory] = mapped_column(Enum(OccurrenceCategory))
    impacts_efficiency: Mapped[bool] = mapped_column(default=False)
    impacts_oee: Mapped[bool] = mapped_column(default=False)
    weight: Mapped[float] = mapped_column(Numeric(5, 2), default=1.0)


class Operator(TimestampMixin, Base):
    __tablename__ = "machining_operators"

    id: Mapped[int] = mapped_column(primary_key=True)
    employee_id: Mapped[int] = mapped_column(ForeignKey("people_employees.id"), index=True)
    code: Mapped[str] = mapped_column(String(10), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(120))
    shift: Mapped[int] = mapped_column(default=1)
    active: Mapped[bool] = mapped_column(default=True)

    appointments: Mapped[list["Appointment"]] = relationship(
        back_populates="operator", cascade="all, delete-orphan"
    )


class Appointment(TimestampMixin, Base):
    __tablename__ = "machining_appointments"

    id: Mapped[int] = mapped_column(primary_key=True)
    appointment_date: Mapped[date] = mapped_column(index=True)
    machine_id: Mapped[int] = mapped_column(
        ForeignKey("machining_machines.id"), index=True
    )
    operator_id: Mapped[int] = mapped_column(
        ForeignKey("machining_operators.id"), index=True
    )
    work_order_number: Mapped[str | None] = mapped_column(String(20), nullable=True, index=True)
    operation: Mapped[str | None] = mapped_column(String(80), nullable=True)
    occurrence_type_id: Mapped[int] = mapped_column(
        ForeignKey("machining_occurrence_types.id"), index=True
    )
    start_time: Mapped[time] = mapped_column(Time)
    end_time: Mapped[time] = mapped_column(Time)
    duration_minutes: Mapped[float] = mapped_column(Numeric(10, 2))
    quantity: Mapped[int] = mapped_column(default=0)
    efficiency_pct: Mapped[float] = mapped_column(Numeric(8, 2), default=0.0)
    standard_time: Mapped[float] = mapped_column(Numeric(10, 2), default=0.0)
    total_production: Mapped[int] = mapped_column(default=0)
    lot_code: Mapped[str | None] = mapped_column(String(40), nullable=True, index=True)
    notes: Mapped[str | None] = mapped_column(String(500), nullable=True)

    machine: Mapped["Machine"] = relationship(back_populates="appointments")
    operator: Mapped["Operator"] = relationship(back_populates="appointments")
    occurrence_type: Mapped["OccurrenceType"] = relationship()

    @property
    def duration_hours(self) -> float:
        return round(float(self.duration_minutes) / 60, 4)
