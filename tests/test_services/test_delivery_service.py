from datetime import date, timedelta

from app.database.models.core import Location, LocationType
from app.database.models.delivery import OrderDelivery
from app.database.models.sales import Customer, CustomerSegment, OrderStatus, SalesOrder
from app.services.delivery_service import DeliveryService

HOJE = date(2026, 10, 28)


def _entrega(session, n, cliente, local, prometida_dias_atras, atraso):
    pedido = SalesOrder(order_number=f"SO-{n:06d}", customer_id=cliente.id, location_id=local.id,
                        status=OrderStatus.SHIPPED, order_date=HOJE - timedelta(days=60), discount_pct=0)
    session.add(pedido)
    session.flush()
    prometida = HOJE - timedelta(days=prometida_dias_atras)
    entregue = None if atraso is None else prometida + timedelta(days=atraso)
    session.add(OrderDelivery(order_id=pedido.id, customer_id=cliente.id,
                              promised_date=prometida, delivered_date=entregue))
    session.flush()


def test_otd_and_open_late(session):
    local = Location(code="L", name="M", city="C", state="SC", location_type=LocationType.OFFICE)
    cliente = Customer(code="C", name="Cliente", segment=CustomerSegment.RETAIL, city="X", state="SC")
    session.add_all([local, cliente])
    session.flush()
    _entrega(session, 1, cliente, local, 30, 0)      # no prazo
    _entrega(session, 2, cliente, local, 25, -2)     # adiantado
    _entrega(session, 3, cliente, local, 20, 5)      # atrasou 5 dias
    _entrega(session, 4, cliente, local, 10, None)   # prazo vencido, ainda não chegou
    _entrega(session, 5, cliente, local, -5, None)   # prazo futuro: fora da conta
    sv = DeliveryService(session)
    atual = sv.summary(HOJE - timedelta(days=90), HOJE + timedelta(days=30), HOJE)["atual"]
    assert (atual["total"], atual["no_prazo"], atual["atrasados"]) == (4, 2, 2)
    assert atual["otd"] == 50.0
    abertos = sv.open_late(HOJE)
    assert [a["atraso"] for a in abertos] == [10]
