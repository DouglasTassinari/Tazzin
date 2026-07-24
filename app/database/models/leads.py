"""Relacionamento com Leads: quem ainda não comprou.

A diferença para o módulo Relacionamento é essa: lá a fila é da carteira
ativa (já é cliente), aqui é de quem entrou por algum canal e ainda não
virou pedido. O que manda a fila é há quantos dias ninguém encosta no lead.
"""
from __future__ import annotations

import enum
from datetime import date

from sqlalchemy import Date, Enum, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base
from app.database.models.core import TimestampMixin


class LeadOrigin(str, enum.Enum):
    SITE = "site"
    INDICACAO = "indicacao"
    FEIRA = "feira"
    OUTBOUND = "outbound"
    MARKETPLACE = "marketplace"


class LeadStatus(str, enum.Enum):
    NOVO = "novo"
    EM_CONTATO = "em_contato"
    QUALIFICADO = "qualificado"
    DESCARTADO = "descartado"


class Lead(TimestampMixin, Base):
    __tablename__ = "leads"

    id: Mapped[int] = mapped_column(primary_key=True)
    company_name: Mapped[str] = mapped_column(String(160))
    contact_name: Mapped[str] = mapped_column(String(120))
    city: Mapped[str] = mapped_column(String(80))
    state: Mapped[str] = mapped_column(String(2), index=True)
    segment: Mapped[str] = mapped_column(String(20))
    origin: Mapped[LeadOrigin] = mapped_column(Enum(LeadOrigin), index=True)
    status: Mapped[LeadStatus] = mapped_column(Enum(LeadStatus), index=True)
    created_date: Mapped[date] = mapped_column(Date)
    last_contact_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    owner_employee_id: Mapped[int | None] = mapped_column(
        ForeignKey("people_employees.id"), nullable=True
    )
    potential_value: Mapped[float] = mapped_column(Numeric(12, 2))
