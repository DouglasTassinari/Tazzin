"""Quality module schema: Inspection, NonConformance, QualityMetric."""
from __future__ import annotations

import enum
from datetime import date

from sqlalchemy import Date, Enum, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.database.models.core import TimestampMixin


class InspectionResult(str, enum.Enum):
    PASS = "pass"
    FAIL = "fail"
    REWORK = "rework"


class NonConformanceSeverity(str, enum.Enum):
    MINOR = "minor"
    MAJOR = "major"
    CRITICAL = "critical"


class NonConformanceStatus(str, enum.Enum):
    OPEN = "open"
    UNDER_REVIEW = "under_review"
    RESOLVED = "resolved"
    CLOSED = "closed"


class Inspection(TimestampMixin, Base):
    __tablename__ = "quality_inspections"

    id: Mapped[int] = mapped_column(primary_key=True)
    work_order_id: Mapped[int | None] = mapped_column(
        ForeignKey("production_work_orders.id"), nullable=True, index=True
    )
    product_id: Mapped[int] = mapped_column(ForeignKey("inventory_products.id"), index=True)
    inspector_employee_id: Mapped[int | None] = mapped_column(
        ForeignKey("people_employees.id"), nullable=True
    )
    inspection_date: Mapped[date] = mapped_column(Date)
    result: Mapped[InspectionResult] = mapped_column(Enum(InspectionResult))
    sample_size: Mapped[int] = mapped_column()
    defect_count: Mapped[int] = mapped_column(default=0)

    nonconformances: Mapped[list["NonConformance"]] = relationship(
        back_populates="inspection", cascade="all, delete-orphan"
    )


class NonConformance(Base):
    __tablename__ = "quality_nonconformances"

    id: Mapped[int] = mapped_column(primary_key=True)
    inspection_id: Mapped[int] = mapped_column(ForeignKey("quality_inspections.id"), index=True)
    severity: Mapped[NonConformanceSeverity] = mapped_column(Enum(NonConformanceSeverity))
    description: Mapped[str] = mapped_column(String(300))
    status: Mapped[NonConformanceStatus] = mapped_column(
        Enum(NonConformanceStatus), default=NonConformanceStatus.OPEN
    )
    opened_date: Mapped[date] = mapped_column(Date)
    closed_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    inspection: Mapped["Inspection"] = relationship(back_populates="nonconformances")


class QualityMetric(Base):
    __tablename__ = "quality_metrics"

    id: Mapped[int] = mapped_column(primary_key=True)
    location_id: Mapped[int] = mapped_column(ForeignKey("locations.id"))
    metric_date: Mapped[date] = mapped_column(Date)
    metric_name: Mapped[str] = mapped_column(String(80))
    metric_value: Mapped[float] = mapped_column(Numeric(10, 4))
