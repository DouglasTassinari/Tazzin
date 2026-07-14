"""Scrap (Refugo) module schema: ScrapRecord, ScrapPart."""
from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import DateTime, ForeignKey, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base
from app.database.models.core import TimestampMixin


class ScrapPart(Base):
    __tablename__ = "machining_scrap_parts"
    __table_args__ = (
        UniqueConstraint("supplier", "part_code", "item_code", name="uq_scrap_part"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    supplier: Mapped[str] = mapped_column(String(120), index=True)
    part_code: Mapped[str] = mapped_column(String(40))
    item_code: Mapped[str] = mapped_column(String(40))
    active: Mapped[bool] = mapped_column(default=True)


class ScrapRecord(TimestampMixin, Base):
    __tablename__ = "machining_scrap_records"

    id: Mapped[int] = mapped_column(primary_key=True)
    record_date: Mapped[date] = mapped_column(index=True)
    operator_id: Mapped[int] = mapped_column(
        ForeignKey("machining_operators.id"), index=True
    )
    machine_id: Mapped[int] = mapped_column(
        ForeignKey("machining_machines.id"), index=True
    )
    work_order_number: Mapped[str | None] = mapped_column(String(20), nullable=True, index=True)
    part_code: Mapped[str | None] = mapped_column(String(40), nullable=True)
    part_description: Mapped[str | None] = mapped_column(String(200), nullable=True)
    supplier: Mapped[str | None] = mapped_column(String(120), nullable=True, index=True)

    reason_1: Mapped[str] = mapped_column(String(120))
    quantity_1: Mapped[int] = mapped_column(default=0)
    notes_1: Mapped[str | None] = mapped_column(String(300), nullable=True)

    reason_2: Mapped[str | None] = mapped_column(String(120), nullable=True)
    quantity_2: Mapped[int | None] = mapped_column(nullable=True)
    notes_2: Mapped[str | None] = mapped_column(String(300), nullable=True)

    reason_3: Mapped[str | None] = mapped_column(String(120), nullable=True)
    quantity_3: Mapped[int | None] = mapped_column(nullable=True)
    notes_3: Mapped[str | None] = mapped_column(String(300), nullable=True)

    total_quantity: Mapped[int] = mapped_column()
    pending: Mapped[bool] = mapped_column(default=False)
    active: Mapped[bool] = mapped_column(default=True, index=True)

    @property
    def origin(self) -> str:
        if self.reason_1 == "Dimensional Errado Usinagem":
            return "usinagem"
        if self.reason_1 == "Outros":
            return "indefinido"
        return "fornecedor"
