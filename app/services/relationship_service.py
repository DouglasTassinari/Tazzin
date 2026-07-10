"""Serviço do módulo Relacionamento com Cliente.

Única camada que as páginas Streamlit acessam para dados de cadência da
carteira. Orquestra o repositório de Vendas + as regras puras de relacionamento.
"""
from __future__ import annotations

from datetime import date

from sqlalchemy.orm import Session

from app.core.metrics import track
from app.domain import relationship_rules
from app.repositories.sales_repository import SalesOrderRepository


class RelationshipService:
    def __init__(self, session: Session):
        self.orders = SalesOrderRepository(session)

    @track("relationship.portfolio")
    def portfolio(self, today: date | None = None) -> list[dict]:
        """Carteira classificada por classe econômica + status de cadência."""
        today = today or date.today()
        rows = self.orders.customer_portfolio(today)
        return relationship_rules.classificar_carteira(rows, today)

    @track("relationship.health_score")
    def health_score(self, today: date | None = None) -> float:
        return relationship_rules.indice_saude(
            [c["status"] for c in self.portfolio(today)]
        )
