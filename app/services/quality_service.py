"""Quality module service — orchestrates repositories + domain rules.

This is the only layer the Streamlit pages talk to for Quality data; pages
never import repositories or models directly.
"""
from __future__ import annotations

from datetime import date

from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.core.metrics import track
from app.database.models.quality import (
    Inspection,
    InspectionResult,
    NonConformance,
    NonConformanceSeverity,
    NonConformanceStatus,
)
from app.domain import quality_rules
from app.repositories.quality_repository import (
    InspectionRepository,
    NonConformanceRepository,
    QualityMetricRepository,
)

logger = get_logger("services.quality")


class QualityService:
    def __init__(self, session: Session):
        self.session = session
        self.inspections = InspectionRepository(session)
        self.nonconformances = NonConformanceRepository(session)
        self.metrics = QualityMetricRepository(session)

    @track("quality.record_inspection")
    def record_inspection(
        self,
        product_id: int,
        inspection_date: date,
        sample_size: int,
        defect_count: int,
        result: InspectionResult,
        work_order_id: int | None = None,
        inspector_employee_id: int | None = None,
    ) -> Inspection:
        quality_rules.validate_inspection(sample_size, defect_count)

        inspection = Inspection(
            work_order_id=work_order_id,
            product_id=product_id,
            inspector_employee_id=inspector_employee_id,
            inspection_date=inspection_date,
            result=result,
            sample_size=sample_size,
            defect_count=defect_count,
        )
        self.inspections.add(inspection)
        logger.info("Recorded inspection for product %s: %s", product_id, result.value)
        return inspection

    @track("quality.open_nonconformance")
    def open_nonconformance(
        self,
        inspection_id: int,
        severity: NonConformanceSeverity,
        description: str,
        opened_date: date,
    ) -> NonConformance:
        nonconformance = NonConformance(
            inspection_id=inspection_id,
            severity=severity,
            description=description,
            status=NonConformanceStatus.OPEN,
            opened_date=opened_date,
        )
        self.nonconformances.add(nonconformance)
        logger.info("Opened nonconformance for inspection %s", inspection_id)
        return nonconformance

    @track("quality.transition_nonconformance")
    def transition_nonconformance(
        self, nonconformance_id: int, target_status: NonConformanceStatus
    ) -> NonConformance:
        nonconformance = self.nonconformances.get(nonconformance_id)
        quality_rules.assert_transition(nonconformance.status, target_status)
        nonconformance.status = target_status
        self.session.flush()
        logger.info("Nonconformance %s moved to %s", nonconformance_id, target_status.value)
        return nonconformance

    @track("quality.defect_rate_trend")
    def defect_rate_trend(self, start: date, end: date) -> list[tuple[str, float]]:
        return self.inspections.defect_rate_by_month(start, end)

    @track("quality.open_nonconformances_by_severity")
    def open_nonconformances_by_severity(self) -> list[tuple[str, int]]:
        return self.nonconformances.open_by_severity()

    @track("quality.pass_rate")
    def pass_rate(self, start: date, end: date) -> float:
        rows = self.inspections.inspections_between(start, end)
        if not rows:
            return 0.0
        passed = sum(1 for row in rows if row.result == InspectionResult.PASS)
        return round(100.0 * passed / len(rows), 2)
