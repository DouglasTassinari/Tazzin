from app.domain import postsales_rules as r


def test_classify_uses_market_ranges():
    assert [r.classify(s) for s in (0, 6, 7, 8, 9, 10)] == [
        "detrator", "detrator", "neutro", "neutro", "promotor", "promotor"]


def test_nps_is_promoters_minus_detractors():
    # 2 promotores, 1 neutro, 1 detrator em 4 respostas -> (2-1)/4 = +25
    assert r.nps([10, 9, 8, 3]) == 25.0
    assert r.nps([]) is None


def test_csat_counts_four_and_five():
    assert r.csat_pct([5, 4, 3, 1]) == 50.0
    assert r.csat_pct([]) is None


def test_response_rate_handles_zero_sent():
    assert r.response_rate(30, 100) == 30.0
    assert r.response_rate(0, 0) is None


def test_nps_zones():
    assert [r.nps_zone(v) for v in (80, 60, 10, -5, None)] == [
        "excelencia", "qualidade", "aperfeicoamento", "critica", "sem_dados"]


def test_followup_band():
    assert [r.followup_band(d) for d in (0, 2, 3, 7, 8)] == ["ok", "ok", "atencao", "atencao", "vencido"]
