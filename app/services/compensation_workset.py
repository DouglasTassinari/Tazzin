"""Mutações do working-set de Cargos e Salários — puras: sem banco, sem Streamlit.

A Fase 2 escreve, mas **nunca no banco**: toda edição acontece sobre o
:class:`~app.services.compensation_service.CompensationSnapshot` que vive na
sessão do visitante. Este módulo é quem sabe editá-lo.

Ele fica na camada de serviços, e não em ``app.core.comp_workset``, de propósito:
lá mora o Streamlit (``st.session_state``), e o que importa Streamlit não se
testa sem um runtime. Aqui as funções recebem o snapshot como argumento e
devolvem/alteram dados simples, então a lógica de escrita — a parte que pode
errar uma conta — fica coberta por testes de unidade comuns.

Toda mutação termina em :func:`recompute`, que refaz a decomposição
(``base + avaliação + tempo de casa``) de todo mundo a partir do estado atual, e
marca o snapshot como ``dirty`` — é o que a página usa para avisar que você está
numa cópia de trabalho e oferecer o "Restaurar base".
"""
from __future__ import annotations

from decimal import Decimal

from app.core.exceptions import ValidationError
from app.domain import compensation_rules as rules
from app.services.compensation_service import (
    AdjustmentEntry,
    CompensationSnapshot,
    EmployeeCompDTO,
    LevelDTO,
    PositionDTO,
)


# --------------------------------------------------------------------------- #
# Leitura                                                                      #
# --------------------------------------------------------------------------- #
def bands_of(ws: CompensationSnapshot) -> rules.Bands:
    return tuple(ws.bands) or rules.DEFAULT_BANDS


def salary_of(emp: EmployeeCompDTO) -> Decimal:
    """Salário do enquadramento; cai para o atual quando o nível não tem base."""
    return emp.final if emp.final is not None else emp.current_salary


def active_employees(ws: CompensationSnapshot) -> list[EmployeeCompDTO]:
    return [emp for emp in ws.employees if emp.active]


def all_levels(ws: CompensationSnapshot) -> list[LevelDTO]:
    return [level for position in ws.positions for level in position.levels]


def find_position(ws: CompensationSnapshot, position_id: int) -> PositionDTO:
    for position in ws.positions:
        if position.id == position_id:
            return position
    raise ValidationError("Cargo não encontrado no working-set.")


def find_level(ws: CompensationSnapshot, level_id: int) -> LevelDTO:
    for level in all_levels(ws):
        if level.id == level_id:
            return level
    raise ValidationError("Nível não encontrado no working-set.")


def find_employee(ws: CompensationSnapshot, employee_id: int) -> EmployeeCompDTO:
    for emp in ws.employees:
        if emp.employee_id == employee_id:
            return emp
    raise ValidationError("Colaborador não encontrado no working-set.")


def _next_id(ids) -> int:
    return max(ids, default=0) + 1


# --------------------------------------------------------------------------- #
# Recomposição — o passo final de toda mutação                                 #
# --------------------------------------------------------------------------- #
def recompute(ws: CompensationSnapshot) -> None:
    """Refaz a decomposição de todos os colaboradores a partir do estado atual.

    Chamada depois de qualquer edição (cargo, nível, faixa, enquadramento,
    dissídio): é o que garante que a base do nível, o tempo de casa e a
    bonificação de liderança sempre reflitam o que está no working-set agora.
    """
    positions = {position.id: position for position in ws.positions}
    levels = {level.id: level for level in all_levels(ws)}
    bands = bands_of(ws)

    for emp in ws.employees:
        position = positions.get(emp.position_id)
        level = levels.get(emp.level_id) if emp.level_id is not None else None
        # Nível órfão (o cargo do colaborador mudou, o nível ficou para trás).
        if level is not None and (position is None or level.position_id != position.id):
            level = None
            emp.level_id = None

        emp.position = position.name if position else "—"
        emp.area = position.area if position else "—"
        emp.level = level.name if level else None
        emp.base = level.base_salary if level else None
        emp.seniority = rules.seniority_addon(emp.hire_date, ws.reference, ws.floors, bands)
        emp.final = (
            rules.compose_salary(emp.base, emp.evaluation, emp.seniority)
            if emp.base is not None
            else None
        )
        emp.leadership_bonus = (
            rules.leadership_bonus(emp.base)
            if (emp.is_leader and emp.base is not None)
            else Decimal("0.00")
        )


def _touch(ws: CompensationSnapshot) -> None:
    ws.dirty = True
    recompute(ws)


