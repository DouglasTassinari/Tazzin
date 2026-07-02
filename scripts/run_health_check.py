"""CLI health probe — same checks the Administration page renders.

Usage: python scripts/run_health_check.py
Exits with status 1 if any check fails (suitable for cron/uptime probes).
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.health import run_health_checks


def main() -> int:
    report = run_health_checks()
    for check in report.checks:
        icon = "OK" if check.healthy else "FAIL"
        print(f"[{icon}] {check.name}: {check.detail} ({check.latency_ms}ms)")
    print("HEALTHY" if report.healthy else "UNHEALTHY")
    return 0 if report.healthy else 1


if __name__ == "__main__":
    sys.exit(main())
