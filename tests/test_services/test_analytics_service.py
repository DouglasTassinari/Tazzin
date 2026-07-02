from datetime import date

from app.database.models.sales import Customer, CustomerSegment
from app.services.analytics_service import AnalyticsService
from app.services.sales_service import SalesService


def test_executive_summary_returns_zeroed_snapshot_when_empty(session):
    service = AnalyticsService(session)
    summary = service.executive_summary(date(2026, 1, 1), date(2026, 12, 31))

    assert summary["total_revenue"] == 0.0
    assert summary["active_projects"] == 0
    assert summary["active_headcount"] == 0
    assert summary["outstanding_receivables"] == 0.0


def test_executive_summary_reflects_sales_activity(session, location, product):
    customer = Customer(
        code="CUST-A", name="Analytics Co", segment=CustomerSegment.RETAIL, city="Metropolis", state="NY"
    )
    session.add(customer)
    session.flush()
    SalesService(session).create_order(
        order_number="SO-500",
        customer_id=customer.id,
        location_id=location.id,
        order_date=date(2026, 5, 10),
        discount_pct=0,
        items=[{"product_id": product.id, "quantity": 2, "unit_price": 100}],
    )

    service = AnalyticsService(session)
    summary = service.executive_summary(date(2026, 5, 1), date(2026, 5, 31))
    assert summary["total_revenue"] == 200.0
