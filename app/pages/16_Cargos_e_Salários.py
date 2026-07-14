"""Cargos e Salários (RH) — a política salarial: leitura, simulação e edição.

Primeira página do TAZZIN que escreve. E escreve **fora do banco**: tudo o que
aparece aqui vem de ``get_workset()``, uma cópia da base carregada em
``st.session_state`` na primeira visita, e toda edição acontece nessa cópia (ver
:mod:`app.services.compensation_workset`). Um F5 — ou o botão "Restaurar base" —
descarta a sessão e recarrega a base intacta. Nenhum visitante suja os dados do
outro, e o banco continua somente-leitura na prática.
"""
# ruff: noqa: E402
from __future__ import annotations

import sys
from pathlib import Path as _Path

_PROJECT_ROOT = str(_Path(__file__).resolve().parents[2])
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from datetime import date
from decimal import Decimal

import pandas as pd
import streamlit as st

from app.core import charts
from app.core.bootstrap import ensure_demo_data_once
from app.core.branding import apply_branding
from app.core.comp_workset import get_workset, reset_workset
from app.core.exceptions import ValidationError
from app.core.formatting import format_brl
from app.domain import compensation_rules as rules
from app.services import compensation_workset as wset

apply_branding("Cargos e Salários")
ensure_demo_data_once()

st.title("Cargos e Salários")
st.caption("Política salarial: cargos, níveis, tempo de casa, enquadramento e dissídio.")

ws = get_workset()
bands = wset.bands_of(ws)
actives = wset.active_employees(ws)


def flash(message: str) -> None:
    """Guarda o aviso de sucesso para depois do ``st.rerun()`` que redesenha a página."""
    st.session_state["comp_flash"] = message


def prune(key: str, valid) -> None:
    """Esquece uma seleção que deixou de existir — um cargo excluído na sessão, por
    exemplo. Sem isso, o ``selectbox`` voltaria com um id que não está mais entre as
    opções."""
    if key in st.session_state and st.session_state[key] not in valid:
        del st.session_state[key]


if message := st.session_state.pop("comp_flash", None):
    st.success(message)

# Rótulos calculados uma vez por render. Dois cuidados aqui: passar um
# ``format_func`` que lê o working-set vivo faria o rótulo mudar debaixo do widget
# a cada edição; e nenhum rótulo carrega dinheiro, porque a base muda a cada
# dissídio — o valor aparece nas métricas e nas tabelas, onde ele pertence.
position_label = {p.id: f"{p.name} · {p.area}" for p in ws.positions}
level_label = {level.id: level.name for level in wset.all_levels(ws)}
employee_label = {
    emp.employee_id: emp.name + ("" if emp.active else " (inativo)") for emp in ws.employees
}

# ── Aviso de cópia de trabalho + restaurar ───────────────────────────────────
state_col, reset_col = st.columns([5, 1], vertical_alignment="center")
with state_col:
    if ws.dirty:
        st.warning(
            "Você está numa **cópia de trabalho desta sessão**. As edições valem só para "
            "você e somem no F5 — o banco não é alterado."
        )
    else:
        st.caption(
            "As abas de edição escrevem numa cópia da base que vive só nesta sessão. "
            "Pode mexer à vontade: nada é gravado no banco."
        )
with reset_col:
    if st.button("Restaurar base", width="stretch", disabled=not ws.dirty, key="comp_reset"):
        reset_workset()
        flash("Working-set restaurado: a página voltou a espelhar a base.")
        st.rerun()

(
    dashboard_tab,
    simulator_tab,
    positions_tab,
    levels_tab,
    progression_tab,
    employee_tab,
    adjustment_tab,
) = st.tabs(
    [
        "Dashboard",
        "Simulador",
        "Cargos",
        "Níveis",
        "Progressão",
        "Gestão do Colaborador",
        "Reajuste Coletivo",
    ]
)

