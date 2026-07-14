"""Time Adjustments (Ajustes) module service — orchestrates repositories + domain rules."""
from __future__ import annotations

from datetime import date, datetime

from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.core.metrics import track
from app.database.models.adjustments import TimeAdjustment
from app.domain import adjustments_rules
from app.repositories.adjustments_repository import TimeAdjustmentRepository

logger = get_logger("services.adjustments")


class AdjustmentsService:
    def __init__(self, session: Session):
        self.session = session
        self.adjustments = TimeAdjustmentRepository(session)

    @track("adjustments.create")
    def create_adjustment(
        self,
        record_date: datetime,
        operator_id: int,
        machine_id: int,
        operation: str,
        previous_time_seconds: float,
        current_time_seconds: float,
        justification: str,
        work_order_number: str | None = None,
        part_code: str | None = None,
        part_description: str | None = None,
        quantity: float = 0,
    ) -> TimeAdjustment:
        adjustments_rules.validate_adjustment(
            previous_time_seconds, current_time_seconds, justification,
        )
        adj = TimeAdjustment(
            record_date=record_date,
            operator_id=operator_id,
            machine_id=machine_id,
            operation=operation,
            previous_time_seconds=previous_time_seconds,
            current_time_seconds=current_time_seconds,
            justification=justification,
            work_order_number=work_order_number,
            part_code=part_code,
            part_description=part_description,
            quantity=quantity,
        )
        self.adjustments.add(adj)
        logger.info(
            "Time adjustment created: operator=%s diff=%.1fs (%s)",
            operator_id,
            adjustments_rules.difference_seconds(previous_time_seconds, current_time_seconds),
            "improvement" if adjustments_rules.is_improvement(previous_time_seconds, current_time_seconds) else "worsening",
        )
        return adj

    @track("adjustments.by_operator")
    def by_operator(self, start: date, end: date) -> list[tuple[str, int, int, float]]:
        return self.adjustments.summary_by_operator(start, end)

    @track("adjustments.by_machine")
    def by_machine(self, start: date, end: date) -> list[tuple[str, int, int, float]]:
        return self.adjustments.summary_by_machine(start, end)

    @track("adjustments.monthly_trend")
    def monthly_trend(self, start: date, end: date) -> list[tuple[str, int, int]]:
        return self.adjustments.monthly_totals(start, end)

    @track("adjustments.operator_alerts")
    def operator_alerts(self, start: date, end: date) -> list[str]:
        """Operators with more worsenings than improvements."""
        rows = self.adjustments.summary_by_operator(start, end)
        return [
            name for name, imp, wor, _ in rows
            if adjustments_rules.operator_has_too_many_worsenings(imp, wor)
        ]

    @track("adjustments.machine_alerts")
    def machine_alerts(self, start: date, end: date) -> list[str]:
        rows = self.adjustments.summary_by_machine(start, end)
        return [
            name for name, imp, wor, _ in rows
            if adjustments_rules.machine_is_worsening(imp, wor)
        ]
