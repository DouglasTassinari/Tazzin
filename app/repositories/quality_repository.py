"""Data access for the Quality module."""
from __future__ import annotations

from datetime import date

from sqlalchemy import func, select

from app.database.models.quality import (
    Inspection,
    NonConformance,
    NonConformanceStatus,
    QualityMetric,
)
from app.repositories.base import BaseRepository


class InspectionRepository(BaseRepository[Inspection]):
    model = Inspection

    def inspections_between(self, start: date, end: date) -> list[Inspection]:
        stmt = select(Inspection).where(
            Inspection.inspection_date >= start, Inspection.inspection_date <= end
        )
        return list(self.session.execute(stmt).scalars().all())

    def defect_rate_by_month(self, start: date, end: date) -> list[tuple[str, float]]:
        """Average defect rate (% of samples with defects) grouped by calendar month."""
        stmt = (
            select(
                func.strftime("%Y-%m", Inspection.inspection_date).label("month"),
                func.sum(Inspection.defect_count).label("defects"),
                func.sum(Inspection.sample_size).label("samples"),
            )
            .where(Inspection.inspection_date >= start, Inspection.inspection_date <= end)
            .group_by("month")
            .order_by("month")
        )
        rows = self.session.execute(stmt).all()
        return [
            (month, round(100.0 * float(defects or 0) / float(samples), 2) if samples else 0.0)
            for month, defects, samples in rows
        ]


class NonConformanceRepository(BaseRepository[NonConformance]):
    model = NonConformance

    def open_by_severity(self) -> list[tuple[str, int]]:
        stmt = (
            select(NonConformance.severity, func.count().label("total"))
            .where(
                NonConformance.status.in_(
                    (NonConformanceStatus.OPEN, NonConformanceStatus.UNDER_REVIEW)
                )
            )
            .group_by(NonConformance.severity)
            .order_by(func.count().desc())
        )
        return [(severity.value, total) for severity, total in self.session.execute(stmt).all()]


class QualityMetricRepository(BaseRepository[QualityMetric]):
    model = QualityMetric

    def metric_trend(self, metric_name: str, start: date, end: date) -> list[tuple[date, float]]:
        stmt = (
            select(QualityMetric.metric_date, QualityMetric.metric_value)
            .where(
                QualityMetric.metric_name == metric_name,
                QualityMetric.metric_date >= start,
                QualityMetric.metric_date <= end,
            )
            .order_by(QualityMetric.metric_date)
        )
        return [(metric_date, float(value)) for metric_date, value in self.session.execute(stmt).all()]
