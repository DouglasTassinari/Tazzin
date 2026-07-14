"""Cargos e Salários (RH) — a política salarial: leitura da base + simulador.

Primeira página do TAZZIN com working-set de sessão: tudo que aparece aqui vem de
``get_workset()``, uma cópia da base carregada em ``st.session_state`` na primeira
visita. A Fase 1 só lê; a Fase 2 escreve nessa cópia. O banco permanece intacto —
um F5 recarrega a base e descarta qualquer edição.
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
from app.core.comp_workset import get_workset
from app.core.formatting import format_brl
from app.domain import compensation_rules as rules

apply_branding("Cargos e Salários")
ensure_demo_data_once()

st.title("Cargos e Salários")
st.caption("Política salarial: cargos, níveis, tempo de casa e enquadramento do time.")

ws = get_workset()
bands = tuple(ws.bands) or rules.DEFAULT_BANDS


def salary_of(emp) -> Decimal:
    """Salário do enquadramento; cai para o salário atual quando o nível não tem base."""
    return emp.final if emp.final is not None else emp.current_salary


dashboard_tab, simulator_tab = st.tabs(["Dashboard", "Simulador"])

# --------------------------------------------------------------------------- #
# Dashboard — quadro atual, decomposto                                        #
# --------------------------------------------------------------------------- #
with dashboard_tab:
    if not ws.employees:
        st.info("Nenhum colaborador enquadrado ainda.")
    else:
        payroll = sum((salary_of(e) for e in ws.employees), Decimal("0"))
        headcount = len(ws.employees)
        average = payroll / headcount
        areas = sorted({p.area for p in ws.positions})

        k1, k2, k3, k4 = st.columns(4)
        k1.metric("Colaboradores enquadrados", headcount)
        k2.metric("Massa salarial", format_brl(payroll))
        k3.metric("Salário médio", format_brl(average))
        k4.metric("Cargos · áreas", f"{len(ws.positions)} · {len(areas)}")

        # ── Massa salarial por área ──
        st.subheader("Massa salarial por área")
        by_area: dict[str, Decimal] = {}
        for emp in ws.employees:
            by_area[emp.area] = by_area.get(emp.area, Decimal("0")) + salary_of(emp)
        ranked = sorted(by_area.items(), key=lambda item: item[1], reverse=True)
        names = [name for name, _ in ranked]
        values = [float(value) for _, value in ranked]
        charts.render(charts.hbar(names, values, money=True))
        st.caption("Custo mensal de folha em cada área — maior no topo é onde a política pesa mais.")

        # ── Quadro de ativos, com o salário aberto em parcelas ──
        st.subheader("Quadro de ativos — salário decomposto")
        area_filter = st.selectbox("Área", ["Todas", *sorted(by_area)], key="comp_area_filter")
        listed = [e for e in ws.employees if area_filter == "Todas" or e.area == area_filter]
        listed.sort(key=salary_of, reverse=True)

        df = pd.DataFrame(
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
                "Salário": [format_brl(salary_of(e)) for e in listed],
                "Bonif. liderança": [
                    format_brl(e.leadership_bonus) if e.is_leader else "—" for e in listed
                ],
            }
        )
        st.dataframe(df, width="stretch", hide_index=True)
        st.caption(
            "Salário = base do nível + adicional de avaliação + tempo de casa. "
            "A bonificação de liderança fica **fora** do salário — é informativa."
        )

        # ── Estrutura de cargos e níveis ──
        st.subheader("Estrutura de cargos e níveis")
        structure = pd.DataFrame(
            {
                "Cargo": [p.name for p in ws.positions],
                "Área": [p.area for p in ws.positions],
                "Níveis": [len(p.levels) if p.has_levels else 0 for p in ws.positions],
                "Faixa de base": [
                    (
                        f"{format_brl(min(bases))} — {format_brl(max(bases))}"
                        if (bases := [level.base_salary for level in p.levels
                                      if level.base_salary is not None])
                        else "—"
                    )
                    for p in ws.positions
                ],
                "Liderança": ["Sim" if p.has_leadership else "Não" for p in ws.positions],
            }
        )
        st.dataframe(structure, width="stretch", hide_index=True)
        st.caption("A progressão de nível é sempre manual — o sistema nunca promove sozinho.")

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

**Escrita efêmera** — as edições deste módulo (Fase 2) vivem só na sua sessão.
O banco é a base sintética, somente-leitura: um F5 recarrega tudo do zero.
            """
        )

