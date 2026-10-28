"""Recuperação de Clientes: contatos feitos para trazer de volta quem parou de comprar.

Cada contato registra o canal e o que o cliente respondeu. Quando o contato
termina em compra, ``recovered_order_id`` aponta o pedido — é daí que sai a
receita recuperada. Cliente e pedido entram só por identificador.
"""
from __future__ import annotations

import enum
from datetime import date

from sqlalchemy import Date, Enum, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base
from app.database.models.core import TimestampMixin


class RecoveryChannel(str, enum.Enum):
    PHONE = "phone"
    WHATSAPP = "whatsapp"
    EMAIL = "email"
    VISIT = "visit"


class RecoveryResult(str, enum.Enum):
    NO_ANSWER = "no_answer"
    INTERESTED = "interested"
    DECLINED = "declined"
    REACTIVATED = "reactivated"


class RecoveryContact(TimestampMixin, Base):
    __tablename__ = "recovery_contacts"

    id: Mapped[int] = mapped_column(primary_key=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("sales_customers.id"), index=True)
    contact_date: Mapped[date] = mapped_column(Date, index=True)
    channel: Mapped[RecoveryChannel] = mapped_column(Enum(RecoveryChannel))
    result: Mapped[RecoveryResult] = mapped_column(Enum(RecoveryResult), index=True)
    recovered_order_id: Mapped[int | None] = mapped_column(ForeignKey("sales_orders.id"), nullable=True)
    owner_employee_id: Mapped[int | None] = mapped_column(
        ForeignKey("people_employees.id"), nullable=True
    )
    note: Mapped[str | None] = mapped_column(String(200), nullable=True)
