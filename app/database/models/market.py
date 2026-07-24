"""Descoberta de Mercado: espelho sintético da base pública de empresas (Receita).

Uma linha por empresa (CNPJ), com o recorte que interessa à prospecção:
atividade econômica (CNAE), praça, porte, situação cadastral e idade. É a
base que o módulo cruza para responder "onde estão as empresas que eu
deveria estar atendendo e ainda não atendo".
"""
from __future__ import annotations

import enum
from datetime import date

from sqlalchemy import Date, Enum, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base
from app.database.models.core import TimestampMixin


class CompanySize(str, enum.Enum):
    MEI = "mei"
    ME = "me"
    EPP = "epp"
    DEMAIS = "demais"


class CompanyStatus(str, enum.Enum):
    ATIVA = "ativa"
    BAIXADA = "baixada"
    SUSPENSA = "suspensa"
    INAPTA = "inapta"


class MarketCompany(TimestampMixin, Base):
    __tablename__ = "market_companies"

    id: Mapped[int] = mapped_column(primary_key=True)
    cnpj: Mapped[str] = mapped_column(String(18), unique=True, index=True)
    legal_name: Mapped[str] = mapped_column(String(160))
    trade_name: Mapped[str | None] = mapped_column(String(160), nullable=True)
    cnae_code: Mapped[str] = mapped_column(String(10), index=True)
    cnae_label: Mapped[str] = mapped_column(String(120))
    city: Mapped[str] = mapped_column(String(80))
    state: Mapped[str] = mapped_column(String(2), index=True)
    size: Mapped[CompanySize] = mapped_column(Enum(CompanySize), index=True)
    status: Mapped[CompanyStatus] = mapped_column(Enum(CompanyStatus), index=True)
    opening_date: Mapped[date] = mapped_column(Date)
    share_capital: Mapped[float] = mapped_column(Numeric(14, 2))
