"""Machining (Usinagem) module service — orchestrates repositories + domain rules.

Covers the shop floor dashboards: operator yield, time breakdown,
machine utilization, production daily output and monthly yield trend.
"""
from __future__ import annotations

from datetime import date, time

from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.core.metrics import track
from app.database.models.machining import Appointment, Machine, OccurrenceType, Operator
from app.domain import machining_rules
from app.repositories.machining_repository import (
    AppointmentRepository,
    MachineRepository,
    OccurrenceTypeRepository,
    OperatorRepository,
)

logger = get_logger("services.machining")


class MachiningService:
    def __init__(self, session: Session):
        self.session = session
        self.machines = MachineRepository(session)
        self.operators = OperatorRepository(session)
        self.occurrence_types = OccurrenceTypeRepository(session)
        self.appointments = AppointmentRepository(session)

    @track("machining.create_appointment")
    def create_appointment(
        self,
        appointment_date: date,
        machine_id: int,
        operator_id: int,
        occurrence_type_id: int,
        start_time: time,
        end_time: time,
        duration_minutes: float,
        quantity: int = 0,
        efficiency_pct: float = 0.0,
        standard_time: float = 0.0,
        total_production: int = 0,
        work_order_number: str | None = None,
        operation: str | None = None,
        lot_code: str | None = None,
        notes: str | None = None,
    ) -> Appointment:
        machining_rules.validate_appointment(duration_minutes, quantity)
        appt = Appointment(
            appointment_date=appointment_date,
            machine_id=machine_id,
            operator_id=operator_id,
            occurrence_type_id=occurrence_type_id,
            start_time=start_time,
            end_time=end_time,
            duration_minutes=duration_minutes,
            quantity=quantity,
            efficiency_pct=efficiency_pct,
            standard_time=standard_time,
            total_production=total_production,
            work_order_number=work_order_number,
            operation=operation,
            lot_code=lot_code,
            notes=notes,
        )
        self.appointments.add(appt)
        logger.info(
            "Appointment created: operator=%s machine=%s date=%s",
            operator_id, machine_id, appointment_date,
        )
        return appt

    @track("machining.operator_yield_ranking")
    def operator_yield_ranking(self, start: date, end: date) -> list[tuple[str, float, int]]:
        return self.appointments.yield_by_operator(start, end)

    @track("machining.time_by_category")
    def time_by_category(self, start: date, end: date) -> list[tuple[str, float]]:
        return self.appointments.time_by_category(start, end)

    @track("machining.time_by_occurrence")
    def time_by_occurrence(self, start: date, end: date) -> list[tuple[str, float]]:
        return self.appointments.time_by_occurrence(start, end)

    @track("machining.production_by_day")
    def production_by_day(self, start: date, end: date) -> list[tuple[str, int]]:
        return self.appointments.production_by_day(start, end)

    @track("machining.machine_utilization")
    def machine_utilization(self, start: date, end: date) -> list[tuple[str, float, float]]:
        return self.appointments.time_by_machine(start, end)

    @track("machining.monthly_yield_trend")
    def monthly_yield_trend(self, start: date, end: date) -> list[tuple[str, float]]:
        return self.appointments.monthly_yield(start, end)

    @track("machining.time_breakdown")
    def time_breakdown_summary(self, start: date, end: date) -> dict[str, float]:
        rows = self.appointments.time_by_category(start, end)
        cat_hours = {cat: h for cat, h in rows}
        prod = cat_hours.get("productive", 0)
        semi = cat_hours.get("semi_productive", 0)
        unprod = cat_hours.get("unproductive", 0)
        total = prod + semi + unprod
        return machining_rules.time_breakdown(
            production_min=prod * 60,
            setup_min=semi * 60,
            no_part_min=0,
            stops_min=unprod * 60,
            available_min=total * 60,
        )
