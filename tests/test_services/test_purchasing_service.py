from datetime import date

import pytest

from app.core.exceptions import EntityNotFoundError, ValidationError
from app.database.models.purchasing import PurchaseOrderStatus, Supplier, SupplierCategory
from app.services.purchasing_service import PurchasingService


def _make_supplier(session) -> Supplier:
    supplier = Supplier(
        code="SUP-9",
        name="Globex Supply",
        category=SupplierCategory.EQUIPMENT,
        city="Springfield",
        state="IL",
        rating=4.5,
    )
    session.add(supplier)
    session.flush()
    return supplier


def test_create_purchase_order_persists_items(session, location, product):
    supplier = _make_supplier(session)
    service = PurchasingService(session)

    order = service.create_purchase_order(
        order_number="PO-100",
        supplier_id=supplier.id,
        location_id=location.id,
        order_date=date(2026, 3, 1),
        items=[{"product_id": product.id, "quantity": 4, "unit_cost": 50}],
    )

    assert order.id is not None
    assert order.status == PurchaseOrderStatus.DRAFT
    assert order.total_cost == 200.0  # 4 * 50


def test_create_purchase_order_rejects_invalid_line_item(session, location, product):
    supplier = _make_supplier(session)
    service = PurchasingService(session)

    with pytest.raises(ValidationError):
        service.create_purchase_order(
            order_number="PO-101",
            supplier_id=supplier.id,
            location_id=location.id,
            order_date=date(2026, 3, 1),
            items=[{"product_id": product.id, "quantity": 0, "unit_cost": 10}],
        )


def test_transition_purchase_order_follows_allowed_path(session, location, product):
    supplier = _make_supplier(session)
    service = PurchasingService(session)
    order = service.create_purchase_order(
        order_number="PO-102",
        supplier_id=supplier.id,
        location_id=location.id,
        order_date=date(2026, 3, 1),
        items=[{"product_id": product.id, "quantity": 1, "unit_cost": 10}],
    )

    updated = service.transition_purchase_order(order.id, PurchaseOrderStatus.SENT)
    assert updated.status == PurchaseOrderStatus.SENT

    with pytest.raises(ValidationError):
        service.transition_purchase_order(order.id, PurchaseOrderStatus.RECEIVED)


def test_transition_unknown_purchase_order_raises_not_found(session):
    service = PurchasingService(session)
    with pytest.raises(EntityNotFoundError):
        service.transition_purchase_order(999, PurchaseOrderStatus.SENT)
