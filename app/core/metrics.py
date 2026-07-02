"""Lightweight in-process metrics collector.

Not a replacement for Prometheus/Grafana in a real deployment — this is
the minimal counter/timer registry the Administration module reads to
render the "System Metrics" panel, and that :mod:`app.core.health` reports
alongside connectivity checks.
"""
from __future__ import annotations

import threading
import time
from collections import defaultdict
from dataclasses import dataclass


@dataclass
class _Stat:
    count: int = 0
    total_ms: float = 0.0
    errors: int = 0

    @property
    def avg_ms(self) -> float:
        return self.total_ms / self.count if self.count else 0.0


class MetricsRegistry:
    """Thread-safe counters and operation timings, keyed by name."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._stats: dict[str, _Stat] = defaultdict(_Stat)
        self._counters: dict[str, int] = defaultdict(int)
        self.started_at = time.time()

    def record_timing(self, name: str, elapsed_ms: float, failed: bool = False) -> None:
        with self._lock:
            stat = self._stats[name]
            stat.count += 1
            stat.total_ms += elapsed_ms
            if failed:
                stat.errors += 1

    def increment(self, name: str, amount: int = 1) -> None:
        with self._lock:
            self._counters[name] += amount

    def snapshot(self) -> dict:
        with self._lock:
            return {
                "uptime_seconds": round(time.time() - self.started_at, 1),
                "counters": dict(self._counters),
                "operations": {
                    name: {"count": s.count, "avg_ms": round(s.avg_ms, 2), "errors": s.errors}
                    for name, s in self._stats.items()
                },
            }


metrics = MetricsRegistry()


def track(name: str):
    """Decorator that records call count, average latency and error count."""

    def decorator(func):
        def wrapper(*args, **kwargs):
            start = time.perf_counter()
            failed = False
            try:
                return func(*args, **kwargs)
            except Exception:
                failed = True
                raise
            finally:
                elapsed_ms = (time.perf_counter() - start) * 1000
                metrics.record_timing(name, elapsed_ms, failed=failed)

        return wrapper

    return decorator
