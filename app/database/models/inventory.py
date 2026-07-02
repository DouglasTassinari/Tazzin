"""Inventory module schema: Product, Warehouse, StockMovement."""
from __future__ import annotations

import enum
from datetime import date

from sqlalchemy import Boolean, Date, Enum, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base
from app.database.models.core import TimestampMixin


class ProductCategory(str, enum.Enum):
    RAW_MATERIAL = "raw_material"
    COMPONENT = "component"
    FINISHED_GOOD = "finished_good"
    PACKAGING = "packaging"


class MovementType(str, enum.Enum):
    INBOUND = "inbound"
    OUTBOUND = "outbound"
    ADJUSTMENT = "adjustment"
    TRANSFER = "transfer"


class Warehouse(TimestampMixin, Base):
    __tablename__ = "inventory_warehouses"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(10), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(120))
    location_id: Mapped[int] = mapped_column(ForeignKey("locations.id"))
    capacity_units: Mapped[int] = mapped_column(default=0)


class Product(TimestampMixin, Base):
    __tablename__ = "inventory_products"

    id: Mapped[int] = mapped_column(primary_key=True)
    sku: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(150))
    category: Mapped[ProductCategory] = mapped_column(Enum(ProductCategory))
    unit_cost: Mapped[float] = mapped_column(Numeric(10, 2))
    unit_price: Mapped[float] = mapped_column(Numeric(10, 2))
    reorder_point: Mapped[int] = mapped_column(default=0)
    active: Mapped[bool] = mapped_column(Boolean, default=True)


class StockMovement(Base):
    __tablename__ = "inventory_stock_movements"

    id: Mapped[int] = mapped_column(primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("inventory_products.id"), index=True)
    warehouse_id: Mapped[int] = mapped_column(ForeignKey("inventory_warehouses.id"), index=True)
    movement_type: Mapped[MovementType] = mapped_column(Enum(MovementType))
    quantity: Mapped[int] = mapped_column()
    movement_date: Mapped[date] = mapped_column(Date)
    reference_note: Mapped[str | None] = mapped_column(String(200), nullable=True)
