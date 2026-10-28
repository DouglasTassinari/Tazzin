from datetime import date, timedelta

from app.database.models.core import Location, LocationType
from app.database.models.postsales import PostSaleSurvey, SurveyFollowUp
from app.database.models.sales import Customer, CustomerSegment, OrderStatus, SalesOrder
from app.services.postsales_service import PostSalesService

HOJE = date(2026, 10, 28)


def _pedido(session, n: int, cliente: Customer, local: Location) -> SalesOrder:
    pedido = SalesOrder(order_number=f"SO-{n:06d}", customer_id=cliente.id, location_id=local.id,
                        status=OrderStatus.INVOICED, order_date=HOJE - timedelta(days=30))
    session.add(pedido)
    session.flush()
    return pedido


def _base(session):
    local = Location(code="L1", name="Matriz", city="Criciúma", state="SC", location_type=LocationType.OFFICE)
    cliente = Customer(code="C1", name="Metalúrgica Norte", segment=CustomerSegment.WHOLESALE,
                       city="Joinville", state="SC")
    session.add_all([local, cliente])
    session.flush()
    return local, cliente


def _pesquisa(session, n, cliente, local, nps, dias_resposta=3, retorno=SurveyFollowUp.NONE):
    pedido = _pedido(session, n, cliente, local)
    enviada = HOJE - timedelta(days=10)
    session.add(PostSaleSurvey(
        order_id=pedido.id, customer_id=cliente.id, sent_date=enviada,
        responded_date=None if nps is None else HOJE - timedelta(days=dias_resposta),
        nps_score=nps, csat_score=None if nps is None else (5 if nps >= 9 else 2),
        comment=None if nps is None else "ok", follow_up=retorno,
    ))
    session.flush()


def test_summary_computes_nps_csat_and_response(session):
    local, cliente = _base(session)
    for i, nota in enumerate([10, 9, 8, 2, None, None], start=1):
        _pesquisa(session, i, cliente, local, nota)
    atual = PostSalesService(session).summary(HOJE - timedelta(days=30), HOJE)["atual"]
    assert atual["enviadas"] == 6 and atual["respondidas"] == 4
    assert atual["taxa_resposta"] == 66.7
    assert atual["nps"] == 25.0           # 2 promotores, 1 detrator em 4
    assert atual["csat"] == 50.0
    assert (atual["promotores"], atual["neutros"], atual["detratores"]) == (2, 1, 1)


def test_detractor_queue_orders_oldest_first_and_skips_resolved(session):
    local, cliente = _base(session)
    _pesquisa(session, 1, cliente, local, 3, dias_resposta=9, retorno=SurveyFollowUp.PENDING)
    _pesquisa(session, 2, cliente, local, 4, dias_resposta=1, retorno=SurveyFollowUp.IN_CONTACT)
    _pesquisa(session, 3, cliente, local, 2, dias_resposta=5, retorno=SurveyFollowUp.RESOLVED)
    _pesquisa(session, 4, cliente, local, 10)
    fila = PostSalesService(session).detractor_queue(HOJE, HOJE - timedelta(days=30), HOJE)
    assert [r["dias"] for r in fila] == [9, 1]
    assert [r["prazo"] for r in fila] == ["vencido", "ok"]


def test_empty_window_has_no_indicators(session):
    atual = PostSalesService(session).summary(HOJE - timedelta(days=30), HOJE)["atual"]
    assert atual["enviadas"] == 0 and atual["nps"] is None
