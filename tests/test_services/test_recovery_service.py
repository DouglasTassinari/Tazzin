from datetime import date, timedelta

from app.database.models.core import Location, LocationType
from app.database.models.inventory import Product, ProductCategory
from app.database.models.recovery import RecoveryChannel, RecoveryContact, RecoveryResult
from app.database.models.sales import (
    Customer,
    CustomerSegment,
    OrderStatus,
    SalesOrder,
    SalesOrderItem,
)
from app.services.recovery_service import RecoveryService

HOJE = date(2026, 10, 28)


def _base(session):
    local = Location(code="L1", name="Matriz", city="Criciúma", state="SC", location_type=LocationType.OFFICE)
    produto = Product(sku="P1", name="Peça", category=ProductCategory.FINISHED_GOOD,
                      unit_cost=5.0, unit_price=10.0, reorder_point=1)
    session.add_all([local, produto])
    session.flush()
    return local, produto


def _cliente(session, codigo: str) -> Customer:
    c = Customer(code=codigo, name=f"Cliente {codigo}", segment=CustomerSegment.RETAIL, city="X", state="SC")
    session.add(c)
    session.flush()
    return c


def _compra(session, n, cliente, local, produto, dias_atras, qtd=10, status=OrderStatus.INVOICED):
    pedido = SalesOrder(order_number=f"SO-{n:06d}", customer_id=cliente.id, location_id=local.id,
                        status=status, order_date=HOJE - timedelta(days=dias_atras), discount_pct=0)
    session.add(pedido)
    session.flush()
    session.add(SalesOrderItem(order_id=pedido.id, product_id=produto.id, quantity=qtd, unit_price=10.0))
    session.flush()
    return pedido


def test_bands_count_clients_by_recency(session):
    local, produto = _base(session)
    for i, dias in enumerate([10, 120, 200, 400], start=1):
        _compra(session, i, _cliente(session, f"C{i}"), local, produto, dias)
    r = RecoveryService(session).bands(HOJE)
    assert r["clientes"] == {"ativo": 1, "em_risco": 1, "inativo": 1, "perdido": 1}


def test_open_orders_do_not_count_as_purchase(session):
    local, produto = _base(session)
    c = _cliente(session, "C1")
    _compra(session, 1, c, local, produto, 300)
    _compra(session, 2, c, local, produto, 5, status=OrderStatus.DRAFT)   # proposta não é compra
    assert RecoveryService(session).bands(HOJE)["clientes"]["inativo"] == 1


def test_queue_orders_by_value_and_sets_priority(session):
    local, produto = _base(session)
    pequeno = _cliente(session, "P")
    grande = _cliente(session, "G")
    _compra(session, 1, pequeno, local, produto, 200, qtd=1)
    _compra(session, 2, grande, local, produto, 220, qtd=100)
    fila = RecoveryService(session).queue(HOJE)
    assert [c["nome"] for c in fila] == ["Cliente G", "Cliente P"]
    assert fila[0]["prioridade"] == "alta"


def test_summary_reactivation_and_recovered_revenue(session):
    local, produto = _base(session)
    c1, c2 = _cliente(session, "A"), _cliente(session, "B")
    volta = _compra(session, 1, c1, local, produto, 20, qtd=50)    # 500 de receita recuperada
    session.add_all([
        RecoveryContact(customer_id=c1.id, contact_date=HOJE - timedelta(days=40),
                        channel=RecoveryChannel.PHONE, result=RecoveryResult.REACTIVATED,
                        recovered_order_id=volta.id),
        RecoveryContact(customer_id=c2.id, contact_date=HOJE - timedelta(days=30),
                        channel=RecoveryChannel.EMAIL, result=RecoveryResult.NO_ANSWER),
    ])
    session.flush()
    atual = RecoveryService(session).summary(HOJE - timedelta(days=90), HOJE)["atual"]
    assert (atual["contatados"], atual["reativados"], atual["taxa"]) == (2, 1, 50.0)
    assert atual["recuperado"] == 500.0
