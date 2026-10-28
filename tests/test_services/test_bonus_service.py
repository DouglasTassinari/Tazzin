from datetime import date

from app.database.models.core import Location, LocationType
from app.database.models.inventory import Product, ProductCategory
from app.database.models.sales import (
    Customer,
    CustomerSegment,
    OrderStatus,
    SalesOrder,
    SalesOrderItem,
)
from app.services.bonus_service import BonusService


def _pedido(session, n, cliente, local, produto, qtd, status=OrderStatus.INVOICED, ano=2026):
    p = SalesOrder(order_number=f"SO-{n:06d}", customer_id=cliente.id, location_id=local.id,
                   status=status, order_date=date(ano, 3, 1), discount_pct=0)
    session.add(p)
    session.flush()
    session.add(SalesOrderItem(order_id=p.id, product_id=produto.id, quantity=qtd, unit_price=10.0))
    session.flush()


def test_ranking_counts_only_wholesale_invoiced_orders_of_the_year(session):
    local = Location(code="L", name="M", city="C", state="SC", location_type=LocationType.OFFICE)
    produto = Product(sku="P", name="Peça", category=ProductCategory.FINISHED_GOOD,
                      unit_cost=1.0, unit_price=10.0, reorder_point=1)
    dist = Customer(code="D", name="Dist A", segment=CustomerSegment.WHOLESALE, city="X", state="SC")
    varejo = Customer(code="V", name="Loja", segment=CustomerSegment.RETAIL, city="X", state="SC")
    session.add_all([local, produto, dist, varejo])
    session.flush()
    _pedido(session, 1, dist, local, produto, 20_000)                       # 200 mil
    _pedido(session, 2, dist, local, produto, 15_000)                       # +150 mil = 350 mil
    _pedido(session, 3, dist, local, produto, 99_999, OrderStatus.DRAFT)    # proposta não conta
    _pedido(session, 4, dist, local, produto, 99_999, ano=2025)             # outro ano não conta
    _pedido(session, 5, varejo, local, produto, 99_999)                     # não é distribuidor
    ranking = BonusService(session).ranking(2026)
    assert len(ranking) == 1
    assert ranking[0]["compras"] == 350_000.0 and ranking[0]["pct"] == 5.0
    assert ranking[0]["bonus"] == 17_500.0 and ranking[0]["faltam"] == 100_000.0
