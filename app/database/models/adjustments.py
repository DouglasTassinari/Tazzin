"""Time Adjustments (Ajustes) module schema: TimeAdjustment."""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base
from app.database.models.core import TimestampMixin


class TimeAdjustment(TimestampMixin, Base):
    __tablename__ = "machining_time_adjustments"

    id: Mapped[int] = mapped_column(primary_key=True)
    record_date: Mapped[datetime] = mapped_column(DateTime, index=True)
    work_order_number: Mapped[str | None] = mapped_column(String(20), nullable=True, index=True)
    operator_id: Mapped[int] = mapped_column(
        ForeignKey("machining_operators.id"), index=True
    )
    machine_id: Mapped[int] = mapped_column(
        ForeignKey("machining_machines.id"), index=True
    )
    part_code: Mapped[str | None] = mapped_column(String(40), nullable=True)
    part_description: Mapped[str | None] = mapped_column(String(200), nullable=True)
    quantity: Mapped[float] = mapped_column(Numeric(14, 4), default=0)
    operation: Mapped[str] = mapped_column(String(80))
    previous_time_seconds: Mapped[float] = mapped_column(Numeric(14, 4))
    current_time_seconds: Mapped[float] = mapped_column(Numeric(14, 4))
    justification: Mapped[str] = mapped_column(String(500))
    active: Mapped[bool] = mapped_column(default=True, index=True)

    @property
    def difference_seconds(self) -> float:
        return float(self.previous_time_seconds) - float(self.current_time_seconds)

    @property
    def is_improvement(self) -> bool:
        return self.difference_seconds > 0
