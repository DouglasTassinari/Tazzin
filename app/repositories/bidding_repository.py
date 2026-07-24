"""Data access for Inteligência de Licitações (PNCP × NCM)."""
from __future__ import annotations

from datetime import date

from sqlalchemy import func, select

from app.database.models.bidding import (
    CatalogItem,
    PriceRecord,
    Tender,
    TenderItem,
    TenderStatus,
)
from app.repositories.base import BaseRepository

# Valor de um item = quantidade × preço unitário estimado.
_VALOR_ITEM = func.sum(TenderItem.quantity * TenderItem.unit_price)


class TenderRepository(BaseRepository[Tender]):
    model = Tender

    # -- Mercado ------------------------------------------------------------ #
    def monthly_value(self, start: date, end: date) -> list[tuple[str, float]]:
        mes = func.strftime("%Y-%m", Tender.publish_date).label("mes")
        stmt = (
            select(mes, func.sum(Tender.estimated_value))
            .where(Tender.publish_date >= start, Tender.publish_date <= end)
            .group_by(mes)
            .order_by(mes)
        )
        return [(str(m), float(total or 0)) for m, total in self.session.execute(stmt).all()]

    def _group_value(self, coluna, start: date, end: date, limit: int | None = None):
        total = func.sum(Tender.estimated_value)
        stmt = (
            select(coluna, total.label("total"))
            .where(Tender.publish_date >= start, Tender.publish_date <= end)
            .group_by(coluna)
            .order_by(total.desc())
        )
        if limit:
            stmt = stmt.limit(limit)
        return self.session.execute(stmt).all()

    def by_state(self, start: date, end: date, limit: int = 12) -> list[tuple[str, float]]:
        rows = self._group_value(Tender.state, start, end, limit)
        return [(uf, float(total or 0)) for uf, total in rows]

    def by_modality(self, start: date, end: date) -> list[tuple[str, float]]:
        rows = self._group_value(Tender.modality, start, end)
        return [(modalidade.value, float(total or 0)) for modalidade, total in rows]

    def top_organs(self, start: date, end: date, limit: int = 10) -> list[tuple[str, float]]:
        rows = self._group_value(Tender.organ, start, end, limit)
        return [(orgao, float(total or 0)) for orgao, total in rows]

    # -- Oportunidades / Operação ------------------------------------------- #
    def open_opportunities(self, today: date) -> list[dict]:
        """Licitações abertas cujo NCM está no catálogo — o que dá para disputar."""
        stmt = (
            select(
                Tender.pncp_id,
                Tender.organ,
                Tender.city,
                Tender.state,
                Tender.modality,
                Tender.opening_date,
                _VALOR_ITEM.label("valor"),
                func.count(TenderItem.id).label("itens"),
            )
            .join(TenderItem, TenderItem.tender_id == Tender.id)
            .join(CatalogItem, CatalogItem.ncm == TenderItem.ncm)
            .where(Tender.status == TenderStatus.ABERTA)
            .group_by(Tender.id)
            .order_by(Tender.opening_date)
        )
        return [
            {
                "pncp": pncp,
                "orgao": orgao,
                "cidade": cidade,
                "estado": uf,
                "modalidade": modalidade.value,
                "abertura": abertura,
                "dias": (abertura - today).days,
                "valor": float(valor or 0),
                "itens": int(itens or 0),
            }
            for pncp, orgao, cidade, uf, modalidade, abertura, valor, itens in (
                self.session.execute(stmt).all()
            )
        ]

    # -- Licitações (consulta) ---------------------------------------------- #
    def search(
        self,
        start: date,
        end: date,
        states: list[str] | None = None,
        modalities: list[str] | None = None,
        statuses: list[str] | None = None,
        limit: int = 300,
    ) -> list[dict]:
        stmt = select(Tender).where(Tender.publish_date >= start, Tender.publish_date <= end)
        if states:
            stmt = stmt.where(Tender.state.in_(states))
        if modalities:
            stmt = stmt.where(Tender.modality.in_(modalities))
        if statuses:
            stmt = stmt.where(Tender.status.in_(statuses))
        stmt = stmt.order_by(Tender.publish_date.desc()).limit(limit)
        return [
            {
                "pncp": t.pncp_id,
                "orgao": t.organ,
                "cidade": t.city,
                "estado": t.state,
                "modalidade": t.modality.value,
                "situacao": t.status.value,
                "publicacao": t.publish_date,
                "abertura": t.opening_date,
                "valor": float(t.estimated_value or 0),
            }
            for t in self.session.execute(stmt).scalars().all()
        ]

    # -- Cobertura ---------------------------------------------------------- #
    def ncm_demand(self, start: date, end: date, limit: int = 40) -> list[dict]:
        """Por NCM: quanto o poder público licitou e se temos aquilo no catálogo."""
        stmt = (
            select(
                TenderItem.ncm,
                func.count(func.distinct(Tender.id)).label("licitacoes"),
                _VALOR_ITEM.label("valor"),
                func.max(CatalogItem.description).label("no_catalogo"),
                func.max(TenderItem.description).label("descricao"),
            )
            .join(Tender, Tender.id == TenderItem.tender_id)
            .join(CatalogItem, CatalogItem.ncm == TenderItem.ncm, isouter=True)
            .where(Tender.publish_date >= start, Tender.publish_date <= end)
            .group_by(TenderItem.ncm)
            .order_by(_VALOR_ITEM.desc())
            .limit(limit)
        )
        return [
            {
                "ncm": ncm,
                "licitacoes": int(licitacoes or 0),
                "valor": float(valor or 0),
                "no_catalogo": catalogo is not None,
                "descricao": descricao,
            }
            for ncm, licitacoes, valor, catalogo, descricao in self.session.execute(stmt).all()
        ]


