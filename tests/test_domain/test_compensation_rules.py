"""Regras de Cargos e Salários — os casos do guia (§10), com pisos próprios.

Os números-alvo do guia vieram da grade real da indústria; aqui a base é sintética,
então cada teste fixa seus próprios pisos e entradas e valida a **mecânica**, que é o
invariante: o tempo de casa acumula e trava, o piso vira em 01/05, a bonificação de
liderança fica fora do salário e o dissídio incide só sobre `salário − tempo de casa`.
"""
from datetime import date
from decimal import Decimal

from app.domain import compensation_rules as rules

# Pisos sintéticos. O salto de 2020 → 2023 é proposital: exercita o fallback do
# piso (aniversário anterior ao primeiro piso cadastrado).
FLOORS = {
    2020: Decimal("1200.00"),
    2023: Decimal("1500.00"),
    2024: Decimal("1600.00"),
    2025: Decimal("1700.00"),
    2026: Decimal("1800.00"),
}
REF = date(2026, 7, 14)


# --------------------------------------------------------------------------- #
# T1 — tempo de casa acumula e cada parcela trava no piso do aniversário       #
# --------------------------------------------------------------------------- #
def test_seniority_accumulates_and_locks_each_parcel_at_its_anniversary_floor():
    hire = date(2014, 6, 15)  # 12 anos de casa em 2026 → faixas de 2, 5 e 10 anos
    steps = rules.seniority_steps(hire, REF, FLOORS)

    assert [step.years for step in steps] == [2, 5, 10]
    # 2016 e 2019 são anteriores ao primeiro piso cadastrado → fallback no menor piso.
    assert steps[0].amount == Decimal("60.00")  # 5% de 1200
    assert steps[1].amount == Decimal("84.00")  # 7% de 1200
    assert steps[2].amount == Decimal("160.00")  # 10% de 1600 (aniversário em 2024)
    assert rules.seniority_addon(hire, REF, FLOORS) == Decimal("304.00")


def test_seniority_band_not_yet_reached_is_skipped():
    hire = date(2025, 6, 15)  # menos de 2 anos de casa
    assert rules.seniority_steps(hire, REF, FLOORS) == []
    assert rules.seniority_addon(hire, REF, FLOORS) == Decimal("0.00")


def test_each_parcel_is_rounded_to_cents_not_only_the_total():
    floors = {2024: Decimal("1234.57")}
    hire = date(2019, 6, 15)  # faixas de 2 (2021) e 5 (2024) anos
    steps = rules.seniority_steps(hire, date(2024, 12, 31), floors)

    # 5% de 1234,57 = 61,7285 → 61,73 ; 7% = 86,4199 → 86,42
    assert [step.amount for step in steps] == [Decimal("61.73"), Decimal("86.42")]
    assert rules.seniority_addon(hire, date(2024, 12, 31), floors) == Decimal("148.15")


def test_leap_day_anniversary_falls_back_to_28_february():
    steps = rules.seniority_steps(date(2016, 2, 29), REF, FLOORS)
    assert steps[0].anniversary == date(2018, 2, 28)


# --------------------------------------------------------------------------- #
# T2 — o piso do ano só vale a partir de 01/05 (data-base do dissídio)         #
# --------------------------------------------------------------------------- #
def test_floor_turns_only_on_may_1st():
    assert rules.effective_floor(FLOORS, date(2025, 4, 30)) == Decimal("1600.00")  # piso de 2024
    assert rules.effective_floor(FLOORS, date(2025, 5, 1)) == Decimal("1700.00")  # piso de 2025
    assert rules.effective_floor(FLOORS, date(2025, 12, 31)) == Decimal("1700.00")


def test_may_1st_cut_changes_the_parcel_locked_by_two_employees_hired_a_day_apart():
    # Mesma faixa (2 anos), aniversários em 30/04/2025 e 01/05/2025.
    before_cut = rules.seniority_steps(date(2023, 4, 30), REF, FLOORS)[0]
    after_cut = rules.seniority_steps(date(2023, 5, 1), REF, FLOORS)[0]

    assert before_cut.floor == Decimal("1600.00")  # ainda o piso de 2024
    assert after_cut.floor == Decimal("1700.00")  # já o piso de 2025
    assert before_cut.amount == Decimal("80.00")  # 5% de 1600
    assert after_cut.amount == Decimal("85.00")  # 5% de 1700


def test_floor_for_year_falls_back_to_the_lowest_registered_floor():
    assert rules.floor_for_year(FLOORS, 2015) == Decimal("1200.00")
    assert rules.floor_for_year(FLOORS, 2030) == Decimal("1800.00")


# --------------------------------------------------------------------------- #
# T3 — simulador                                                              #
# --------------------------------------------------------------------------- #
def test_simulate_composes_base_evaluation_and_seniority():
    sim = rules.simulate(
        Decimal("3000.00"), date(2014, 6, 15), REF, FLOORS, evaluation=Decimal("200.00")
    )

    assert sim.seniority_addon == Decimal("304.00")
    assert sim.salary == Decimal("3504.00")  # 3000 + 200 + 304
    assert [step.years for step in sim.steps] == [2, 5, 10]
    assert sim.leadership_bonus == Decimal("0.00")


