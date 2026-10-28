"""Data access for Prazo de Entrega."""
from __future__ import annotations

from datetime import date

from sqlalchemy import select

from app.database.models.delivery import OrderDelivery
from app.database.models.sales import Customer, SalesOrder
from app.repositories.base import BaseRepository


class DeliveryRepository(BaseRepository[OrderDelivery]):
    model = OrderDelivery

    def rows(self, start: date, end: date) -> list[dict]:
        """Entregas com data prometida na janela, com pedido e cliente."""
        stmt = (
            select(OrderDelivery, SalesOrder.order_number, Customer.name, Customer.segment)
            .join(SalesOrder, SalesOrder.id == OrderDelivery.order_id)
            .join(Customer, Customer.id == OrderDelivery.customer_id)
            .where(OrderDelivery.promised_date.between(start, end))
        )
        return [
            {"pedido": numero, "cliente": cliente, "segmento": seg.value,
             "prometida": d.promised_date, "entregue": d.delivered_date}
            for d, numero, cliente, seg in self.session.execute(stmt).all()
        ]
