from datetime import date

from app.database.models.maintenance import (
    Asset,
    AssetCategory,
    AssetCriticality,
    MaintenanceLog,
    MaintenancePriority,
    MaintenanceRequest,
    MaintenanceRequestType,
    MaintenanceStatus,
)
from app.repositories.maintenance_repository import (
    AssetRepository,
    MaintenanceLogRepository,
    MaintenanceRequestRepository,
)


def _make_asset(session, location, criticality=AssetCriticality.MEDIUM, tag="AST-1") -> Asset:
    asset = Asset(
        asset_tag=tag,
        name="CNC Machine",
        location_id=location.id,
        category=AssetCategory.MACHINE,
        install_date=date(2020, 1, 1),
        criticality=criticality,
    )
    session.add(asset)
    session.flush()
    return asset


def test_by_criticality_filters_assets(session, location):
    critical = _make_asset(session, location, criticality=AssetCriticality.CRITICAL, tag="AST-CRIT")
    _make_asset(session, location, criticality=AssetCriticality.LOW, tag="AST-LOW")

    repo = AssetRepository(session)
    results = repo.by_criticality(AssetCriticality.CRITICAL)

    assert [a.id for a in results] == [critical.id]


def test_open_by_priority_counts_only_open_statuses(session, location):
    asset = _make_asset(session, location)
    session.add_all(
        [
            MaintenanceRequest(
                asset_id=asset.id,
                request_type=MaintenanceRequestType.CORRECTIVE,
                priority=MaintenancePriority.URGENT,
                status=MaintenanceStatus.OPEN,
                opened_date=date(2026, 1, 1),
            ),
            MaintenanceRequest(
                asset_id=asset.id,
                request_type=MaintenanceRequestType.PREVENTIVE,
                priority=MaintenancePriority.URGENT,
                status=MaintenanceStatus.IN_PROGRESS,
                opened_date=date(2026, 1, 2),
            ),
            MaintenanceRequest(
                asset_id=asset.id,
                request_type=MaintenanceRequestType.PREVENTIVE,
                priority=MaintenancePriority.LOW,
                status=MaintenanceStatus.SCHEDULED,
                opened_date=date(2026, 1, 3),
            ),
            MaintenanceRequest(
                asset_id=asset.id,
                request_type=MaintenanceRequestType.PREVENTIVE,
                priority=MaintenancePriority.LOW,
                status=MaintenanceStatus.COMPLETED,
                opened_date=date(2026, 1, 4),
            ),
        ]
    )
    session.flush()

    repo = MaintenanceRequestRepository(session)
    rows = repo.open_by_priority()

    assert rows[0] == ("urgent", 2)
    assert ("low", 1) in rows
    assert sum(count for _, count in rows) == 3


def test_requests_between_filters_by_opened_date(session, location):
    asset = _make_asset(session, location)
    inside = MaintenanceRequest(
        asset_id=asset.id,
        request_type=MaintenanceRequestType.CORRECTIVE,
        priority=MaintenancePriority.MEDIUM,
        status=MaintenanceStatus.OPEN,
        opened_date=date(2026, 1, 15),
    )
    outside = MaintenanceRequest(
        asset_id=asset.id,
        request_type=MaintenanceRequestType.CORRECTIVE,
        priority=MaintenancePriority.MEDIUM,
        status=MaintenanceStatus.OPEN,
        opened_date=date(2026, 3, 1),
    )
    session.add_all([inside, outside])
    session.flush()

    repo = MaintenanceRequestRepository(session)
    rows = repo.requests_between(date(2026, 1, 1), date(2026, 1, 31))

    assert [r.id for r in rows] == [inside.id]


def test_cost_by_month_sums_logs_in_period(session, location):
    asset = _make_asset(session, location)
    request = MaintenanceRequest(
        asset_id=asset.id,
        request_type=MaintenanceRequestType.CORRECTIVE,
        priority=MaintenancePriority.HIGH,
        status=MaintenanceStatus.IN_PROGRESS,
        opened_date=date(2026, 1, 1),
    )
    session.add(request)
    session.flush()

    session.add_all(
        [
            MaintenanceLog(request_id=request.id, log_date=date(2026, 1, 5), hours_spent=2, cost=100),
            MaintenanceLog(request_id=request.id, log_date=date(2026, 1, 20), hours_spent=1, cost=50),
            MaintenanceLog(request_id=request.id, log_date=date(2026, 2, 1), hours_spent=3, cost=300),
        ]
    )
    session.flush()

    repo = MaintenanceLogRepository(session)
    rows = repo.cost_by_month(date(2026, 1, 1), date(2026, 1, 31))

    assert rows == [("2026-01", 150.0)]