# --------------------------------------------------------------------------- #
# Cargos                                                                       #
# --------------------------------------------------------------------------- #
def save_position(
    ws: CompensationSnapshot,
    *,
    position_id: int | None = None,
    name: str,
    area: str,
    code: str | None = None,
    has_leadership: bool = False,
    has_levels: bool = True,
) -> PositionDTO:
    """Cria (``position_id=None``) ou edita um cargo."""
    name = (name or "").strip()
    area = (area or "").strip()
    if not name:
        raise ValidationError("O cargo precisa de um nome.")
    if not area:
        raise ValidationError("O cargo precisa de uma área.")
    if any(
        p.id != position_id and p.name.casefold() == name.casefold()
        and p.area.casefold() == area.casefold()
        for p in ws.positions
    ):
        raise ValidationError(f"Já existe o cargo “{name}” na área {area}.")

    if position_id is None:
        position = PositionDTO(
            id=_next_id([p.id for p in ws.positions]),
            name=name,
            area=area,
            code=(code or "").strip() or None,
            has_leadership=has_leadership,
            has_levels=has_levels,
            levels=[],
        )
        ws.positions.append(position)
    else:
        position = find_position(ws, position_id)
        position.name = name
        position.area = area
        position.code = (code or "").strip() or None
        position.has_leadership = has_leadership
        position.has_levels = has_levels

    _touch(ws)
    return position


def delete_position(ws: CompensationSnapshot, position_id: int) -> None:
    """Exclui um cargo — bloqueado enquanto houver alguém enquadrado nele."""
    position = find_position(ws, position_id)
    occupants = [emp for emp in active_employees(ws) if emp.position_id == position_id]
    if occupants:
        raise ValidationError(
            f"{len(occupants)} colaborador(es) ainda estão em “{position.name}” "
            f"(ex.: {occupants[0].name}). Reenquadre antes de excluir."
        )
    ws.positions.remove(position)
    _touch(ws)


# --------------------------------------------------------------------------- #
# Níveis                                                                       #
# --------------------------------------------------------------------------- #
def save_level(
    ws: CompensationSnapshot,
    position_id: int,
    *,
    level_id: int | None = None,
    name: str,
    description: str | None = None,
    base_salary: Decimal | None = None,
    display_order: int = 1,
) -> LevelDTO:
    """Cria ou edita um nível dentro de um cargo. ``base_salary=None`` = a definir."""
    position = find_position(ws, position_id)
    name = (name or "").strip()
    if not name:
        raise ValidationError("O nível precisa de um nome.")
    if base_salary is not None:
        base_salary = rules.money(base_salary)
        if base_salary < 0:
            raise ValidationError("A base do nível não pode ser negativa.")
    if any(
        level.id != level_id and level.name.casefold() == name.casefold()
        for level in position.levels
    ):
        raise ValidationError(f"O cargo “{position.name}” já tem um nível “{name}”.")

    if level_id is None:
        level = LevelDTO(
            id=_next_id([level.id for level in all_levels(ws)]),
            position_id=position.id,
            name=name,
            description=(description or "").strip() or None,
            base_salary=base_salary,
            display_order=int(display_order),
        )
        position.levels.append(level)
    else:
        level = find_level(ws, level_id)
        if level.position_id != position.id:
            raise ValidationError("Esse nível pertence a outro cargo.")
        level.name = name
        level.description = (description or "").strip() or None
        level.base_salary = base_salary
        level.display_order = int(display_order)

    position.levels.sort(key=lambda level: (level.display_order, level.name))
    _touch(ws)
    return level


def delete_level(ws: CompensationSnapshot, level_id: int) -> None:
    """Exclui um nível — bloqueado enquanto houver alguém enquadrado nele."""
    level = find_level(ws, level_id)
    occupants = [emp for emp in active_employees(ws) if emp.level_id == level_id]
    if occupants:
        raise ValidationError(
            f"{len(occupants)} colaborador(es) estão no nível “{level.name}” "
            f"(ex.: {occupants[0].name}). Reenquadre antes de excluir."
        )
    find_position(ws, level.position_id).levels.remove(level)
    _touch(ws)


# --------------------------------------------------------------------------- #
# Progressão (faixas de tempo de casa)                                         #
# --------------------------------------------------------------------------- #
def set_bands(ws: CompensationSnapshot, bands) -> None:
    """Substitui as faixas de tempo de casa. Mexer aqui recalcula todo mundo."""
    cleaned: list[tuple[int, Decimal]] = []
    seen: set[int] = set()
    for years, percent in bands:
        years = int(years)
        percent = rules.money(percent)
        if years <= 0:
            raise ValidationError("O tempo de casa da faixa precisa ser maior que zero.")
        if percent <= 0:
            raise ValidationError("O percentual da faixa precisa ser maior que zero.")
        if years in seen:
            raise ValidationError(f"Há duas faixas para {years} anos de casa.")
        seen.add(years)
        cleaned.append((years, percent))

    if not cleaned:
        raise ValidationError("Cadastre ao menos uma faixa de tempo de casa.")

    cleaned.sort(key=lambda band: band[0])
    ws.bands = cleaned
    _touch(ws)


