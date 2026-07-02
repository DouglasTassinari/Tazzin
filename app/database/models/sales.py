"""Sales module schema: Customer, SalesOrder, SalesOrderItem.

Cross-module references (e.g. ``SalesOrderItem.product_id`` pointing at
``inventory.products``) are plain foreign-key columns without an ORM
``relationship()``. This is a deliberate low-coupling choice: modules
stay independently deployable/testable and only agree on an id contract,
never on each other's mapped classes. Relationships *within* a module
(Customer -> SalesOrder -> SalesOrderItem) do use ``relationship()``
since that cohesion is intentional.
"""
from __future__ import annotations

import enum
from datetime import date

from sqlalchemy import Date, Enum, ForeignKey, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.database.models.core import TimestampMixin


class CustomerSegment(str, enum.Enum):
    RETAIL = "retail"
    WHOLESALE = "wholesale"
    ENTERPRISE = "enterprise"


class OrderStatus(str, enum.Enum):
    DRAFT = "draft"
    CONFIRMED = "confirmed"
    SHIPPED = "shipped"
    INVOICED = "invoiced"
    CANCELLED = "cancelled"


class Customer(TimestampMixin, Base):
    __tablename__ = "sales_customers"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(15), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(150))
    segment: Mapped[CustomerSegment] = mapped_column(Enum(CustomerSegment))
    city: Mapped[str] = mapped_column(String(80))
    state: Mapped[str] = mapped_column(String(80))
    active: Mapped[bool] = mapped_column(default=True)

    orders: Mapped[list["SalesOrder"]] = relationship(back_populates="customer")


class SalesOrder(TimestampMixin, Base):
    __tablename__ = "sales_orders"

    id: Mapped[int] = mapped_column(primary_key=True)
    order_number: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("sales_customers.id"), index=True)
    location_id: Mapped[int] = mapped_column(ForeignKey("locations.id"))
    status: Mapped[OrderStatus] = mapped_column(Enum(OrderStatus), default=OrderStatus.DRAFT)
    order_date: Mapped[date] = mapped_column(Date)
    discount_pct: Mapped[float] = mapped_column(Numeric(5, 2), default=0)

    customer: Mapped["Customer"] = relationship(back_populates="orders")
    items: Mapped[list["SalesOrderItem"]] = relationship(
        back_populates="order", cascade="all, delete-orphan"
    )

    @property
    def gross_amount(self) -> float:
        return sum(item.line_total for item in self.items)

    @property
    def net_amount(self) -> float:
        return round(float(self.gross_amount) * (1 - float(self.discount_pct) / 100), 2)


class SalesOrderItem(Base):
    __tablename__ = "sales_order_items"
    __table_args__ = (UniqueConstraint("order_id", "product_id", name="uq_order_product"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("sales_orders.id"), index=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("inventory_products.id"), index=True)
    quantity: Mapped[int] = mapped_column()
    unit_price: Mapped[float] = mapped_column(Numeric(10, 2))

    order: Mapped["SalesOrder"] = relationship(back_populates="items")

    @property
    def line_total(self) -> float:
        return round(float(self.quantity) * float(self.unit_price), 2)
