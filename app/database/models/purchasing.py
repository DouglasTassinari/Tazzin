"""Purchasing module schema: Supplier, PurchaseOrder, PurchaseOrderItem."""
from __future__ import annotations

import enum
from datetime import date

from sqlalchemy import Date, Enum, ForeignKey, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.database.models.core import TimestampMixin


class SupplierCategory(str, enum.Enum):
    RAW_MATERIAL = "raw_material"
    SERVICES = "services"
    EQUIPMENT = "equipment"
    PACKAGING = "packaging"


class PurchaseOrderStatus(str, enum.Enum):
    DRAFT = "draft"
    SENT = "sent"
    CONFIRMED = "confirmed"
    RECEIVED = "received"
    CANCELLED = "cancelled"


class Supplier(TimestampMixin, Base):
    __tablename__ = "purchasing_suppliers"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(15), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(150))
    category: Mapped[SupplierCategory] = mapped_column(Enum(SupplierCategory))
    city: Mapped[str] = mapped_column(String(80))
    state: Mapped[str] = mapped_column(String(80))
    rating: Mapped[float] = mapped_column(Numeric(3, 2), default=3.0)


class PurchaseOrder(TimestampMixin, Base):
    __tablename__ = "purchasing_orders"

    id: Mapped[int] = mapped_column(primary_key=True)
    order_number: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    supplier_id: Mapped[int] = mapped_column(ForeignKey("purchasing_suppliers.id"), index=True)
    location_id: Mapped[int] = mapped_column(ForeignKey("locations.id"))
    status: Mapped[PurchaseOrderStatus] = mapped_column(
        Enum(PurchaseOrderStatus), default=PurchaseOrderStatus.DRAFT
    )
    order_date: Mapped[date] = mapped_column(Date)
    expected_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    items: Mapped[list["PurchaseOrderItem"]] = relationship(
        back_populates="purchase_order", cascade="all, delete-orphan"
    )

    @property
    def total_cost(self) -> float:
        return round(sum(item.quantity * float(item.unit_cost) for item in self.items), 2)


class PurchaseOrderItem(Base):
    __tablename__ = "purchasing_order_items"
    __table_args__ = (
        UniqueConstraint("purchase_order_id", "product_id", name="uq_po_product"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    purchase_order_id: Mapped[int] = mapped_column(
        ForeignKey("purchasing_orders.id"), index=True
    )
    product_id: Mapped[int] = mapped_column(ForeignKey("inventory_products.id"), index=True)
    quantity: Mapped[int] = mapped_column()
    unit_cost: Mapped[float] = mapped_column(Numeric(10, 2))

    purchase_order: Mapped["PurchaseOrder"] = relationship(back_populates="items")
