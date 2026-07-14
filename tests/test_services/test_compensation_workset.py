"""Mutações do working-set de Cargos e Salários (Fase 2).

Sem banco e sem Streamlit: o snapshot é montado à mão e as funções são exercitadas
como funções puras. O que se valida aqui é a mecânica da escrita — a decomposição
sempre fecha, exclusão com ocupante é bloqueada, o dissídio incide só sobre
`salário − tempo de casa` e o adicional de avaliação continua sendo o resíduo.
"""
from datetime import date
from decimal import Decimal

import pytest

from app.core.exceptions import ValidationError
from app.services import compensation_workset as wset
from app.services.compensation_service import (
    CompensationSnapshot,
    EmployeeCompDTO,
    LevelDTO,
    PositionDTO,
)

FLOORS = {
    2020: Decimal("1200.00"),
    2023: Decimal("1500.00"),
    2024: Decimal("1600.00"),
    2025: Decimal("1700.00"),
    2026: Decimal("1800.00"),
}
REF = date(2026, 7, 14)


def _employee(employee_id: int, name: str, hire: date, position_id: int, level_id: int, evaluation):
    """Colaborador com os campos derivados zerados — ``recompute`` preenche."""
    return EmployeeCompDTO(
        employee_id=employee_id,
        name=name,
        area="",
        position_id=position_id,
        position="",
        level_id=level_id,
        level=None,
        hire_date=hire,
        current_salary=Decimal("0.00"),
        base=None,
        evaluation=Decimal(evaluation),
        seniority=Decimal("0.00"),
        final=None,
        is_leader=False,
        leadership_bonus=Decimal("0.00"),
    )


@pytest.fixture
def ws() -> CompensationSnapshot:
    torneiro = PositionDTO(
        id=1, name="Torneiro", area="Usinagem", code="TRN",
        has_leadership=False, has_levels=True,
        levels=[
            LevelDTO(id=1, position_id=1, name="Nível 1", description=None,
                     base_salary=Decimal("3000.00"), display_order=1),
            LevelDTO(id=2, position_id=1, name="Nível 2", description=None,
                     base_salary=Decimal("4000.00"), display_order=2),
        ],
    )
    supervisor = PositionDTO(
        id=2, name="Supervisor", area="Usinagem", code="SUP",
        has_leadership=True, has_levels=True,
        levels=[
            LevelDTO(id=3, position_id=2, name="Único", description=None,
                     base_salary=Decimal("6000.00"), display_order=1),
        ],
    )
    snapshot = CompensationSnapshot(
        reference=REF,
        floors=dict(FLOORS),
        bands=[(2, Decimal("5")), (5, Decimal("7")), (10, Decimal("10")),
               (15, Decimal("12")), (20, Decimal("15"))],
        positions=[torneiro, supervisor],
        employees=[
            # tempo de casa = 304,00 (faixas de 2, 5 e 10 anos)
            _employee(1, "Ana", date(2014, 6, 15), 1, 1, "0"),
            # tempo de casa = 324,00 — a faixa de 10 anos cai em 20/06/2026, após o corte
            _employee(2, "Bruno", date(2016, 6, 20), 1, 2, "100"),
        ],
    )
    wset.recompute(snapshot)
    snapshot.dirty = False  # recompute inicial não conta como edição
    return snapshot


# --------------------------------------------------------------------------- #
# Recomposição                                                                 #
# --------------------------------------------------------------------------- #
def test_recompute_decomposes_every_salary(ws):
    ana, bruno = ws.employees

    assert ana.base == Decimal("3000.00")
    assert ana.seniority == Decimal("304.00")
    assert ana.final == Decimal("3304.00")  # 3000 + 0 + 304
    assert bruno.seniority == Decimal("324.00")
    assert bruno.final == Decimal("4424.00")  # 4000 + 100 + 324
    assert ana.position == "Torneiro" and ana.area == "Usinagem" and ana.level == "Nível 1"
    assert ana.leadership_bonus == Decimal("0.00")


def test_the_base_snapshot_starts_clean(ws):
    assert ws.dirty is False
    assert ws.history == []


# --------------------------------------------------------------------------- #
# Cargos                                                                       #
# --------------------------------------------------------------------------- #
def test_save_position_creates_with_a_fresh_id_and_marks_the_workset_dirty(ws):
    created = wset.save_position(ws, name="Fresador", area="Usinagem", has_levels=True)

    assert created.id == 3  # não colide com os existentes
    assert created in ws.positions
    assert ws.dirty is True