# --------------------------------------------------------------------------- #
# Simulador — estima um cenário, não grava nada                               #
# --------------------------------------------------------------------------- #
with simulator_tab:
    st.subheader("Simulador de enquadramento")
    st.caption("Estima o salário de um cenário. Nada é gravado — nem na sessão, nem no banco.")

    if not ws.positions:
        st.info("Cadastre cargos e níveis para simular.")
        st.stop()

    col1, col2 = st.columns(2)
    position = col1.selectbox(
        "Cargo",
        ws.positions,
        format_func=lambda p: f"{p.name} · {p.area}",
        key="sim_position",
    )
    levels = sorted(position.levels, key=lambda level: level.display_order)
    level = col2.selectbox(
        "Nível",
        levels,
        format_func=lambda level: (
            f"{level.name} — {format_brl(level.base_salary)}"
            if level.base_salary is not None
            else f"{level.name} — base a definir"
        ),
        key="sim_level",
    ) if levels else None

    col3, col4, col5 = st.columns(3)
    hire = col3.date_input(
        "Admissão",
        value=date(ws.reference.year - 6, 1, 15),
        min_value=date(1980, 1, 1),
        max_value=ws.reference,
        format="DD/MM/YYYY",
        key="sim_hire",
    )
    evaluation = col4.number_input(
        "Adicional de avaliação (R$)",
        min_value=0.0,
        value=0.0,
        step=50.0,
        format="%.2f",
        key="sim_evaluation",
    )
    leadership = col5.checkbox(
        "Exerce liderança",
        value=position.has_leadership,
        help="Bonificação de 10% da base, paga fora do salário.",
        key="sim_leadership",
    )

    if level is None:
        st.warning(
            f"**{position.name}** não tem níveis cadastrados: a base entra como zero e o "
            "salário vira adicional de avaliação + tempo de casa."
        )
    elif level.base_salary is None:
        st.warning(
            f"O nível **{level.name}** está com a base a definir: a simulação usa zero como base."
        )

    base = level.base_salary if (level and level.base_salary is not None) else Decimal("0")

    sim = rules.simulate(
        base,
        hire,
        ws.reference,
        ws.floors,
        evaluation=Decimal(str(evaluation)),
        leadership=leadership,
        bands=bands,
    )

    st.markdown("#### Composição estimada")
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Base do nível", format_brl(sim.base))
    m2.metric("Adicional de avaliação", format_brl(sim.evaluation_addon))
    m3.metric("Tempo de casa", format_brl(sim.seniority_addon))
    m4.metric("Salário", format_brl(sim.salary))

    if leadership:
        st.info(
            f"**Bonificação de liderança:** {format_brl(sim.leadership_bonus)} — paga fora do "
            f"salário. Custo total do colaborador: **{format_brl(sim.total_with_bonus)}**."
        )

    st.markdown("#### Faixas de tempo de casa atingidas")
    if not sim.steps:
        next_band = bands[0][0] if bands else None
        st.info(
            "Nenhuma faixa atingida ainda"
            + (f" — a primeira é aos {next_band} anos de casa." if next_band else ".")
        )
    else:
        steps_df = pd.DataFrame(
            {
                "Faixa": [f"{step.years} anos" for step in sim.steps],
                "Percentual": [f"{step.percent:.0f}%" for step in sim.steps],
                "Aniversário": [step.anniversary.strftime("%d/%m/%Y") for step in sim.steps],
                "Piso vigente na data": [format_brl(step.floor) for step in sim.steps],
                "Valor travado": [format_brl(step.amount) for step in sim.steps],
            }
        )
        st.dataframe(steps_df, width="stretch", hide_index=True)
        st.caption(
            "Cada parcela trava no piso vigente na data do aniversário (respeitando o corte "
            "01/05) e não é mais reajustada. Por isso duas pessoas com o mesmo tempo de casa "
            "podem ter parcelas diferentes."
        )