class PriceRecordRepository(BaseRepository[PriceRecord]):
    model = PriceRecord

    def active(self, today: date) -> list[dict]:
        """Atas vigentes, com o preço da ata ao lado do nosso preço de catálogo."""
        stmt = (
            select(PriceRecord, CatalogItem.our_price, CatalogItem.description)
            .join(CatalogItem, CatalogItem.ncm == PriceRecord.ncm, isouter=True)
            .where(PriceRecord.valid_until >= today)
            .order_by(PriceRecord.valid_until)
        )
        atas = []
        for ata, nosso_preco, descricao in self.session.execute(stmt).all():
            preco_ata = float(ata.unit_price or 0)
            nosso = float(nosso_preco) if nosso_preco is not None else None
            # Gap positivo = a ata paga mais do que cobramos (espaço para entrar).
            gap = ((preco_ata - nosso) / nosso * 100) if nosso else None
            atas.append(
                {
                    "ncm": ata.ncm,
                    "descricao": descricao or "fora do catálogo",
                    "orgao": ata.organ,
                    "fornecedor": ata.supplier,
                    "preco_ata": preco_ata,
                    "nosso_preco": nosso,
                    "gap_pct": gap,
                    "quantidade": float(ata.quantity or 0),
                    "valida_ate": ata.valid_until,
                    "dias": (ata.valid_until - today).days,
                }
            )
        return atas


class CatalogRepository(BaseRepository[CatalogItem]):
    model = CatalogItem

    def all_items(self) -> list[dict]:
        stmt = select(CatalogItem).order_by(CatalogItem.family, CatalogItem.description)
        return [
            {
                "ncm": item.ncm,
                "descricao": item.description,
                "familia": item.family,
                "nosso_preco": float(item.our_price or 0),
            }
            for item in self.session.execute(stmt).scalars().all()
        ]

    def ncm_set(self) -> set[str]:
        return {ncm for (ncm,) in self.session.execute(select(CatalogItem.ncm)).all()}
