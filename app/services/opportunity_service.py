"""Serviço do módulo Radar de Oportunidades.

Única camada que as páginas Streamlit acessam para o follow-up térmico das
propostas em aberto. Orquestra o repositório de Vendas + as regras puras.
"""
from __future__ import annotations

from datetime import date

from sqlalchemy.orm import Session

from app.core.metrics import track
from app.domain import opportunity_rules
from app.repositories.sales_repository import SalesOrderRepository


class OpportunityService:
    def __init__(self, session: Session):
        self.orders = SalesOrderRepository(session)

    @track("opportunity.radar")
    def radar(self, today: date | None = None) -> list[dict]:
        """Propostas em aberto classificadas por temperatura e já ordenadas."""
        today = today or date.today()
        propostas = self.orders.open_proposals()
        return opportunity_rules.classificar_propostas(propostas, today)

    @track("opportunity.pipeline_inflado")
    def pipeline_inflado(self, today: date | None = None) -> float:
        return opportunity_rules.pipeline_inflado(self.radar(today))
