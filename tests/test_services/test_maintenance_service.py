from datetime import date

import pytest

from app.core.exceptions import EntityNotFoundError, ValidationError
from app.database.models.maintenance import (
    Asset,
    AssetCategory,
    AssetCriticality,
    MaintenancePriority,
    MaintenanceRequestType,
    MaintenanceStatus,
)
from app.services.maintenance_service import MaintenanceService


def _make_asset(session, location) -> Asset:
    asset = Asset(
        asset_tag="AST-9",
        name="Forklift",
        location_id=location.id,
        category=AssetCategory.VEHICLE,
        install_date=date(2019, 6, 1),
        criticality=AssetCriticality.HIGH,
    )
    session.add(asset)
    session.flush()
    return asset


def test_open_request_persists_in_open_status(session, location):
    asset = _make_asset(session, location)
    service = MaintenanceService(session)

    request = service.open_request(
        asset_id=asset.id,
        request_type=MaintenanceRequestType.CORRECTIVE,
        priority=MaintenancePriority.HIGH,
        opened_date=date(2026, 3, 1),
    )

    assert request.id is not None
    assert request.status == MaintenanceStatus.OPEN


def test_log_work_validates_and_appends_log(session, location):
    asset = _make_asset(session, location)
    service = MaintenanceService(session)
    request = service.open_request(
        asset_id=asset.id,
        request_type=MaintenanceRequestType.PREVENTIVE,
        priority=MaintenancePriority.LOW,
        opened_date=date(2026, 3, 1),
    )

    log = service.log_work(request.id, date(2026, 3, 2), hours_spent=2.5, cost=120.0)

    assert log.id is not None
    assert request.logs == [log]


def test_log_work_rejects_invalid_hours(session, location):
    asset = _make_asset(session, location)
    service = MaintenanceService(session)
    request = service.open_request(
        asset_id=asset.id,
        request_type=MaintenanceRequestType.PREVENTIVE,
        priority=MaintenancePriority.LOW,
        opened_date=date(2026, 3, 1),
    )

    with pytest.raises(ValidationError):
        service.log_work(request.id, date(2026, 3, 2), hours_spent=0, cost=10)


def test_transition_request_follows_allowed_path(session, location):
    asset = _make_asset(session, location)
    service = MaintenanceService(session)
    request = service.open_request(
        asset_id=asset.id,
        request_type=MaintenanceRequestType.CORRECTIVE,
        priority=MaintenancePriority.URGENT,
        opened_date=date(2026, 3, 1),
    )

    updated = service.transition_request(request.id, MaintenanceStatus.SCHEDULED)
    assert updated.status == MaintenanceStatus.SCHEDULED

    with pytest.raises(ValidationError):
        service.transition_request(request.id, MaintenanceStatus.COMPLETED)


def test_transition_unknown_request_raises_not_found(session):
    service = MaintenanceService(session)
    with pytest.raises(EntityNotFoundError):
        service.transition_request(999, MaintenanceStatus.SCHEDULED)
