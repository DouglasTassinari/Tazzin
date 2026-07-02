from datetime import date, datetime

import pytest

from app.core.exceptions import EntityNotFoundError, ValidationError
from app.database.models.production import ProductionEventType, ProductionLine, WorkOrderStatus
from app.services.production_service import ProductionService


@pytest.fixture()
def production_line(session, location) -> ProductionLine:
    line = ProductionLine(
        code="LINE-9",
        name="Packaging Line",
        location_id=location.id,
        capacity_units_per_hour=200,
    )
    session.add(line)
    session.flush()
    return line


def test_create_work_order_persists_in_planned_status(session, location, product, production_line):
    service = ProductionService(session)

    order = service.create_work_order(
        order_number="WO-100",
        product_id=product.id,
        production_line_id=production_line.id,
        planned_quantity=100,
        scheduled_date=date(2026, 3, 1),
    )

    assert order.id is not None
    assert order.status == WorkOrderStatus.PLANNED


def test_create_work_order_rejects_overrun_beyond_tolerance(session, location, product, production_line):
    service = ProductionService(session)

    with pytest.raises(ValidationError):
        service.create_work_order(
            order_number="WO-101",
            product_id=product.id,
            production_line_id=production_line.id,
            planned_quantity=100,
            scheduled_date=date(2026, 3, 1),
            produced_quantity=100,
            scrap_quantity=10,
        )


def test_transition_work_order_follows_allowed_path(session, location, product, production_line):
    service = ProductionService(session)
    order = service.create_work_order(
        order_number="WO-102",
        product_id=product.id,
        production_line_id=production_line.id,
        planned_quantity=100,
        scheduled_date=date(2026, 3, 1),
    )

    updated = service.transition_work_order(order.id, WorkOrderStatus.IN_PROGRESS)
    assert updated.status == WorkOrderStatus.IN_PROGRESS

    with pytest.raises(ValidationError):
        service.transition_work_order(order.id, WorkOrderStatus.PLANNED)


def test_transition_unknown_work_order_raises_not_found(session):
    service = ProductionService(session)
    with pytest.raises(EntityNotFoundError):
        service.transition_work_order(999, WorkOrderStatus.IN_PROGRESS)


def test_record_event_appends_to_work_order(session, location, product, production_line):
    service = ProductionService(session)
    order = service.create_work_order(
        order_number="WO-103",
        product_id=product.id,
        production_line_id=production_line.id,
        planned_quantity=100,
        scheduled_date=date(2026, 3, 1),
    )

    event = service.record_event(
        order.id, ProductionEventType.START, datetime(2026, 3, 1, 8, 0), notes="Shift start"
    )

    assert event.id is not None
    assert len(order.events) == 1
    assert order.events[0].event_type == ProductionEventType.START


def test_line_yield_report_and_monthly_scrap_wrap_repository(session, location, product, production_line):
    service = ProductionService(session)
    order = service.create_work_order(
        order_number="WO-104",
        product_id=product.id,
        production_line_id=production_line.id,
        planned_quantity=100,
        scheduled_date=date(2026, 4, 1),
        produced_quantity=90,
        scrap_quantity=10,
    )
    service.transition_work_order(order.id, WorkOrderStatus.IN_PROGRESS)
    service.transition_work_order(order.id, WorkOrderStatus.COMPLETED)

    yield_rows = service.line_yield_report(date(2026, 4, 1), date(2026, 4, 30))
    scrap_rows = service.monthly_scrap(date(2026, 4, 1), date(2026, 4, 30))

    assert yield_rows == [("Packaging Line", 90.0)]
    assert scrap_rows == [("2026-04", 10)]