# --------------------------------------------------------------------------- #
# Gestão do colaborador                                                        #
# --------------------------------------------------------------------------- #
def update_placement(
    ws: CompensationSnapshot,
    employee_id: int,
    *,
    position_id: int,
    level_id: int | None,
    evaluation: Decimal,
    is_leader: bool,
) -> EmployeeCompDTO:
    """Reenquadra um colaborador: cargo, nível, adicional de avaliação e liderança."""
    emp = find_employee(ws, employee_id)
    position = find_position(ws, position_id)

    if level_id is not None:
        level = find_level(ws, level_id)
        if level.position_id != position.id:
            raise ValidationError(
                f"O nível “{level.name}” não pertence ao cargo “{position.name}”."
            )

    evaluation = rules.money(evaluation)
    if evaluation < 0:
        raise ValidationError("O adicional de avaliação não pode ser negativo.")

    emp.position_id = position.id
    emp.level_id = level_id
    emp.evaluation = evaluation
    emp.is_leader = is_leader
    _touch(ws)
    return emp


def set_employee_active(ws: CompensationSnapshot, employee_id: int, active: bool) -> EmployeeCompDTO:
    """Inativa/reativa um colaborador — só na sessão; a base nunca é tocada."""
    emp = find_employee(ws, employee_id)
    emp.active = bool(active)
    _touch(ws)
    return emp


# --------------------------------------------------------------------------- #
# Reajuste coletivo (dissídio)                                                 #
# --------------------------------------------------------------------------- #
def _validated_percent(percent) -> Decimal:
    percent = rules.money(percent)
    if percent <= 0:
        raise ValidationError("O percentual do reajuste precisa ser maior que zero.")
    return percent


def adjustment_preview(ws: CompensationSnapshot, percent, year: int) -> rules.AdjustmentResult:
    """Simula o dissídio sobre os ativos, sem alterar o working-set."""
    percent = _validated_percent(percent)
    employees = active_employees(ws)
    if not employees:
        raise ValidationError("Não há colaboradores ativos para reajustar.")
    return rules.apply_collective_adjustment(
        [(emp.employee_id, salary_of(emp), emp.hire_date) for emp in employees],
        ws.floors,
        percent,
        year,
        ws.reference,
        bands_of(ws),
    )


def gap_preview(ws: CompensationSnapshot, percent, year: int) -> list[rules.GapLine]:
    """Defasagem retroativa: faixas batidas após 01/05 ainda pagas no piso antigo."""
    percent = _validated_percent(percent)
    return rules.retroactive_gap(
        [(emp.employee_id, emp.hire_date) for emp in active_employees(ws)],
        ws.floors,
        percent,
        year,
        ws.reference,
        bands_of(ws),
    )


def apply_adjustment(ws: CompensationSnapshot, percent, year: int) -> rules.AdjustmentResult:
    """Aplica o dissídio ao working-set: piso do ano, bases dos níveis e salários.

    O percentual incide só sobre ``salário − tempo de casa``; o tempo de casa é
    recomposto pela regra. Depois do reajuste, o adicional de avaliação de cada
    um vira o resíduo (``novo salário − base − tempo de casa``), preservando a
    decomposição.
    """
    result = adjustment_preview(ws, percent, year)
    factor = Decimal(1) + result.percent / Decimal(100)

    ws.floors = dict(result.floors_after)
    for position in ws.positions:
        for level in position.levels:
            if level.base_salary is not None:
                level.base_salary = rules.money(level.base_salary * factor)

    new_salary = {line.key: line.after for line in result.lines}
    levels = {level.id: level for level in all_levels(ws)}
    bands = bands_of(ws)
    for emp in ws.employees:
        after = new_salary.get(emp.employee_id)
        if after is None:  # inativo não entra no dissídio
            continue
        level = levels.get(emp.level_id) if emp.level_id is not None else None
        base = level.base_salary if (level and level.base_salary is not None) else Decimal("0")
        seniority = rules.seniority_addon(emp.hire_date, ws.reference, ws.floors, bands)
        emp.current_salary = after
        emp.evaluation = rules.evaluation_addon(after, base, seniority)

    ws.history.append(
        AdjustmentEntry(
            year=result.year,
            percent=result.percent,
            floor_before=result.floor_before,
            floor_after=result.floor_after,
            total_before=result.total_before,
            total_after=result.total_after,
            headcount=len(result.lines),
        )
    )
    _touch(ws)
    return result
