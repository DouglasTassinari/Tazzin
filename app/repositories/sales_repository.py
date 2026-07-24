"""Data access for the Sales module."""
from __future__ import annotations

from datetime import date, timedelta

from sqlalchemy import func, select

from app.database.models.sales import Customer, OrderStatus, SalesOrder, SalesOrderItem
from app.repositories.base import BaseRepository


class CustomerRepository(BaseRepository[Customer]):
    model = Customer

    def find_by_code(self, code: str) -> Customer | None:
        stmt = select(Customer).where(Customer.code == code)
        return self.session.execute(stmt).scalar_one_or_none()

    def active_customers(self) -> list[Customer]:
        stmt = select(Customer).where(Customer.active.is_(True))
        return list(self.session.execute(stmt).scalars().all())


class SalesOrderRepository(BaseRepository[SalesOrder]):
    model = SalesOrder

    def orders_between(self, start: date, end: date) -> list[SalesOrder]:
        stmt = select(SalesOrder).where(
            SalesOrder.order_date >= start, SalesOrder.order_date <= end
        )
        return list(self.session.execute(stmt).scalars().all())

    def by_status(self, status: OrderStatus) -> list[SalesOrder]:
        stmt = select(SalesOrder).where(SalesOrder.status == status)
        return list(self.session.execute(stmt).scalars().all())

    def revenue_by_month(self, start: date, end: date) -> list[tuple[str, float]]:
        """Net revenue (gross minus discount) grouped by calendar month."""
        stmt = (
            select(
                func.strftime("%Y-%m", SalesOrder.order_date).label("month"),
                func.sum(SalesOrderItem.quantity * SalesOrderItem.unit_price).label("gross"),
                func.avg(SalesOrder.discount_pct).label("avg_discount"),
            )
            .join(SalesOrderItem, SalesOrderItem.order_id == SalesOrder.id)
            .where(SalesOrder.order_date >= start, SalesOrder.order_date <= end)
            .where(SalesOrder.status != OrderStatus.CANCELLED)
            .group_by("month")
            .order_by("month")
        )
        rows = self.session.execute(stmt).all()
        return [
            (month, round(float(gross or 0) * (1 - float(avg_discount or 0) / 100), 2))
            for month, gross, avg_discount in rows
        ]

    def revenue_by_day(self, start: date, end: date) -> list[tuple[str, float, int]]:
        """Receita líquida por dia: ``(dia, receita, nº de pedidos)``.

        Mesmo cálculo de líquido do :meth:`revenue_by_month` (bruto menos o
        desconto médio), só que agrupado por data — é a base da Tabela Diária.
        """
        stmt = (
            select(
                func.strftime("%Y-%m-%d", SalesOrder.order_date).label("dia"),
                func.sum(SalesOrderItem.quantity * SalesOrderItem.unit_price).label("gross"),
                func.avg(SalesOrder.discount_pct).label("avg_discount"),
                func.count(func.distinct(SalesOrder.id)).label("pedidos"),
            )
            .join(SalesOrderItem, SalesOrderItem.order_id == SalesOrder.id)
            .where(SalesOrder.order_date >= start, SalesOrder.order_date <= end)
            .where(SalesOrder.status != OrderStatus.CANCELLED)
            .group_by("dia")
            .order_by("dia")
        )
        return [
            (dia, round(float(gross or 0) * (1 - float(avg_discount or 0) / 100), 2), int(pedidos or 0))
            for dia, gross, avg_discount, pedidos in self.session.execute(stmt).all()
        ]

    def revenue_by_segment(self, start: date, end: date) -> list[tuple[str, float]]:
        """Gross revenue grouped by customer segment (enum value, total)."""
        total = func.sum(SalesOrderItem.quantity * SalesOrderItem.unit_price)
        stmt = (
            select(Customer.segment, total.label("total"))
            .join(SalesOrder, SalesOrder.customer_id == Customer.id)
            .join(SalesOrderItem, SalesOrderItem.order_id == SalesOrder.id)
            .where(SalesOrder.order_date >= start, SalesOrder.order_date <= end)
            .where(SalesOrder.status != OrderStatus.CANCELLED)
            .group_by(Customer.segment)
            .order_by(total.desc())
        )
        return [(segment.value, round(float(amount), 2)) for segment, amount in self.session.execute(stmt).all()]

    def customer_portfolio(self, today: date, months: int = 36) -> list[dict]:
        """Carteira de clientes ativos para o módulo Relacionamento.

        Para cada cliente ativo devolve a última interação (data do pedido mais
        recente, ignorando cancelados) e o faturamento dos últimos ``months``
        meses — base da classe econômica. Duas consultas agregadas mescladas em
        memória por id do cliente (SQLite não tem ``FILTER`` amplo).
        """
        cutoff = today - timedelta(days=round(months * 30.4))
        last_stmt = (
            select(
                Customer.id,
                Customer.name,
                Customer.segment,
                Customer.city,
                Customer.state,
                func.max(SalesOrder.order_date).label("last"),
            )
            .join(SalesOrder, SalesOrder.customer_id == Customer.id)
            .where(Customer.active.is_(True), SalesOrder.status != OrderStatus.CANCELLED)
            .group_by(Customer.id)
        )
        rev_stmt = (
            select(
                SalesOrder.customer_id,
                func.sum(SalesOrderItem.quantity * SalesOrderItem.unit_price),
            )
            .join(SalesOrderItem, SalesOrderItem.order_id == SalesOrder.id)
            .where(
                SalesOrder.status != OrderStatus.CANCELLED,
                SalesOrder.order_date >= cutoff,
            )
            .group_by(SalesOrder.customer_id)
        )
        revenue = {
            cid: float(total or 0) for cid, total in self.session.execute(rev_stmt).all()
        }
        return [
            {
                "id": cid,
                "cliente": name,
                "segmento": segment.value,
                "cidade": city,
                "estado": state,
                "ultima_interacao": last,
                "faturamento_36m": revenue.get(cid, 0.0),
            }
            for cid, name, segment, city, state, last in self.session.execute(last_stmt).all()
        ]

    def open_proposals(self) -> list[dict]:
        """Propostas em aberto para o Radar: pedidos DRAFT/CONFIRMED ainda não
        expedidos nem faturados. Valor líquido (bruto − desconto) por proposta.
        """
        gross = func.sum(SalesOrderItem.quantity * SalesOrderItem.unit_price)
        stmt = (
            select(
                SalesOrder.id,
                SalesOrder.order_number,
                Customer.name,
                Customer.segment,
                SalesOrder.order_date,
                SalesOrder.status,
                SalesOrder.discount_pct,
                gross.label("gross"),
            )
            .join(Customer, Customer.id == SalesOrder.customer_id)
            .join(SalesOrderItem, SalesOrderItem.order_id == SalesOrder.id)
            .where(SalesOrder.status.in_([OrderStatus.DRAFT, OrderStatus.CONFIRMED]))
            .group_by(SalesOrder.id)
        )
        propostas = []
        for oid, numero, cliente, segmento, criacao, status, desconto, bruto in (
            self.session.execute(stmt).all()
        ):
            valor = round(float(bruto or 0) * (1 - float(desconto or 0) / 100), 2)
            propostas.append(
                {
                    "id": oid,
                    "numero": numero,
                    "cliente": cliente,
                    "segmento": segmento.value,
                    "data_criacao": criacao,
                    "status": status.value,
                    "valor": valor,
                }
            )
        return propostas

    def top_customers(self, start: date, end: date, limit: int = 10) -> list[tuple[str, float]]:
        stmt = (
            select(
                Customer.name,
                func.sum(SalesOrderItem.quantity * SalesOrderItem.unit_price).label("total"),
            )
            .join(SalesOrder, SalesOrder.customer_id == Customer.id)
            .join(SalesOrderItem, SalesOrderItem.order_id == SalesOrder.id)
            .where(SalesOrder.order_date >= start, SalesOrder.order_date <= end)
            .where(SalesOrder.status != OrderStatus.CANCELLED)
            .group_by(Customer.id)
            .order_by(func.sum(SalesOrderItem.quantity * SalesOrderItem.unit_price).desc())
            .limit(limit)
        )
        return [(name, round(float(total), 2)) for name, total in self.session.execute(stmt).all()]
