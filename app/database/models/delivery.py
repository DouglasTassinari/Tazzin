"""Prazo de Entrega: data prometida e data real de entrega de cada pedido despachado."""
from __future__ import annotations

from datetime import date

from sqlalchemy import Date, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base
from app.database.models.core import TimestampMixin


class OrderDelivery(TimestampMixin, Base):
    __tablename__ = "delivery_orders"

    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("sales_orders.id"), unique=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("sales_customers.id"), index=True)
    promised_date: Mapped[date] = mapped_column(Date, index=True)
    delivered_date: Mapped[date | None] = mapped_column(Date, nullable=True)  # None = ainda não entregue
