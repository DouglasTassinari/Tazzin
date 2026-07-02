"""Maintenance module schema: Asset, MaintenanceRequest, MaintenanceLog."""
from __future__ import annotations

import enum
from datetime import date

from sqlalchemy import Date, Enum, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.database.models.core import TimestampMixin


class AssetCategory(str, enum.Enum):
    MACHINE = "machine"
    VEHICLE = "vehicle"
    FACILITY = "facility"
    IT_EQUIPMENT = "it_equipment"


class AssetCriticality(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class MaintenanceRequestType(str, enum.Enum):
    PREVENTIVE = "preventive"
    CORRECTIVE = "corrective"
    PREDICTIVE = "predictive"


class MaintenancePriority(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class MaintenanceStatus(str, enum.Enum):
    OPEN = "open"
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class Asset(TimestampMixin, Base):
    __tablename__ = "maintenance_assets"

    id: Mapped[int] = mapped_column(primary_key=True)
    asset_tag: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(150))
    location_id: Mapped[int] = mapped_column(ForeignKey("locations.id"))
    category: Mapped[AssetCategory] = mapped_column(Enum(AssetCategory))
    install_date: Mapped[date] = mapped_column(Date)
    criticality: Mapped[AssetCriticality] = mapped_column(Enum(AssetCriticality))


class MaintenanceRequest(TimestampMixin, Base):
    __tablename__ = "maintenance_requests"

    id: Mapped[int] = mapped_column(primary_key=True)
    asset_id: Mapped[int] = mapped_column(ForeignKey("maintenance_assets.id"), index=True)
    request_type: Mapped[MaintenanceRequestType] = mapped_column(Enum(MaintenanceRequestType))
    priority: Mapped[MaintenancePriority] = mapped_column(Enum(MaintenancePriority))
    status: Mapped[MaintenanceStatus] = mapped_column(
        Enum(MaintenanceStatus), default=MaintenanceStatus.OPEN
    )
    opened_date: Mapped[date] = mapped_column(Date)
    requested_by_employee_id: Mapped[int | None] = mapped_column(
        ForeignKey("people_employees.id"), nullable=True
    )

    logs: Mapped[list["MaintenanceLog"]] = relationship(
        back_populates="request", cascade="all, delete-orphan"
    )


class MaintenanceLog(Base):
    __tablename__ = "maintenance_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    request_id: Mapped[int] = mapped_column(ForeignKey("maintenance_requests.id"), index=True)
    log_date: Mapped[date] = mapped_column(Date)
    hours_spent: Mapped[float] = mapped_column(Numeric(6, 2))
    cost: Mapped[float] = mapped_column(Numeric(10, 2))
    notes: Mapped[str | None] = mapped_column(String(300), nullable=True)

    request: Mapped["MaintenanceRequest"] = relationship(back_populates="logs")
