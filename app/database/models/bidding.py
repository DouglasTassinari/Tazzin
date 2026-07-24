"""Inteligência de Licitações: compras públicas (PNCP) cruzadas por NCM.

Quatro peças que se conversam:

* :class:`Tender` — a licitação publicada (órgão, praça, modalidade, valor).
* :class:`TenderItem` — o item disputado, com o **NCM** que é a chave do
  cruzamento com o que a empresa vende.
* :class:`PriceRecord` — a ata de registro de preços que sobrou da licitação
  homologada: o preço que o concorrente conseguiu segurar.
* :class:`CatalogItem` — o catálogo próprio por NCM, que define se aquela
  licitação é ou não uma oportunidade real.
"""
from __future__ import annotations

import enum
from datetime import date

from sqlalchemy import Date, Enum, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.database.models.core import TimestampMixin


class TenderModality(str, enum.Enum):
    PREGAO_ELETRONICO = "pregao_eletronico"
    DISPENSA = "dispensa"
    CONCORRENCIA = "concorrencia"
    INEXIGIBILIDADE = "inexigibilidade"


class TenderStatus(str, enum.Enum):
    ABERTA = "aberta"
    HOMOLOGADA = "homologada"
    FRACASSADA = "fracassada"
    CANCELADA = "cancelada"


class Tender(TimestampMixin, Base):
    __tablename__ = "bidding_tenders"

    id: Mapped[int] = mapped_column(primary_key=True)
    pncp_id: Mapped[str] = mapped_column(String(30), unique=True, index=True)
    organ: Mapped[str] = mapped_column(String(160))
    city: Mapped[str] = mapped_column(String(80))
    state: Mapped[str] = mapped_column(String(2), index=True)
    modality: Mapped[TenderModality] = mapped_column(Enum(TenderModality), index=True)
    status: Mapped[TenderStatus] = mapped_column(Enum(TenderStatus), index=True)
    publish_date: Mapped[date] = mapped_column(Date, index=True)
    opening_date: Mapped[date] = mapped_column(Date)
    estimated_value: Mapped[float] = mapped_column(Numeric(14, 2))

    items: Mapped[list["TenderItem"]] = relationship(
        back_populates="tender", cascade="all, delete-orphan"
    )


class TenderItem(Base):
    __tablename__ = "bidding_tender_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    tender_id: Mapped[int] = mapped_column(ForeignKey("bidding_tenders.id"), index=True)
    ncm: Mapped[str] = mapped_column(String(10), index=True)
    description: Mapped[str] = mapped_column(String(160))
    quantity: Mapped[float] = mapped_column(Numeric(12, 2))
    unit_price: Mapped[float] = mapped_column(Numeric(12, 2))
    awarded_price: Mapped[float | None] = mapped_column(Numeric(12, 2), nullable=True)
    awarded_supplier: Mapped[str | None] = mapped_column(String(160), nullable=True)

    tender: Mapped["Tender"] = relationship(back_populates="items")


class PriceRecord(Base):
    """Ata de registro de preços — o preço que ficou valendo depois da disputa."""

    __tablename__ = "bidding_price_records"

    id: Mapped[int] = mapped_column(primary_key=True)
    tender_id: Mapped[int] = mapped_column(ForeignKey("bidding_tenders.id"), index=True)
    ncm: Mapped[str] = mapped_column(String(10), index=True)
    organ: Mapped[str] = mapped_column(String(160))
    supplier: Mapped[str] = mapped_column(String(160))
    unit_price: Mapped[float] = mapped_column(Numeric(12, 2))
    quantity: Mapped[float] = mapped_column(Numeric(12, 2))
    valid_until: Mapped[date] = mapped_column(Date, index=True)


class CatalogItem(Base):
    """O que a empresa vende, pelo NCM — a chave que abre a oportunidade."""

    __tablename__ = "bidding_catalog_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    ncm: Mapped[str] = mapped_column(String(10), unique=True, index=True)
    description: Mapped[str] = mapped_column(String(160))
    family: Mapped[str] = mapped_column(String(80))
    our_price: Mapped[float] = mapped_column(Numeric(12, 2))
