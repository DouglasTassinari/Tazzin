from datetime import date

from app.domain import delivery_rules as r

HOJE = date(2026, 10, 28)


def test_delay_days_and_open_orders():
    assert r.delay_days(date(2026, 10, 10), date(2026, 10, 8), HOJE) == 0
    assert r.delay_days(date(2026, 10, 10), date(2026, 10, 13), HOJE) == 3
    assert r.delay_days(date(2026, 10, 20), None, HOJE) == 8    # não entregue: conta até hoje


def test_is_due_only_when_delivered_or_overdue():
    assert r.is_due(date(2026, 11, 5), None, HOJE) is False
    assert r.is_due(date(2026, 10, 1), None, HOJE) is True
    assert r.is_due(date(2026, 11, 5), date(2026, 10, 27), HOJE) is True


def test_bands_and_rate():
    assert [r.delay_band(d) for d in (0, 1, 3, 4, 7, 8)] == ["no_prazo", "leve", "leve", "medio", "medio", "grave"]
    assert r.otd_rate(95, 100) == 95.0 and r.otd_rate(0, 0) is None
