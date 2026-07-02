from datetime import date

from app.database.models.quality import (
    Inspection,
    InspectionResult,
    NonConformance,
    NonConformanceSeverity,
    NonConformanceStatus,
    QualityMetric,
)
from app.repositories.quality_repository import (
    InspectionRepository,
    NonConformanceRepository,
    QualityMetricRepository,
)


def _make_inspection(session, product, inspection_date, sample_size, defect_count) -> Inspection:
    inspection = Inspection(
        product_id=product.id,
        inspection_date=inspection_date,
        result=InspectionResult.PASS,
        sample_size=sample_size,
        defect_count=defect_count,
    )
    session.add(inspection)
    session.flush()
    return inspection


def test_inspections_between_filters_by_date(session, product):
    _make_inspection(session, product, date(2026, 1, 10), 100, 5)
    _make_inspection(session, product, date(2026, 3, 10), 100, 5)

    repo = InspectionRepository(session)
    rows = repo.inspections_between(date(2026, 1, 1), date(2026, 1, 31))

    assert len(rows) == 1
    assert rows[0].inspection_date == date(2026, 1, 10)


def test_defect_rate_by_month_groups_and_averages(session, product):
    _make_inspection(session, product, date(2026, 1, 5), 100, 10)
    _make_inspection(session, product, date(2026, 1, 20), 100, 20)
    _make_inspection(session, product, date(2026, 2, 1), 50, 5)

    repo = InspectionRepository(session)
    rows = repo.defect_rate_by_month(date(2026, 1, 1), date(2026, 2, 28))

    assert rows == [("2026-01", 15.0), ("2026-02", 10.0)]


def test_open_by_severity_excludes_resolved_and_closed(session, product):
    inspection = _make_inspection(session, product, date(2026, 1, 1), 100, 5)
    session.add_all(
        [
            NonConformance(
                inspection_id=inspection.id,
                severity=NonConformanceSeverity.MAJOR,
                description="Two major defects open",
                status=NonConformanceStatus.OPEN,
                opened_date=date(2026, 1, 2),
            ),
            NonConformance(
                inspection_id=inspection.id,
                severity=NonConformanceSeverity.MAJOR,
                description="Another major under review",
                status=NonConformanceStatus.UNDER_REVIEW,
                opened_date=date(2026, 1, 3),
            ),
            NonConformance(
                inspection_id=inspection.id,
                severity=NonConformanceSeverity.MINOR,
                description="Minor already closed",
                status=NonConformanceStatus.CLOSED,
                opened_date=date(2026, 1, 4),
                closed_date=date(2026, 1, 5),
            ),
        ]
    )
    session.flush()

    repo = NonConformanceRepository(session)
    rows = repo.open_by_severity()

    assert rows == [("major", 2)]


def test_metric_trend_orders_by_date(session, location):
    session.add_all(
        [
            QualityMetric(
                location_id=location.id,
                metric_date=date(2026, 2, 1),
                metric_name="scrap_rate",
                metric_value=1.5,
            ),
            QualityMetric(
                location_id=location.id,
                metric_date=date(2026, 1, 1),
                metric_name="scrap_rate",
                metric_value=2.5,
            ),
        ]
    )
    session.flush()

    repo = QualityMetricRepository(session)
    rows = repo.metric_trend("scrap_rate", date(2026, 1, 1), date(2026, 2, 28))

    assert rows == [(date(2026, 1, 1), 2.5), (date(2026, 2, 1), 1.5)]
