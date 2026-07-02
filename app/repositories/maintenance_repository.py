"""Data access for the Maintenance module."""
from __future__ import annotations

from datetime import date

from sqlalchemy import func, select

from app.database.models.maintenance import (
    Asset,
    AssetCriticality,
    MaintenanceLog,
    MaintenanceRequest,
    MaintenanceStatus,
)
from app.repositories.base import BaseRepository

_OPEN_STATUSES = (
    MaintenanceStatus.OPEN,
    MaintenanceStatus.SCHEDULED,
    MaintenanceStatus.IN_PROGRESS,
)


class AssetRepository(BaseRepository[Asset]):
    model = Asset

    def by_criticality(self, criticality: AssetCriticality) -> list[Asset]:
        stmt = select(Asset).where(Asset.criticality == criticality)
        return list(self.session.execute(stmt).scalars().all())


class MaintenanceRequestRepository(BaseRepository[MaintenanceRequest]):
    model = MaintenanceRequest

    def requests_between(self, start: date, end: date) -> list[MaintenanceRequest]:
        stmt = select(MaintenanceRequest).where(
            MaintenanceRequest.opened_date >= start, MaintenanceRequest.opened_date <= end
        )
        return list(self.session.execute(stmt).scalars().all())

    def by_status(self, status: MaintenanceStatus) -> list[MaintenanceRequest]:
        stmt = select(MaintenanceRequest).where(MaintenanceRequest.status == status)
        return list(self.session.execute(stmt).scalars().all())

    def open_by_priority(self) -> list[tuple[str, int]]:
        stmt = (
            select(MaintenanceRequest.priority, func.count().label("total"))
            .where(MaintenanceRequest.status.in_(_OPEN_STATUSES))
            .group_by(MaintenanceRequest.priority)
            .order_by(func.count().desc())
        )
        return [(priority.value, count) for priority, count in self.session.execute(stmt).all()]


class MaintenanceLogRepository(BaseRepository[MaintenanceLog]):
    model = MaintenanceLog

    def cost_by_month(self, start: date, end: date) -> list[tuple[str, float]]:
        stmt = (
            select(
                func.strftime("%Y-%m", MaintenanceLog.log_date).label("month"),
                func.sum(MaintenanceLog.cost).label("total_cost"),
            )
            .where(MaintenanceLog.log_date >= start, MaintenanceLog.log_date <= end)
            .group_by("month")
            .order_by("month")
        )
        return [(month, round(float(total_cost or 0), 2)) for month, total_cost in self.session.execute(stmt).all()]
