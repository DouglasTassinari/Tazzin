from datetime import date

import pytest

from app.core.exceptions import EntityNotFoundError, ValidationError
from app.database.models.sales import Customer, CustomerSegment, OrderStatus
from app.services.sales_service import SalesService


def _make_customer(session) -> Customer:
    customer = Customer(
        code="CUST-9", name="Globex", segment=CustomerSegment.ENTERPRISE, city="Springfield", state="IL"
    )
    session.add(customer)
    session.flush()
    return customer


def test_create_order_persists_items(session, location, product):
    customer = _make_customer(session)
    service = SalesService(session)

    order = service.create_order(
        order_number="SO-100",
        customer_id=customer.id,
        location_id=location.id,
        order_date=date(2026, 3, 1),
        discount_pct=5,
        items=[{"product_id": product.id, "quantity": 4, "unit_price": 50}],
    )

    assert order.id is not None
    assert order.status == OrderStatus.DRAFT
    assert order.net_amount == 190.0  # 4*50 * 0.95


def test_create_order_rejects_invalid_discount(session, location, product):
    customer = _make_customer(session)
    service = SalesService(session)

    with pytest.raises(ValidationError):
        service.create_order(
            order_number="SO-101",
            customer_id=customer.id,
            location_id=location.id,
            order_date=date(2026, 3, 1),
            discount_pct=99,
            items=[{"product_id": product.id, "quantity": 1, "unit_price": 10}],
        )


def test_transition_order_follows_allowed_path(session, location, product):
    customer = _make_customer(session)
    service = SalesService(session)
    order = service.create_order(
        order_number="SO-102",
        customer_id=customer.id,
        location_id=location.id,
        order_date=date(2026, 3, 1),
        discount_pct=0,
        items=[{"product_id": product.id, "quantity": 1, "unit_price": 10}],
    )

    updated = service.transition_order(order.id, OrderStatus.CONFIRMED)
    assert updated.status == OrderStatus.CONFIRMED

    with pytest.raises(ValidationError):
        service.transition_order(order.id, OrderStatus.INVOICED)


def test_transition_unknown_order_raises_not_found(session):
    service = SalesService(session)
    with pytest.raises(EntityNotFoundError):
        service.transition_order(999, OrderStatus.CONFIRMED)