# --------------------------------------------------------------------------- #
# Dashboard — o quadro atual, decomposto                                       #
# --------------------------------------------------------------------------- #
with dashboard_tab:
    if not actives:
        st.info("Nenhum colaborador ativo no working-set.")
    else:
        payroll = sum((wset.salary_of(emp) for emp in actives), Decimal("0"))
        areas = sorted({position.area for position in ws.positions})

        k1, k2, k3, k4 = st.columns(4)
        k1.metric("Colaboradores ativos", len(actives))
        k2.metric("Massa salarial", format_brl(payroll))
        k3.metric("Salário médio", format_brl(payroll / len(actives)))
        k4.metric("Cargos · áreas", f"{len(ws.positions)} · {len(areas)}")

        st.subheader("Massa salarial por área")
        by_area: dict[str, Decimal] = {}
        for emp in actives:
            by_area[emp.area] = by_area.get(emp.area, Decimal("0")) + wset.salary_of(emp)
        ranked = sorted(by_area.items(), key=lambda item: item[1], reverse=True)
        charts.render(
            charts.hbar([name for name, _ in ranked], [float(v) for _, v in ranked], money=True)
        )
        st.caption("Custo mensal de folha em cada área — maior no topo é onde a política pesa mais.")

        st.subheader("Quadro de ativos — salário decomposto")
        prune("comp_area_filter", {"Todas", *by_area})
        area_choice = st.selectbox("Área", ["Todas", *sorted(by_area)], key="comp_area_filter")
        listed = [e for e in actives if area_choice == "Todas" or e.area == area_choice]
        listed.sort(key=wset.salary_of, reverse=True)

        st.dataframe(
            pd.DataFrame(
                {
                    "Colaborador": [e.name for e in listed],
                    "Área": [e.area for e in listed],
                    "Cargo": [e.position for e in listed],
                    "Nível": [e.level or "—" for e in listed],
                    "Admissão": [e.hire_date.strftime("%d/%m/%Y") for e in listed],
                    "Base do nível": [
                        format_brl(e.base) if e.base is not None else "—" for e in listed
                    ],
                    "Adicional de avaliação": [format_brl(e.evaluation) for e in listed],
                    "Tempo de casa": [format_brl(e.seniority) for e in listed],
                    "Salário": [format_brl(wset.salary_of(e)) for e in listed],
                    "Bonif. liderança": [
                        format_brl(e.leadership_bonus) if e.is_leader else "—" for e in listed
                    ],
                }
            ),
            width="stretch",
            hide_index=True,
        )
        st.caption(
            "Salário = base do nível + adicional de avaliação + tempo de casa. "
            "A bonificação de liderança fica **fora** do salário — é informativa."
        )

    with st.expander("Sobre este módulo"):
        floors_text = " · ".join(
            f"{year}: {format_brl(value)}" for year, value in sorted(ws.floors.items())
        )
        bands_text = " · ".join(f"{years} anos: {percent:.0f}%" for years, percent in bands)
        st.markdown(
            f"""
**Como o salário é composto**

`salário = base do nível + adicional de avaliação + ajuste por tempo de casa`

- **Tempo de casa** — acumulativo e **fixo**: em cada aniversário de casa
  ({bands_text}) a parcela trava no piso vigente **naquela data** e nunca mais é
  reajustada.
- **Corte 01/05** — o piso de um ano só passa a valer na data-base do dissídio
  (1º de maio). Antes disso, vale o piso do ano anterior.
- **Bonificação de liderança** (10% da base) **não entra no salário**: é paga à
  parte e aparece aqui só como informação.
- **Reajuste coletivo (dissídio)** — o percentual incide apenas sobre
  `salário − tempo de casa`; o tempo de casa é recomposto pela regra, não
  reajustado junto.
- **Progressão de nível é manual** — promover é decisão de gestão, nunca automática.

**Pisos do sindicato:** {floors_text}

**Data de referência dos cálculos:** {ws.reference.strftime("%d/%m/%Y")}

**Escrita efêmera** — as edições deste módulo vivem só na sua sessão. O banco é a
base sintética, somente-leitura: um F5 (ou o botão "Restaurar base") recarrega tudo.
            """
        )

