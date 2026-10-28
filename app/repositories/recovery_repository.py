"""Data access for Recuperação de Clientes."""
from __future__ import annotations

from datetime import date

from sqlalchemy import func, select

from app.database.models.people import Employee
from app.database.models.recovery import RecoveryContact
from app.database.models.sales import (
    Customer,
    OrderStatus,
    SalesOrder,
    SalesOrderItem,
)
from app.repositories.base import BaseRepository

# Compra efetivada: pedido já despachado ou faturado.
_COMPRAS = (OrderStatus.SHIPPED, OrderStatus.INVOICED)


class RecoveryRepository(BaseRepository[RecoveryContact]):
    model = RecoveryContact

    def purchases(self) -> list[dict]:
        """Uma linha por compra efetivada, com o valor líquido do pedido."""
        bruto = func.sum(SalesOrderItem.quantity * SalesOrderItem.unit_price)
        stmt = (
            select(SalesOrder.id, SalesOrder.customer_id, SalesOrder.order_date,
                   SalesOrder.discount_pct, bruto)
            .join(SalesOrderItem, SalesOrderItem.order_id == SalesOrder.id)
            .where(SalesOrder.status.in_(_COMPRAS))
            .group_by(SalesOrder.id)
        )
        return [
            {"pedido": oid, "cliente_id": cid, "data": data,
             "valor": round(float(total or 0) * (1 - float(desc or 0) / 100), 2)}
            for oid, cid, data, desc, total in self.session.execute(stmt).all()
        ]

    def customers(self) -> dict[int, dict]:
        stmt = select(Customer.id, Customer.name, Customer.segment, Customer.city, Customer.state)
        return {
            cid: {"nome": nome, "segmento": seg.value, "cidade": f"{cidade}/{uf}"}
            for cid, nome, seg, cidade, uf in self.session.execute(stmt).all()
        }

    def contacts(self, start: date, end: date) -> list[dict]:
        """Contatos do período, com cliente, responsável e valor recuperado."""
        stmt = (
            select(RecoveryContact, Customer.name, Customer.segment, Employee.full_name)
            .join(Customer, Customer.id == RecoveryContact.customer_id)
            .join(Employee, Employee.id == RecoveryContact.owner_employee_id, isouter=True)
            .where(RecoveryContact.contact_date.between(start, end))
        )
        valores = {p["pedido"]: p["valor"] for p in self.purchases()}
        return [
            {
                "cliente_id": c.customer_id, "cliente": cliente, "segmento": seg.value,
                "data": c.contact_date, "canal": c.channel.value, "resultado": c.result.value,
                "responsavel": resp or "sem dono",
                "recuperado": valores.get(c.recovered_order_id, 0.0) if c.recovered_order_id else 0.0,
                "anotacao": c.note,
            }
            for c, cliente, seg, resp in self.session.execute(stmt).all()
        ]

    def last_contacts(self) -> dict[int, date]:
        stmt = select(RecoveryContact.customer_id, func.max(RecoveryContact.contact_date)).group_by(
            RecoveryContact.customer_id
        )
        return {cid: data for cid, data in self.session.execute(stmt).all()}
