"""Data access for Bônus dos Distribuidores."""
from __future__ import annotations

from datetime import date

from sqlalchemy import func, select

from app.database.models.sales import (
    Customer,
    CustomerSegment,
    OrderStatus,
    SalesOrder,
    SalesOrderItem,
)
from app.repositories.base import BaseRepository


class BonusRepository(BaseRepository[Customer]):
    model = Customer

    def distributor_orders(self, start: date, end: date) -> list[dict]:
        """Pedidos faturados dos distribuidores (clientes de atacado) no período."""
        bruto = func.sum(SalesOrderItem.quantity * SalesOrderItem.unit_price)
        stmt = (
            select(Customer.id, Customer.name, Customer.state, SalesOrder.order_date,
                   SalesOrder.discount_pct, bruto)
            .join(SalesOrder, SalesOrder.customer_id == Customer.id)
            .join(SalesOrderItem, SalesOrderItem.order_id == SalesOrder.id)
            .where(Customer.segment == CustomerSegment.WHOLESALE,
                   SalesOrder.status == OrderStatus.INVOICED,
                   SalesOrder.order_date.between(start, end))
            .group_by(SalesOrder.id)
        )
        return [
            {"cliente_id": cid, "nome": nome, "uf": uf, "data": data,
             "valor": round(float(total or 0) * (1 - float(desc or 0) / 100), 2)}
            for cid, nome, uf, data, desc, total in self.session.execute(stmt).all()
        ]