# --------------------------------------------------------------------------- #
# Simulador — estima um cenário, não grava nada                                #
# --------------------------------------------------------------------------- #
with simulator_tab:
    st.subheader("Simulador de enquadramento")
    st.caption("Estima o salário de um cenário. Não grava — nem na sessão, nem no banco.")

    if not ws.positions:
        st.info("Cadastre um cargo na aba **Cargos** para simular.")
    else:
        sim_col1, sim_col2 = st.columns(2)
        prune("comp_sim_position", position_label)
        sim_position = wset.find_position(
            ws,
            sim_col1.selectbox(
                "Cargo do cenário",
                [p.id for p in ws.positions],
                format_func=position_label.get,
                key="comp_sim_position",
            ),
        )
        sim_levels = sorted(sim_position.levels, key=lambda level: level.display_order)
        prune("comp_sim_level", {level.id for level in sim_levels})
        sim_level_id = (
            sim_col2.selectbox(
                "Nível do cenário",
                [level.id for level in sim_levels],
                format_func=level_label.get,
                key="comp_sim_level",
            )
            if sim_levels
            else None
        )
        sim_level = wset.find_level(ws, sim_level_id) if sim_level_id else None

        sim_col3, sim_col4, sim_col5 = st.columns(3)
        sim_hire = sim_col3.date_input(
            "Admissão do cenário",
            value=date(ws.reference.year - 6, 1, 15),
            min_value=date(1980, 1, 1),
            max_value=ws.reference,
            format="DD/MM/YYYY",
            key="comp_sim_hire",
        )
        sim_evaluation = sim_col4.number_input(
            "Adicional de avaliação do cenário (R$)",
            min_value=0.0,
            value=0.0,
            step=50.0,
            format="%.2f",
            key="comp_sim_evaluation",
        )
        sim_leadership = sim_col5.checkbox(
            "Exerce liderança no cenário",
            value=sim_position.has_leadership,
            help="Bonificação de 10% da base, paga fora do salário.",
            key="comp_sim_leadership",
        )

        if sim_level is None:
            st.warning(
                f"**{sim_position.name}** não tem níveis: a base entra como zero e o salário "
                "vira adicional de avaliação + tempo de casa."
            )
        elif sim_level.base_salary is None:
            st.warning(f"O nível **{sim_level.name}** está com a base a definir: a simulação usa zero.")

        sim = rules.simulate(
            sim_level.base_salary if (sim_level and sim_level.base_salary is not None) else Decimal("0"),
            sim_hire,
            ws.reference,
            ws.floors,
            evaluation=Decimal(str(sim_evaluation)),
            leadership=sim_leadership,
            bands=bands,
        )

        st.markdown("#### Composição estimada")
        s1, s2, s3, s4 = st.columns(4)
        s1.metric("Base do nível", format_brl(sim.base))
        s2.metric("Adicional de avaliação", format_brl(sim.evaluation_addon))
        s3.metric("Tempo de casa", format_brl(sim.seniority_addon))
        s4.metric("Salário", format_brl(sim.salary))

        if sim_leadership:
            st.info(
                f"**Bonificação de liderança:** {format_brl(sim.leadership_bonus)} — paga fora do "
                f"salário. Custo total: **{format_brl(sim.total_with_bonus)}**."
            )

        st.markdown("#### Faixas de tempo de casa atingidas")
        if not sim.steps:
            st.info(f"Nenhuma faixa atingida — a primeira é aos {bands[0][0]} anos de casa.")
        else:
            st.dataframe(
                pd.DataFrame(
                    {
                        "Faixa": [f"{step.years} anos" for step in sim.steps],
                        "Percentual": [f"{step.percent:.0f}%" for step in sim.steps],
                        "Aniversário": [step.anniversary.strftime("%d/%m/%Y") for step in sim.steps],
                        "Piso vigente na data": [format_brl(step.floor) for step in sim.steps],
                        "Valor travado": [format_brl(step.amount) for step in sim.steps],
                    }
                ),
                width="stretch",
                hide_index=True,
            )
            st.caption(
                "Cada parcela trava no piso vigente na data do aniversário (respeitando o corte "
                "01/05) e não é mais reajustada — por isso dois colegas com o mesmo tempo de casa "
                "podem ter parcelas diferentes."
            )

