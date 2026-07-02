"""Cross-module primitives: timestamp mixin and the shared Location entity.

``Location`` represents a physical site (plant, warehouse or office) and
is referenced by Production, Inventory and People so the synthetic data
set reads like one real company with several sites, not disconnected
demo tables.
"""
from __future__ import annotations

import enum
from datetime import datetime

from sqlalchemy import DateTime, Enum, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )


class LocationType(str, enum.Enum):
    PLANT = "plant"
    WAREHOUSE = "warehouse"
    OFFICE = "office"


class Location(TimestampMixin, Base):
    __tablename__ = "locations"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(10), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(120))
    city: Mapped[str] = mapped_column(String(80))
    state: Mapped[str] = mapped_column(String(80))
    country: Mapped[str] = mapped_column(String(80), default="Brazil")
    location_type: Mapped[LocationType] = mapped_column(Enum(LocationType))

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return f"<Location {self.code} {self.name}>"
