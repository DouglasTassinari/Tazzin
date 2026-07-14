"""Scrap (Refugo) module service — orchestrates repositories + domain rules."""
from __future__ import annotations

from datetime import date

from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.core.metrics import track
from app.database.models.scrap import ScrapRecord
from app.domain import scrap_rules
from app.repositories.scrap_repository import ScrapPartRepository, ScrapRecordRepository

logger = get_logger("services.scrap")


class ScrapService:
    def __init__(self, session: Session):
        self.session = session
        self.records = ScrapRecordRepository(session)
        self.parts = ScrapPartRepository(session)

    @track("scrap.create_record")
    def create_record(
        self,
        record_date: date,
        operator_id: int,
        machine_id: int,
        reason_1: str,
        quantity_1: int,
        total_quantity: int | None = None,
        work_order_number: str | None = None,
        part_code: str | None = None,
        part_description: str | None = None,
        supplier: str | None = None,
        notes_1: str | None = None,
        reason_2: str | None = None,
        quantity_2: int | None = None,
        notes_2: str | None = None,
        reason_3: str | None = None,
        quantity_3: int | None = None,
        notes_3: str | None = None,
        pending: bool = False,
    ) -> ScrapRecord:
        scrap_rules.validate_scrap_record(
            reason_1, quantity_1, reason_2, quantity_2, reason_3, quantity_3,
        )
        computed_total = scrap_rules.total_quantity(quantity_1, quantity_2, quantity_3)
        record = ScrapRecord(
            record_date=record_date,
            operator_id=operator_id,
            machine_id=machine_id,
            work_order_number=work_order_number,
            part_code=part_code,
            part_description=part_description,
            supplier=supplier,
            reason_1=reason_1,
            quantity_1=quantity_1,
            notes_1=notes_1,
            reason_2=reason_2,
            quantity_2=quantity_2,
            notes_2=notes_2,
            reason_3=reason_3,
            quantity_3=quantity_3,
            notes_3=notes_3,
            total_quantity=total_quantity if total_quantity is not None else computed_total,
            pending=pending,
        )
        self.records.add(record)
        logger.info(
            "Scrap record created: operator=%s machine=%s qty=%s",
            operator_id, machine_id, record.total_quantity,
        )
        return record

    @track("scrap.total_in_period")
    def total_in_period(self, start: date, end: date) -> int:
        return self.records.total_by_period(start, end)

    @track("scrap.by_reason")
    def by_reason(self, start: date, end: date) -> list[tuple[str, int]]:
        return self.records.by_reason(start, end)

    @track("scrap.by_machine")
    def by_machine(self, start: date, end: date) -> list[tuple[str, int]]:
        return self.records.by_machine(start, end)

    @track("scrap.by_operator")
    def by_operator(self, start: date, end: date) -> list[tuple[str, int]]:
        return self.records.by_operator(start, end)

    @track("scrap.by_supplier")
    def by_supplier(self, start: date, end: date) -> list[tuple[str, int]]:
        return self.records.by_supplier(start, end)

    @track("scrap.by_origin")
    def by_origin(self, start: date, end: date) -> list[tuple[str, int]]:
        return self.records.by_origin(start, end)

    @track("scrap.monthly_trend")
    def monthly_trend(self, start: date, end: date) -> list[tuple[str, int]]:
        return self.records.monthly_totals(start, end)

    @track("scrap.concentration_alerts")
    def concentration_alerts(self, start: date, end: date) -> dict[str, list[str]]:
        reasons = dict(self.records.by_reason(start, end))
        machines = dict(self.records.by_machine(start, end))
        suppliers = dict(self.records.by_supplier(start, end))
        return {
            "reasons": scrap_rules.check_concentration(reasons, scrap_rules.CONCENTRATION_REASON_PCT),
            "machines": scrap_rules.check_concentration(machines, scrap_rules.CONCENTRATION_MACHINE_PCT),
            "suppliers": scrap_rules.check_concentration(suppliers, scrap_rules.CONCENTRATION_SUPPLIER_PCT),
        }