# --------------------------------------------------------------------------- #
# Cargos — CRUD na sessão                                                      #
# --------------------------------------------------------------------------- #
with positions_tab:
    st.subheader("Cargos")
    st.caption("Criar, editar e excluir cargos. Excluir é bloqueado se alguém ainda estiver nele.")

    prune("comp_position_pick", {None, *position_label})
    picked = st.selectbox(
        "Cargo a editar",
        [None, *[p.id for p in ws.positions]],
        format_func=lambda pid: "➕ Novo cargo" if pid is None else position_label[pid],
        key="comp_position_pick",
    )
    editing = wset.find_position(ws, picked) if picked else None

    with st.form("comp_position_form"):
        f1, f2, f3 = st.columns([2, 2, 1])
        p_name = f1.text_input("Nome do cargo", value=editing.name if editing else "")
        p_area = f2.text_input("Área do cargo", value=editing.area if editing else "")
        p_code = f3.text_input("Código", value=(editing.code or "") if editing else "")
        f4, f5 = st.columns(2)
        p_leadership = f4.checkbox(
            "Cargo de liderança", value=editing.has_leadership if editing else False
        )
        p_levels = f5.checkbox("Cargo com níveis", value=editing.has_levels if editing else True)
        submitted = st.form_submit_button(
            "Salvar cargo" if editing else "Criar cargo", type="primary"
        )

    if submitted:
        try:
            saved = wset.save_position(
                ws,
                position_id=picked,
                name=p_name,
                area=p_area,
                code=p_code,
                has_leadership=p_leadership,
                has_levels=p_levels,
            )
            flash(f"Cargo “{saved.name}” salvo na sessão.")
            st.rerun()
        except ValidationError as exc:
            st.error(str(exc))

    if editing and st.button("Excluir cargo", key="comp_position_delete"):
        try:
            wset.delete_position(ws, editing.id)
            flash(f"Cargo “{editing.name}” excluído da sessão.")
            st.rerun()
        except ValidationError as exc:
            st.error(str(exc))

    st.markdown("#### Cargos no working-set")
    headcount: dict[int, int] = {}
    for emp in actives:
        headcount[emp.position_id] = headcount.get(emp.position_id, 0) + 1
    st.dataframe(
        pd.DataFrame(
            {
                "Cargo": [p.name for p in ws.positions],
                "Área": [p.area for p in ws.positions],
                "Código": [p.code or "—" for p in ws.positions],
                "Níveis": [len(p.levels) if p.has_levels else 0 for p in ws.positions],
                "Liderança": ["Sim" if p.has_leadership else "Não" for p in ws.positions],
                "Ocupantes": [headcount.get(p.id, 0) for p in ws.positions],
            }
        ),
        width="stretch",
        hide_index=True,
    )

# --------------------------------------------------------------------------- #
# Níveis — CRUD dentro de um cargo                                             #
# --------------------------------------------------------------------------- #
with levels_tab:
    st.subheader("Níveis")
    st.caption("Os níveis carregam a **base** do salário. Mudar uma base recalcula quem está nela.")

    if not ws.positions:
        st.info("Cadastre um cargo antes de criar níveis.")
    else:
        prune("comp_level_position", position_label)
        level_position = wset.find_position(
            ws,
            st.selectbox(
                "Cargo dos níveis",
                [p.id for p in ws.positions],
                format_func=position_label.get,
                key="comp_level_position",
            ),
        )
        position_levels = sorted(level_position.levels, key=lambda level: level.display_order)

        prune("comp_level_pick", {None, *[level.id for level in position_levels]})
        picked_level = st.selectbox(
            "Nível a editar",
            [None, *[level.id for level in position_levels]],
            format_func=lambda lid: "➕ Novo nível" if lid is None else level_label[lid],
            key="comp_level_pick",
        )
        editing_level = wset.find_level(ws, picked_level) if picked_level else None

        with st.form("comp_level_form"):
            l1, l2, l3 = st.columns([2, 2, 1])
            l_name = l1.text_input(
                "Nome do nível", value=editing_level.name if editing_level else ""
            )
            l_base = l2.number_input(
                "Base do nível (R$)",
                min_value=0.0,
                value=(
                    float(editing_level.base_salary)
                    if (editing_level and editing_level.base_salary is not None)
                    else 0.0
                ),
                step=100.0,
                format="%.2f",
                help="Zero = base a definir (o nível não entra na composição).",
            )
            l_order = l3.number_input(
                "Ordem",
                min_value=1,
                value=editing_level.display_order if editing_level else len(position_levels) + 1,
                step=1,
            )
            l_description = st.text_input(
                "Descrição do nível",
                value=(editing_level.description or "") if editing_level else "",
            )
            level_submitted = st.form_submit_button(
                "Salvar nível" if editing_level else "Criar nível", type="primary"
            )

        if level_submitted:
            try:
                saved_level = wset.save_level(
                    ws,
                    level_position.id,
                    level_id=picked_level,
                    name=l_name,
                    description=l_description,
                    base_salary=Decimal(str(l_base)) if l_base > 0 else None,
                    display_order=int(l_order),
                )
                flash(f"Nível “{saved_level.name}” salvo em {level_position.name}.")
                st.rerun()
            except ValidationError as exc:
                st.error(str(exc))

        if editing_level and st.button("Excluir nível", key="comp_level_delete"):
            try:
                wset.delete_level(ws, editing_level.id)
                flash(f"Nível “{editing_level.name}” excluído da sessão.")
                st.rerun()
            except ValidationError as exc:
                st.error(str(exc))

        st.markdown(f"#### Níveis de {level_position.name}")
        if not position_levels:
            st.info("Esse cargo ainda não tem níveis.")
        else:
            occupants: dict[int, int] = {}
            for emp in actives:
                if emp.level_id is not None:
                    occupants[emp.level_id] = occupants.get(emp.level_id, 0) + 1
            st.dataframe(
                pd.DataFrame(
                    {
                        "Ordem": [level.display_order for level in position_levels],
                        "Nível": [level.name for level in position_levels],
                        "Base": [
                            format_brl(level.base_salary)
                            if level.base_salary is not None
                            else "a definir"
                            for level in position_levels
                        ],
                        "Descrição": [level.description or "—" for level in position_levels],
                        "Ocupantes": [occupants.get(level.id, 0) for level in position_levels],
                    }
                ),
                width="stretch",
                hide_index=True,
            )

