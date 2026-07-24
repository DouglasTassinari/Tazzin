"""Inteligência de Licitações — compras públicas (PNCP) cruzadas por NCM.

O NCM é a dobradiça do módulo: é ele que liga o que o poder público está
comprando ao que a empresa sabe vender. Sem esse cruzamento a lista de
licitações é só ruído.
"""
from __future__ import annotations

from datetime import date

from sqlalchemy.orm import Session

from app.core.metrics import track
from app.repositories.bidding_repository import (
    CatalogRepository,
    PriceRecordRepository,
    TenderRepository,
)


class BiddingService:
    def __init__(self, session: Session):
        self.session = session
        self.tenders = TenderRepository(session)
        self.price_records = PriceRecordRepository(session)
        self.catalog = CatalogRepository(session)

    # -- Mercado ------------------------------------------------------------ #
    @track("bidding.market")
    def market(self, start: date, end: date) -> dict:
        return {
            "mensal": self.tenders.monthly_value(start, end),
            "por_estado": self.tenders.by_state(start, end),
            "por_modalidade": self.tenders.by_modality(start, end),
            "top_orgaos": self.tenders.top_organs(start, end),
        }

    # -- Oportunidades / Operação ------------------------------------------- #
    @track("bidding.opportunities")
    def opportunities(self, today: date) -> list[dict]:
        """Abertas que batem com o catálogo, da mais próxima de abrir em diante."""
        return self.tenders.open_opportunities(today)

    # -- Licitações --------------------------------------------------------- #
    @track("bidding.search")
    def search(
        self,
        start: date,
        end: date,
        states: list[str] | None = None,
        modalities: list[str] | None = None,
        statuses: list[str] | None = None,
    ) -> list[dict]:
        return self.tenders.search(start, end, states, modalities, statuses)

    # -- Atas --------------------------------------------------------------- #
    @track("bidding.active_price_records")
    def active_price_records(self, today: date) -> list[dict]:
        return self.price_records.active(today)

    # -- Catálogo ----------------------------------------------------------- #
    @track("bidding.catalog")
    def catalog_items(self) -> list[dict]:
        return self.catalog.all_items()

    # -- Cobertura ---------------------------------------------------------- #
    @track("bidding.coverage")
    def coverage(self, start: date, end: date) -> dict:
        """Quanto da demanda pública o catálogo alcança — e o que está de fora."""
        demanda = self.tenders.ncm_demand(start, end)
        valor_total = sum(item["valor"] for item in demanda)
        valor_coberto = sum(item["valor"] for item in demanda if item["no_catalogo"])
        return {
            "demanda": demanda,
            "valor_total": valor_total,
            "valor_coberto": valor_coberto,
            "pct_coberto": (valor_coberto / valor_total * 100) if valor_total else 0.0,
            "fora_do_catalogo": [item for item in demanda if not item["no_catalogo"]],
        }
