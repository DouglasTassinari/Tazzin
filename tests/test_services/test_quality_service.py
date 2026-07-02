from datetime import date

import pytest

from app.core.exceptions import EntityNotFoundError, ValidationError
from app.database.models.quality import (
    InspectionResult,
    NonConformanceSeverity,
    NonConformanceStatus,
)
from app.services.quality_service import QualityService


def test_record_inspection_persists(session, product):
    service = QualityService(session)

    inspection = service.record_inspection(
        product_id=product.id,
        inspection_date=date(2026, 1, 15),
        sample_size=100,
        defect_count=10,
        result=InspectionResult.FAIL,
    )

    assert inspection.id is not None
    assert inspection.result == InspectionResult.FAIL


def test_record_inspection_rejects_invalid_defect_count(session, product):
    service = QualityService(session)

    with pytest.raises(ValidationError):
        service.record_inspection(
            product_id=product.id,
            inspection_date=date(2026, 1, 15),
            sample_size=10,
            defect_count=99,
            result=InspectionResult.FAIL,
        )


def test_open_and_transition_nonconformance(session, product):
    service = QualityService(session)
    inspection = service.record_inspection(
        product_id=product.id,
        inspection_date=date(2026, 1, 15),
        sample_size=100,
        defect_count=10,
        result=InspectionResult.FAIL,
    )

    nonconformance = service.open_nonconformance(
        inspection_id=inspection.id,
        severity=NonConformanceSeverity.CRITICAL,
        description="Critical defect found on line",
        opened_date=date(2026, 1, 16),
    )
    assert nonconformance.status == NonConformanceStatus.OPEN

    updated = service.transition_nonconformance(nonconformance.id, NonConformanceStatus.UNDER_REVIEW)
    assert updated.status == NonConformanceStatus.UNDER_REVIEW

    with pytest.raises(ValidationError):
        service.transition_nonconformance(nonconformance.id, NonConformanceStatus.OPEN)


def test_transition_unknown_nonconformance_raises_not_found(session):
    service = QualityService(session)
    with pytest.raises(EntityNotFoundError):
        service.transition_nonconformance(999, NonConformanceStatus.UNDER_REVIEW)


def test_pass_rate_computes_percentage_of_passed_inspections(session, product):
    service = QualityService(session)
    service.record_inspection(
        product_id=product.id,
        inspection_date=date(2026, 1, 1),
        sample_size=10,
        defect_count=0,
        result=InspectionResult.PASS,
    )
    service.record_inspection(
        product_id=product.id,
        inspection_date=date(2026, 1, 2),
        sample_size=10,
        defect_count=5,
        result=InspectionResult.FAIL,
    )

    rate = service.pass_rate(date(2026, 1, 1), date(2026, 1, 31))
    assert rate == 50.0


def test_pass_rate_returns_zero_when_no_inspections(session):
    service = QualityService(session)
    assert service.pass_rate(date(2026, 1, 1), date(2026, 1, 31)) == 0.0