# --------------------------------------------------------------------------- #
# Progressão — as faixas de tempo de casa                                      #
# --------------------------------------------------------------------------- #
with progression_tab:
    st.subheader("Progressão por tempo de casa")
    st.caption(
        "As faixas valem para todos os cargos. Alterar aqui recalcula o tempo de casa de "
        "todo mundo — cada parcela é recomposta no piso vigente na data do aniversário."
    )

    edited = st.data_editor(
        pd.DataFrame(
            {
                "Anos de casa": [int(years) for years, _ in bands],
                "Percentual (%)": [float(percent) for _, percent in bands],
            }
        ),
        num_rows="dynamic",
        width="stretch",
        hide_index=True,
        key="comp_bands_editor",
        column_config={
            "Anos de casa": st.column_config.NumberColumn(min_value=1, step=1, format="%d"),
            "Percentual (%)": st.column_config.NumberColumn(min_value=0.0, step=0.5, format="%.2f"),
        },
    )

    if st.button("Aplicar faixas", type="primary", key="comp_bands_apply"):
        try:
            rows = [
                (row["Anos de casa"], Decimal(str(row["Percentual (%)"])))
                for _, row in edited.iterrows()
                if pd.notna(row["Anos de casa"]) and pd.notna(row["Percentual (%)"])
            ]
            wset.set_bands(ws, rows)
            flash("Faixas de progressão aplicadas — o tempo de casa foi recalculado.")
            st.rerun()
        except ValidationError as exc:
            st.error(str(exc))

    st.markdown("#### Impacto atual das faixas")
    if actives:
        seniority_total = sum((emp.seniority for emp in actives), Decimal("0"))
        reached = sum(1 for emp in actives if emp.seniority > 0)
        i1, i2, i3 = st.columns(3)
        i1.metric("Custo mensal de tempo de casa", format_brl(seniority_total))
        i2.metric("Com alguma faixa atingida", f"{reached} de {len(actives)}")
        i3.metric(
            "% da massa salarial",
            f"{seniority_total / sum((wset.salary_of(e) for e in actives), Decimal('0')) * 100:.1f}%",
        )

