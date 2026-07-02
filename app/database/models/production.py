"""Production module schema: ProductionLine, WorkOrder, ProductionEvent."""
from __future__ import annotations

import enum
from datetime import date, datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.database.models.core import TimestampMixin


class WorkOrderStatus(str, enum.Enum):
    PLANNED = "planned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class ProductionEventType(str, enum.Enum):
    START = "start"
    PAUSE = "pause"
    RESUME = "resume"
    STOP = "stop"
    QUALITY_HOLD = "quality_hold"


class ProductionLine(TimestampMixin, Base):
    __tablename__ = "production_lines"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(10), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(120))
    location_id: Mapped[int] = mapped_column(ForeignKey("locations.id"))
    capacity_units_per_hour: Mapped[float] = mapped_column(Numeric(10, 2), default=0)


class WorkOrder(TimestampMixin, Base):
    __tablename__ = "production_work_orders"

    id: Mapped[int] = mapped_column(primary_key=True)
    order_number: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("inventory_products.id"), index=True)
    production_line_id: Mapped[int] = mapped_column(
        ForeignKey("production_lines.id"), index=True
    )
    status: Mapped[WorkOrderStatus] = mapped_column(
        Enum(WorkOrderStatus), default=WorkOrderStatus.PLANNED
    )
    planned_quantity: Mapped[int] = mapped_column()
    produced_quantity: Mapped[int] = mapped_column(default=0)
    scrap_quantity: Mapped[int] = mapped_column(default=0)
    scheduled_date: Mapped[date] = mapped_column()
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    events: Mapped[list["ProductionEvent"]] = relationship(
        back_populates="work_order", cascade="all, delete-orphan"
    )

    @property
    def yield_pct(self) -> float:
        total = self.produced_quantity + self.scrap_quantity
        return round(100 * self.produced_quantity / total, 2) if total else 0.0


class ProductionEvent(Base):
    __tablename__ = "production_events"

    id: Mapped[int] = mapped_column(primary_key=True)
    work_order_id: Mapped[int] = mapped_column(
        ForeignKey("production_work_orders.id"), index=True
    )
    event_type: Mapped[ProductionEventType] = mapped_column(Enum(ProductionEventType))
    event_time: Mapped[datetime] = mapped_column(DateTime)
    notes: Mapped[str | None] = mapped_column(String(200), nullable=True)

    work_order: Mapped["WorkOrder"] = relationship(back_populates="events")
