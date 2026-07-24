"""Descoberta de Mercado — orquestra o repositório da base de empresas.

Camada única que as páginas usam para o módulo; nenhuma página importa
repositório ou model direto.
"""
from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.metrics import track
from app.repositories.market_repository import MarketCompanyRepository


class MarketService:
    def __init__(self, session: Session):
        self.session = session
        self.companies = MarketCompanyRepository(session)

    @track("market.filter_options")
    def filter_options(self) -> dict:
        """Valores disponíveis para montar os filtros da tela."""
        return {
            "estados": self.companies.distinct_states(),
            "cnaes": self.companies.distinct_cnaes(),
        }

    @track("market.overview")
    def overview(
        self,
        states: list[str] | None = None,
        cnaes: list[str] | None = None,
        sizes: list[str] | None = None,
        active_only: bool = True,
    ) -> dict:
        """Tudo que a tela mostra num filtro só, para não repetir os argumentos."""
        filtros = (states, cnaes, sizes, active_only)
        return {
            "resumo": self.companies.summary(*filtros),
            "por_estado": self.companies.by_state(*filtros),
            "por_cnae": self.companies.by_cnae(*filtros),
            "por_porte": self.companies.by_size(*filtros),
            "aberturas": self.companies.openings_by_year(*filtros),
        }

    @track("market.sample")
    def sample(
        self,
        states: list[str] | None = None,
        cnaes: list[str] | None = None,
        sizes: list[str] | None = None,
        active_only: bool = True,
        limit: int = 300,
    ) -> list[dict]:
        empresas = self.companies.sample(states, cnaes, sizes, active_only, limit)
        return [
            {
                "cnpj": e.cnpj,
                "razao_social": e.legal_name,
                "nome_fantasia": e.trade_name or "—",
                "cnae": e.cnae_label,
                "cidade": e.city,
                "estado": e.state,
                "porte": e.size.value,
                "situacao": e.status.value,
                "abertura": e.opening_date,
                "capital_social": float(e.share_capital or 0),
            }
            for e in empresas
        ]