# --------------------------------------------------------------------------- #
# Gestão do Colaborador — enquadramento                                        #
# --------------------------------------------------------------------------- #
with employee_tab:
    st.subheader("Gestão do colaborador")
    st.caption("Reenquadrar (cargo, nível, adicional, liderança) e inativar — sempre só na sessão.")

    if not ws.employees:
        st.info("Nenhum colaborador no working-set.")
    else:
        roster = sorted(ws.employees, key=lambda emp: emp.name)
        prune("comp_employee_pick", employee_label)
        chosen_id = st.selectbox(
            "Colaborador",
            [emp.employee_id for emp in roster],
            format_func=employee_label.get,
            key="comp_employee_pick",
        )
        emp = wset.find_employee(ws, chosen_id)

        if not emp.active:
            st.warning(f"**{emp.name}** está inativo nesta sessão — fora da folha e do dissídio.")

        e1, e2, e3, e4 = st.columns(4)
        e1.metric("Base do nível", format_brl(emp.base) if emp.base is not None else "—")
        e2.metric("Adicional de avaliação", format_brl(emp.evaluation))
        e3.metric("Tempo de casa", format_brl(emp.seniority))
        e4.metric("Salário", format_brl(wset.salary_of(emp)))
        st.caption(
            f"Admitido em {emp.hire_date.strftime('%d/%m/%Y')} · "
            f"{emp.position} · {emp.level or 'sem nível'}"
            + (f" · bonificação de liderança {format_brl(emp.leadership_bonus)}" if emp.is_leader else "")
        )

        with st.form("comp_employee_form"):
            g1, g2 = st.columns(2)
            g_position_id = g1.selectbox(
                "Enquadrar no cargo",
                [p.id for p in ws.positions],
                index=next(
                    (i for i, p in enumerate(ws.positions) if p.id == emp.position_id), 0
                ),
                format_func=position_label.get,
            )
            target_levels = sorted(
                wset.find_position(ws, g_position_id).levels,
                key=lambda level: level.display_order,
            )
            level_ids = [None, *[level.id for level in target_levels]]
            g_level_id = g2.selectbox(
                "Enquadrar no nível",
                level_ids,
                index=level_ids.index(emp.level_id) if emp.level_id in level_ids else 0,
                format_func=lambda lid: "Sem nível" if lid is None else level_label[lid],
            )
            g3, g4 = st.columns(2)
            g_evaluation = g3.number_input(
                "Adicional de avaliação (R$)",
                min_value=0.0,
                value=float(emp.evaluation),
                step=50.0,
                format="%.2f",
            )
            g_leader = g4.checkbox("Exerce liderança", value=emp.is_leader)
            placement_submitted = st.form_submit_button("Aplicar enquadramento", type="primary")

        if placement_submitted:
            try:
                updated = wset.update_placement(
                    ws,
                    emp.employee_id,
                    position_id=g_position_id,
                    level_id=g_level_id,
                    evaluation=Decimal(str(g_evaluation)),
                    is_leader=g_leader,
                )
                flash(
                    f"{updated.name} reenquadrado: {updated.position}"
                    f" · {updated.level or 'sem nível'} · {format_brl(wset.salary_of(updated))}."
                )
                st.rerun()
            except ValidationError as exc:
                st.error(str(exc))

        # O alvo é lido ANTES da mutação: depois de ``set_employee_active`` o
        # ``emp.active`` já é o novo valor, e a frase sairia invertida.
        activate = not emp.active
        if st.button(
            "Reativar colaborador" if activate else "Inativar colaborador",
            key="comp_employee_toggle",
        ):
            wset.set_employee_active(ws, emp.employee_id, activate)
            flash(f"{emp.name} {'reativado' if activate else 'inativado'} nesta sessão.")
            st.rerun()

        st.caption(
            "A progressão de nível é **manual**: o sistema nunca promove sozinho. "
            "Nada disso é gravado no banco."
        )

