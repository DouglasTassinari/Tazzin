"""Health check used by the Administration page, the CLI script and (in a
real deployment) an uptime probe hitting a thin HTTP wrapper around this
module.
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field

from sqlalchemy import text

from app.core import metrics as metrics_module
from app.core.logging import get_logger

logger = get_logger("health")


@dataclass
class CheckResult:
    name: str
    healthy: bool
    detail: str
    latency_ms: float = 0.0


@dataclass
class HealthReport:
    healthy: bool
    checks: list[CheckResult] = field(default_factory=list)
    generated_at: float = field(default_factory=time.time)


def check_database() -> CheckResult:
    from app.database.base import engine

    start = time.perf_counter()
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        elapsed = (time.perf_counter() - start) * 1000
        return CheckResult("database", True, "connection OK", round(elapsed, 2))
    except Exception as exc:  # pragma: no cover - defensive path
        elapsed = (time.perf_counter() - start) * 1000
        logger.error("database health check failed: %s", exc)
        return CheckResult("database", False, str(exc), round(elapsed, 2))


def check_disk_writable() -> CheckResult:
    from app.core.config import settings

    start = time.perf_counter()
    probe = settings.log_dir / ".health_probe"
    try:
        settings.log_dir.mkdir(parents=True, exist_ok=True)
        probe.write_text("ok")
        probe.unlink()
        elapsed = (time.perf_counter() - start) * 1000
        return CheckResult("log_directory", True, "writable", round(elapsed, 2))
    except OSError as exc:  # pragma: no cover - defensive path
        elapsed = (time.perf_counter() - start) * 1000
        return CheckResult("log_directory", False, str(exc), round(elapsed, 2))


def run_health_checks() -> HealthReport:
    """Run every registered check and return an aggregate report."""
    checks = [check_database(), check_disk_writable()]
    report = HealthReport(healthy=all(c.healthy for c in checks), checks=checks)
    metrics_module.metrics.increment("health_check_runs")
    if not report.healthy:
        metrics_module.metrics.increment("health_check_failures")
    return report
