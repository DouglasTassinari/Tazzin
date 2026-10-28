from app.domain import bonus_rules as r


def test_tier_and_pct_follow_thresholds():
    assert [r.bonus_pct(v) for v in (0, 149_999, 150_000, 300_000, 450_000, 600_000, 9e6)] == [0, 0, 3, 5, 8, 10, 10]


def test_bonus_applies_to_whole_total():
    assert r.bonus_value(300_000) == 15_000.0


def test_gap_and_progress():
    assert r.next_tier_gap(100_000) == (50_000.0, 3.0)
    assert r.next_tier_gap(700_000) is None
    assert r.progress_to_next(225_000) == 50.0
    assert r.progress_to_next(700_000) == 100.0
