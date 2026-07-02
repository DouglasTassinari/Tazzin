from datetime import date

import pytest

from app.core.exceptions import ValidationError
from app.database.models.inventory import MovementType, Warehouse
from app.services.inventory_service import InventoryService


def _make_warehouse(session, location) -> Warehouse:
    warehouse = Warehouse(code="WH-9", name="Overflow Warehouse", location_id=location.id, capacity_units=500)
    session.add(warehouse)
    session.flush()
    return warehouse


def test_record_movement_persists_stock_movement(session, location, product):
    warehouse = _make_warehouse(session, location)
    service = InventoryService(session)

    movement = service.record_movement(
        product_id=product.id,
        warehouse_id=warehouse.id,
        movement_type=MovementType.INBOUND,
        quantity=40,
        movement_date=date(2026, 1, 10),
        reference_note="Initial stock",
    )

    assert movement.id is not None
    assert movement.quantity == 40
    assert movement.reference_note == "Initial stock"


def test_record_movement_rejects_invalid_quantity(session, location, product):
    warehouse = _make_warehouse(session, location)
    service = InventoryService(session)

    with pytest.raises(ValidationError):
        service.record_movement(
            product_id=product.id,
            warehouse_id=warehouse.id,
            movement_type=MovementType.OUTBOUND,
            quantity=-1,
            movement_date=date(2026, 1, 10),
        )


def test_on_hand_report_reflects_recorded_movements(session, location, product):
    warehouse = _make_warehouse(session, location)
    service = InventoryService(session)

    service.record_movement(product.id, warehouse.id, MovementType.INBOUND, 60, date(2026, 1, 1))
    service.record_movement(product.id, warehouse.id, MovementType.OUTBOUND, 10, date(2026, 1, 2))

    report = service.on_hand_report()

    assert report == [(product.sku, product.name, 50)]


def test_low_stock_alert_flags_products_below_reorder_point(session, location, product):
    warehouse = _make_warehouse(session, location)
    service = InventoryService(session)

    service.record_movement(product.id, warehouse.id, MovementType.INBOUND, 10, date(2026, 1, 1))

    alerts = service.low_stock_alert()

    assert [p.sku for p in alerts] == [product.sku]