def test_save_position_edits_in_place(ws):
    wset.save_position(ws, position_id=1, name="Torneiro CNC", area="Usinagem",
                       has_leadership=False, has_levels=True)

    assert wset.find_position(ws, 1).name == "Torneiro CNC"
    assert ws.employees[0].position == "Torneiro CNC"  # o quadro acompanha


def test_save_position_rejects_a_blank_name_or_a_duplicate(ws):
    with pytest.raises(ValidationError):
        wset.save_position(ws, name="   ", area="Usinagem")
    with pytest.raises(ValidationError):
        wset.save_position(ws, name="torneiro", area="usinagem")  # mesmo cargo, outra caixa


def test_delete_position_is_blocked_while_someone_is_placed_in_it(ws):
    with pytest.raises(ValidationError, match="Reenquadre"):
        wset.delete_position(ws, 1)
    assert wset.find_position(ws, 1) is not None


def test_delete_position_works_once_it_is_empty(ws):
    empty = wset.save_position(ws, name="Fresador", area="Usinagem")
    wset.delete_position(ws, empty.id)

    assert all(position.id != empty.id for position in ws.positions)


# --------------------------------------------------------------------------- #
# Níveis                                                                       #
# --------------------------------------------------------------------------- #
def test_changing_a_level_base_recomposes_whoever_is_in_it(ws):
    wset.save_level(ws, 1, level_id=1, name="Nível 1", base_salary=Decimal("3500.00"))

    ana = ws.employees[0]
    assert ana.base == Decimal("3500.00")
    assert ana.final == Decimal("3804.00")  # 3500 + 0 + 304


def test_save_level_creates_inside_the_position_and_rejects_duplicates(ws):
    created = wset.save_level(ws, 1, name="Nível 3", base_salary=Decimal("5000.00"), display_order=3)

    assert created.position_id == 1
    assert created in wset.find_position(ws, 1).levels
    with pytest.raises(ValidationError):
        wset.save_level(ws, 1, name="nível 3", base_salary=Decimal("5100.00"))


def test_level_without_a_base_leaves_the_employee_without_a_composed_salary(ws):
    wset.save_level(ws, 1, level_id=1, name="Nível 1", base_salary=None)

    ana = ws.employees[0]
    assert ana.base is None
    assert ana.final is None  # sem base não há composição — a UI cai no salário atual


def test_delete_level_is_blocked_while_someone_is_placed_in_it(ws):
    with pytest.raises(ValidationError, match="Reenquadre"):
        wset.delete_level(ws, 1)


# --------------------------------------------------------------------------- #
# Progressão                                                                   #
# --------------------------------------------------------------------------- #
def test_set_bands_recalculates_everyones_seniority(ws):
    wset.set_bands(ws, [(2, Decimal("10"))])  # uma única faixa, 10%

    ana = ws.employees[0]
    # Aniversário de 2 anos em 15/06/2016 → piso de fallback (1200) → 10% = 120,00
    assert ana.seniority == Decimal("120.00")
    assert ana.final == Decimal("3120.00")


def test_set_bands_rejects_duplicates_and_non_positive_values(ws):
    with pytest.raises(ValidationError):
        wset.set_bands(ws, [(2, Decimal("5")), (2, Decimal("7"))])
    with pytest.raises(ValidationError):
        wset.set_bands(ws, [(0, Decimal("5"))])
    with pytest.raises(ValidationError):
        wset.set_bands(ws, [])


# --------------------------------------------------------------------------- #
# Gestão do colaborador                                                        #
# --------------------------------------------------------------------------- #
def test_update_placement_moves_the_employee_and_recomposes(ws):
    updated = wset.update_placement(
        ws, 1, position_id=2, level_id=3, evaluation=Decimal("0"), is_leader=True
    )

    assert updated.position == "Supervisor"
    assert updated.base == Decimal("6000.00")
    assert updated.final == Decimal("6304.00")  # 6000 + 0 + 304
    # A bonificação de liderança fica FORA do salário.
    assert updated.leadership_bonus == Decimal("600.00")
    assert updated.final == Decimal("6304.00")


