"""Maintenance module service — orchestrates repositories + domain rules.

This is the only layer the Streamlit pages talk to for Maintenance data;
pages never import repositories or models directly.
"""
from __future__ import annotations

from datetime import date

from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.core.metrics import track
from app.database.models.maintenance import (
    MaintenanceLog,
    MaintenancePriority,
    MaintenanceRequest,
    MaintenanceRequestType,
    MaintenanceStatus,
)
from app.domain import maintenance_rules
from app.repositories.maintenance_repository import (
    AssetRepository,
    MaintenanceLogRepository,
    MaintenanceRequestRepository,
)

logger = get_logger("services.maintenance")


class MaintenanceService:
    def __init__(self, session: Session):
        self.session = session
        self.assets = AssetRepository(session)
        self.requests = MaintenanceRequestRepository(session)
        self.logs = MaintenanceLogRepository(session)

    @track("maintenance.open_request")
    def open_request(
        self,
        asset_id: int,
        request_type: MaintenanceRequestType,
        priority: MaintenancePriority,
        opened_date: date,
        requested_by_employee_id: int | None = None,
    ) -> MaintenanceRequest:
        request = MaintenanceRequest(
            asset_id=asset_id,
            request_type=request_type,
            priority=priority,
            status=MaintenanceStatus.OPEN,
            opened_date=opened_date,
            requested_by_employee_id=requested_by_employee_id,
        )
        self.requests.add(request)
        logger.info("Opened maintenance request for asset %s", asset_id)
        return request

    @track("maintenance.transition_request")
    def transition_request(self, request_id: int, target_status: MaintenanceStatus) -> MaintenanceRequest:
        request = self.requests.get(request_id)
        maintenance_rules.assert_transition(request.status, target_status)
        request.status = target_status
        self.session.flush()
        logger.info("Request %s moved to %s", request_id, target_status.value)
        return request

    @track("maintenance.log_work")
    def log_work(
        self,
        request_id: int,
        log_date: date,
        hours_spent: float,
        cost: float,
        notes: str | None = None,
    ) -> MaintenanceLog:
        maintenance_rules.validate_log(hours_spent, cost)
        request = self.requests.get(request_id)
        log = MaintenanceLog(
            request_id=request.id,
            log_date=log_date,
            hours_spent=hours_spent,
            cost=cost,
            notes=notes,
        )
        self.logs.add(log)
        logger.info("Logged %.2fh / %.2f cost on request %s", hours_spent, cost, request_id)
        return log

    @track("maintenance.monthly_maintenance_cost")
    def monthly_maintenance_cost(self, start: date, end: date) -> list[tuple[str, float]]:
        return self.logs.cost_by_month(start, end)

    @track("maintenance.open_requests_by_priority")
    def open_requests_by_priority(self) -> list[tuple[str, int]]:
        return self.requests.open_by_priority()