# --------------------------------------------------------------------------- #
# Reajuste Coletivo — o dissídio                                               #
# --------------------------------------------------------------------------- #
with adjustment_tab:
    st.subheader("Reajuste coletivo (dissídio)")
    st.caption(
        "O percentual incide só sobre `salário − tempo de casa`. O tempo de casa é recomposto "
        "pela regra: as parcelas antigas ficam travadas, e só a faixa batida após 01/05 acompanha "
        "o piso novo."
    )

    a1, a2 = st.columns(2)
    percent = a1.number_input(
        "Percentual do dissídio (%)",
        min_value=0.0,
        max_value=100.0,
        value=5.0,
        step=0.5,
        format="%.2f",
        key="comp_adjustment_percent",
    )
    year = a2.number_input(
        "Ano-base do reajuste",
        min_value=2000,
        max_value=2100,
        value=ws.reference.year,
        step=1,
        key="comp_adjustment_year",
    )

    if not actives:
        st.info("Nenhum colaborador ativo para reajustar.")
    else:
        try:
            preview = wset.adjustment_preview(ws, Decimal(str(percent)), int(year))
            gaps = wset.gap_preview(ws, Decimal(str(percent)), int(year))
        except ValidationError as exc:
            preview, gaps = None, []
            st.error(str(exc))

        if preview:
            delta = preview.total_after - preview.total_before
            p1, p2, p3, p4 = st.columns(4)
            p1.metric("Piso do ano", format_brl(preview.floor_after),
                      delta=format_brl(preview.floor_after - preview.floor_before))
            p2.metric("Massa após o reajuste", format_brl(preview.total_after), delta=format_brl(delta))
            p3.metric("Impacto mensal", format_brl(delta))
            p4.metric("Impacto anual (12x)", format_brl(delta * 12))

            names = {emp.employee_id: emp.name for emp in ws.employees}
            lines = sorted(
                preview.lines, key=lambda line: line.after - line.before, reverse=True
            )
            st.markdown("#### Prévia por colaborador")
            st.dataframe(
                pd.DataFrame(
                    {
                        "Colaborador": [names.get(line.key, "—") for line in lines],
                        "Salário atual": [format_brl(line.before) for line in lines],
                        "Após o reajuste": [format_brl(line.after) for line in lines],
                        "Diferença": [format_brl(line.after - line.before) for line in lines],
                        "Efetivo (%)": [
                            f"{(line.after - line.before) / line.before * 100:.2f}%"
                            if line.before
                            else "—"
                            for line in lines
                        ],
                    }
                ),
                width="stretch",
                hide_index=True,
            )
            st.caption(
                f"O efetivo fica abaixo de {percent:.2f}% porque o tempo de casa não é "
                "reajustado junto — é recomposto pela regra."
            )

            st.markdown("#### Defasagem retroativa")
            if not gaps:
                st.info(
                    f"Ninguém bateu faixa de tempo de casa entre 01/05/{int(year)} e "
                    f"{ws.reference.strftime('%d/%m/%Y')} — nada a corrigir."
                )
            else:
                total_gap = sum((gap.difference for gap in gaps), Decimal("0"))
                st.dataframe(
                    pd.DataFrame(
                        {
                            "Colaborador": [names.get(gap.key, "—") for gap in gaps],
                            "Faixa": [f"{gap.years} anos" for gap in gaps],
                            "Aniversário": [gap.anniversary.strftime("%d/%m/%Y") for gap in gaps],
                            "Pago (piso antigo)": [format_brl(gap.paid) for gap in gaps],
                            "Correto (piso novo)": [format_brl(gap.correct) for gap in gaps],
                            "Diferença": [format_brl(gap.difference) for gap in gaps],
                        }
                    ),
                    width="stretch",
                    hide_index=True,
                )
                st.caption(
                    f"{len(gaps)} parcela(s) batida(s) depois do corte 01/05 e ainda calculada(s) "
                    f"no piso antigo. Diferença mensal a pagar: **{format_brl(total_gap)}**."
                )

            if st.button("Aplicar reajuste ao working-set", type="primary", key="comp_adjustment_apply"):
                try:
                    applied = wset.apply_adjustment(ws, Decimal(str(percent)), int(year))
                    flash(
                        f"Dissídio de {applied.percent:.2f}% aplicado a {len(applied.lines)} "
                        f"colaboradores — massa de {format_brl(applied.total_before)} para "
                        f"{format_brl(applied.total_after)}. Só nesta sessão."
                    )
                    st.rerun()
                except ValidationError as exc:
                    st.error(str(exc))

    st.markdown("#### Histórico da sessão")
    if not ws.history:
        st.info("Nenhum reajuste aplicado nesta sessão.")
    else:
        st.dataframe(
            pd.DataFrame(
                {
                    "Ano-base": [entry.year for entry in ws.history],
                    "Percentual": [f"{entry.percent:.2f}%" for entry in ws.history],
                    "Piso antes": [format_brl(entry.floor_before) for entry in ws.history],
                    "Piso depois": [format_brl(entry.floor_after) for entry in ws.history],
                    "Massa antes": [format_brl(entry.total_before) for entry in ws.history],
                    "Massa depois": [format_brl(entry.total_after) for entry in ws.history],
                    "Colaboradores": [entry.headcount for entry in ws.history],
                }
            ),
            width="stretch",
            hide_index=True,
        )
        st.caption("Este histórico vive só na sessão — o F5 o apaga junto com o resto.")