def test_update_placement_rejects_a_level_from_another_position(ws):
    with pytest.raises(ValidationError, match="não pertence"):
        wset.update_placement(ws, 1, position_id=2, level_id=1, evaluation=Decimal("0"), is_leader=False)


def test_update_placement_rejects_a_negative_evaluation_addon(ws):
    with pytest.raises(ValidationError):
        wset.update_placement(ws, 1, position_id=1, level_id=1, evaluation=Decimal("-1"), is_leader=False)


def test_placement_without_a_level_keeps_the_employee_without_a_base(ws):
    updated = wset.update_placement(
        ws, 1, position_id=1, level_id=None, evaluation=Decimal("500"), is_leader=False
    )

    assert updated.level is None
    assert updated.base is None
    assert updated.final is None


def test_inactivating_takes_the_employee_out_of_the_active_roster(ws):
    wset.set_employee_active(ws, 2, False)

    assert [emp.name for emp in wset.active_employees(ws)] == ["Ana"]


# --------------------------------------------------------------------------- #
# Reajuste coletivo                                                            #
# --------------------------------------------------------------------------- #
def test_apply_adjustment_raises_the_floor_the_level_bases_and_the_salaries(ws):
    result = wset.apply_adjustment(ws, Decimal("10"), 2026)
    ana, bruno = ws.employees

    # O piso do ano e as bases dos níveis acompanham o dissídio.
    assert ws.floors[2026] == Decimal("1980.00")
    assert wset.find_level(ws, 1).base_salary == Decimal("3300.00")
    assert wset.find_level(ws, 2).base_salary == Decimal("4400.00")

    # Ana: (3304 − 304) × 1,10 + 304 = 3604,00 — e não 3304 × 1,10 = 3634,40.
    assert ana.final == Decimal("3604.00")
    assert ana.evaluation == Decimal("0.00")  # o adicional segue sendo o resíduo

    # Bruno bateu a faixa de 10 anos depois de 01/05: essa parcela vai ao piso novo.
    assert bruno.seniority == Decimal("342.00")  # 60 + 84 + 198 (era 324)
    assert bruno.final == Decimal("4852.00")  # (4424 − 324) × 1,10 + 342
    assert bruno.evaluation == Decimal("110.00")  # o adicional foi reajustado junto com a base

    assert result.total_before == Decimal("7728.00")
    assert result.total_after == Decimal("8456.00")


def test_apply_adjustment_keeps_the_decomposition_closing(ws):
    wset.apply_adjustment(ws, Decimal("7.5"), 2026)

    for emp in ws.employees:
        assert emp.final == emp.base + emp.evaluation + emp.seniority


def test_apply_adjustment_records_the_session_history(ws):
    wset.apply_adjustment(ws, Decimal("10"), 2026)

    assert len(ws.history) == 1
    entry = ws.history[0]
    assert entry.year == 2026
    assert entry.percent == Decimal("10.00")
    assert entry.floor_before == Decimal("1800.00")
    assert entry.floor_after == Decimal("1980.00")
    assert entry.headcount == 2
    assert ws.dirty is True


def test_apply_adjustment_leaves_inactive_employees_out(ws):
    wset.set_employee_active(ws, 2, False)
    result = wset.apply_adjustment(ws, Decimal("10"), 2026)

    assert [line.key for line in result.lines] == [1]  # só Ana
    assert len(result.lines) == 1
    assert ws.history[0].headcount == 1


def test_adjustment_preview_does_not_touch_the_workset(ws):
    before = [emp.final for emp in ws.employees]
    preview = wset.adjustment_preview(ws, Decimal("10"), 2026)

    assert preview.total_after == Decimal("8456.00")
    assert [emp.final for emp in ws.employees] == before  # nada mudou
    assert ws.floors[2026] == Decimal("1800.00")
    assert ws.dirty is False


def test_adjustment_rejects_a_non_positive_percent(ws):
    with pytest.raises(ValidationError):
        wset.adjustment_preview(ws, Decimal("0"), 2026)


def test_gap_preview_lists_only_bands_earned_after_may_1st(ws):
    gaps = wset.gap_preview(ws, Decimal("10"), 2026)

    assert len(gaps) == 1
    assert gaps[0].key == 2  # Bruno
    assert gaps[0].years == 10
    assert gaps[0].paid == Decimal("180.00")
    assert gaps[0].correct == Decimal("198.00")
    assert gaps[0].difference == Decimal("18.00")
