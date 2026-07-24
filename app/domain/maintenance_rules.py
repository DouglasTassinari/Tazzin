"""Pure business rules for the Maintenance module — no database, no I/O."""
from __future__ import annotations

from datetime import date, timedelta

from app.core.exceptions import ValidationError
from app.database.models.maintenance import AssetCriticality, MaintenanceStatus

_ALLOWED_TRANSITIONS: dict[MaintenanceStatus, set[MaintenanceStatus]] = {
    MaintenanceStatus.OPEN: {MaintenanceStatus.SCHEDULED, MaintenanceStatus.CANCELLED},
    MaintenanceStatus.SCHEDULED: {MaintenanceStatus.IN_PROGRESS, MaintenanceStatus.CANCELLED},
    MaintenanceStatus.IN_PROGRESS: {MaintenanceStatus.COMPLETED, MaintenanceStatus.CANCELLED},
    MaintenanceStatus.COMPLETED: set(),
    MaintenanceStatus.CANCELLED: set(),
}


def validate_log(hours_spent: float, cost: float) -> None:
    if hours_spent <= 0:
        raise ValidationError("Hours spent must be positive")
    if cost < 0:
        raise ValidationError("Cost must be non-negative")


def can_transition(current: MaintenanceStatus, target: MaintenanceStatus) -> bool:
    return target in _ALLOWED_TRANSITIONS.get(current, set())


def assert_transition(current: MaintenanceStatus, target: MaintenanceStatus) -> None:
    if not can_transition(current, target):
        raise ValidationError(f"Cannot move request from {current.value} to {target.value}")


# --------------------------------------------------------------------------- #
# Calibração: de quanto em quanto tempo cada ativo precisa voltar à bancada.    #
# --------------------------------------------------------------------------- #
# Quanto mais crítico o ativo, mais curto o ciclo. Estes intervalos são a
# convenção desta amostra — num cliente real eles vêm do plano de calibração.
CALIBRATION_INTERVAL_MONTHS: dict[AssetCriticality, int] = {
    AssetCriticality.CRITICAL: 6,
    AssetCriticality.HIGH: 12,
    AssetCriticality.MEDIUM: 18,
    AssetCriticality.LOW: 24,
}

# Dias antes do vencimento em que o farol passa de verde para amarelo.
CALIBRATION_WARN_DAYS = 30


def _add_months(origem: date, meses: int) -> date:
    """Soma meses preservando o dia (encurtando quando o mês destino é menor)."""
    total = origem.month - 1 + meses
    ano = origem.year + total // 12
    mes = total % 12 + 1
    if mes == 12:
        ultimo_dia = 31
    else:
        ultimo_dia = (date(ano, mes + 1, 1) - timedelta(days=1)).day
    return date(ano, mes, min(origem.day, ultimo_dia))


def next_calibration_date(base: date, criticality: AssetCriticality) -> date:
    """Vencimento = último serviço (ou instalação) + intervalo da criticidade."""
    return _add_months(base, CALIBRATION_INTERVAL_MONTHS.get(criticality, 12))


def calibration_band(due: date, today: date) -> str:
    """Farol do vencimento: ``vencido`` · ``atencao`` · ``ok``."""
    dias = (due - today).days
    if dias < 0:
        return "vencido"
    if dias <= CALIBRATION_WARN_DAYS:
        return "atencao"
    return "ok"
