"""Pós-Vendas: pesquisa de satisfação enviada depois da entrega do pedido.

Uma pesquisa por pedido. A nota de recomendação (0 a 10) alimenta o NPS e a
nota de satisfação (1 a 5), o CSAT. Quem dá nota baixa entra numa fila de
retorno com responsável. Pedido e cliente entram só por identificador, como
nos demais módulos.
"""
from __future__ import annotations

import enum
from datetime import date

from sqlalchemy import Date, Enum, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base
from app.database.models.core import TimestampMixin


class SurveyFollowUp(str, enum.Enum):
    NONE = "none"              # não precisa de retorno (nota boa ou sem resposta)
    PENDING = "pending"        # detrator ainda sem contato
    IN_CONTACT = "in_contact"  # retorno em andamento
    RESOLVED = "resolved"      # retorno concluído


class PostSaleSurvey(TimestampMixin, Base):
    __tablename__ = "postsales_surveys"

    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("sales_orders.id"), unique=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("sales_customers.id"), index=True)
    sent_date: Mapped[date] = mapped_column(Date, index=True)
    responded_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    nps_score: Mapped[int | None] = mapped_column(nullable=True)   # 0 a 10
    csat_score: Mapped[int | None] = mapped_column(nullable=True)  # 1 a 5
    comment: Mapped[str | None] = mapped_column(String(240), nullable=True)
    follow_up: Mapped[SurveyFollowUp] = mapped_column(
        Enum(SurveyFollowUp), default=SurveyFollowUp.NONE, index=True
    )
    owner_employee_id: Mapped[int | None] = mapped_column(
        ForeignKey("people_employees.id"), nullable=True
    )