def test_simulate_never_returns_less_than_the_current_salary():
    sim = rules.simulate(
        Decimal("3000.00"),
        date(2014, 6, 15),
        REF,
        FLOORS,
        current_salary=Decimal("5000.00"),
    )
    assert sim.salary == Decimal("5000.00")  # composição daria 3304, mas não pode cair


def test_evaluation_addon_is_the_residual_and_never_negative():
    assert rules.evaluation_addon(Decimal("4000"), Decimal("3000"), Decimal("304")) == Decimal("696.00")
    assert rules.evaluation_addon(Decimal("1000"), Decimal("3000"), Decimal("304")) == Decimal("0.00")


# --------------------------------------------------------------------------- #
# T4 — bonificação de liderança fica FORA do salário                          #
# --------------------------------------------------------------------------- #
def test_leadership_bonus_stays_out_of_the_salary():
    without = rules.simulate(Decimal("3000.00"), date(2014, 6, 15), REF, FLOORS)
    with_leadership = rules.simulate(
        Decimal("3000.00"), date(2014, 6, 15), REF, FLOORS, leadership=True
    )

    assert with_leadership.salary == without.salary  # o salário NÃO muda
    assert with_leadership.leadership_bonus == Decimal("300.00")  # 10% da base
    assert with_leadership.total_with_bonus == without.salary + Decimal("300.00")


# --------------------------------------------------------------------------- #
# T5 — reajuste coletivo: o % incide só sobre salário − tempo de casa          #
# --------------------------------------------------------------------------- #
def test_collective_adjustment_applies_percent_only_outside_the_seniority_parcel():
    hire = date(2014, 6, 15)  # tempo de casa = 304,00; nenhum aniversário após 01/05/2026
    result = rules.apply_collective_adjustment(
        [("ana", Decimal("4000.00"), hire)], FLOORS, Decimal("10"), 2026, REF
    )

    assert result.floor_before == Decimal("1800.00")
    assert result.floor_after == Decimal("1980.00")  # o piso do ano também é reajustado
    # (4000 − 304) × 1,10 + 304 = 4369,60 — e NÃO 4000 × 1,10 = 4400.
    assert result.lines[0].after == Decimal("4369.60")
    assert result.lines[0].after != Decimal("4400.00")
    assert result.total_before == Decimal("4000.00")
    assert result.total_after == Decimal("4369.60")


def test_collective_adjustment_recomposes_the_parcel_earned_after_may_1st():
    # Aniversário de 10 anos em 20/06/2026: caiu depois do corte, então essa parcela
    # acompanha o piso novo; as anteriores permanecem travadas.
    hire = date(2016, 6, 20)
    before = rules.seniority_addon(hire, REF, FLOORS)
    result = rules.apply_collective_adjustment(
        [("bruno", Decimal("4000.00"), hire)], FLOORS, Decimal("10"), 2026, REF
    )
    after = rules.seniority_addon(hire, REF, result.floors_after)

    assert before == Decimal("324.00")  # 60 + 84 + 180 (10% de 1800)
    assert after == Decimal("342.00")   # 60 + 84 + 198 (10% de 1980) — só a última mudou
    assert result.lines[0].after == Decimal("4385.60")  # (4000 − 324) × 1,10 + 342


# --------------------------------------------------------------------------- #
# T6 — defasagem retroativa do dissídio atrasado                              #
# --------------------------------------------------------------------------- #
def test_retroactive_gap_lists_bands_earned_after_may_1st_on_the_old_floor():
    gaps = rules.retroactive_gap(
        [("bruno", date(2016, 6, 20))], FLOORS, Decimal("10"), 2026, REF
    )

    assert len(gaps) == 1
    gap = gaps[0]
    assert gap.years == 10
    assert gap.anniversary == date(2026, 6, 20)
    assert gap.paid == Decimal("180.00")  # 10% do piso antigo (1800)
    assert gap.correct == Decimal("198.00")  # 10% do piso novo (1980)
    assert gap.difference == Decimal("18.00")


def test_retroactive_gap_ignores_anniversaries_outside_the_window():
    # Todos os aniversários de Ana são anteriores a 01/05/2026 → nada a corrigir.
    assert rules.retroactive_gap(
        [("ana", date(2014, 6, 15))], FLOORS, Decimal("10"), 2026, REF
    ) == []


# --------------------------------------------------------------------------- #
# T8 — colaborador sem nível: base zero, salário = adicional + tempo de casa   #
# --------------------------------------------------------------------------- #
def test_employee_without_level_has_no_base():
    sim = rules.simulate(
        Decimal("0"), date(2014, 6, 15), REF, FLOORS, evaluation=Decimal("2500.00"), leadership=True
    )

    assert sim.base == Decimal("0.00")
    assert sim.salary == Decimal("2804.00")  # 0 + 2500 + 304
    assert sim.leadership_bonus == Decimal("0.00")  # 10% de base zero
    assert rules.compose_salary(Decimal("0"), Decimal("2500"), Decimal("304")) == Decimal("2804.00")


# --------------------------------------------------------------------------- #
# §8 — guard de permissão                                                     #
# --------------------------------------------------------------------------- #
def test_can_manage_allows_developer_director_and_hr_area():
    assert rules.can_manage("desenvolvedor") is True
    assert rules.can_manage("diretor") is True
    assert rules.can_manage("gestor", ["rh", "producao"]) is True
    assert rules.can_manage("gestor", ["producao"]) is False
    assert rules.can_manage(None) is False
