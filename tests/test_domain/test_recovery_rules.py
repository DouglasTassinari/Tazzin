from app.domain import recovery_rules as r


def test_recency_band_boundaries():
    assert [r.recency_band(d) for d in (0, 90, 91, 180, 181, 365, 366)] == [
        "ativo", "ativo", "em_risco", "em_risco", "inativo", "inativo", "perdido"]


def test_reactivation_rate():
    assert r.reactivation_rate(15, 100) == 15.0
    assert r.reactivation_rate(0, 0) is None


def test_priority_follows_value_ranking():
    assert [r.priority(x) for x in (0.0, 0.25, 0.26, 0.6, 0.61, 1.0)] == [
        "alta", "alta", "media", "media", "baixa", "baixa"]
