"""Machining (Usinagem) dashboard page — shop floor overview."""
# ruff: noqa: E402
from __future__ import annotations

import sys
from pathlib import Path as _Path

_PROJECT_ROOT = str(_Path(__file__).resolve().parents[2])
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from datetime import date, timedelta

import streamlit as st

from app.core import charts
from app.core.bootstrap import ensure_demo_data_once
from app.core.branding import apply_branding
from app.database.base import session_scope
from app.domain.machining_rules import YIELD_TARGET_PCT
from app.services.machining_service import MachiningService

apply_branding("Chão de Fábrica")
ensure_demo_data_once()

CATEGORY_LABELS = {
    "productive": ("Produção", charts.POSITIVO),
    "semi_productive": ("Setup", charts.ATENCAO),
    "unproductive": ("Improdutivo", charts.NEGATIVO),
}

st.title("Chão de Fábrica")
st.caption("Chão de fábrica: rendimento dos operadores, utilização de máquinas e composição de tempo.")

col1, col2 = st.columns(2)
default_start = date.today() - timedelta(days=90)
start = col1.date_input("De", value=default_start)
end = col2.date_input("Até", value=date.today())

with session_scope() as session:
    svc = MachiningService(session)
    ranking = svc.operator_yield_ranking(start, end)
    time_cat = svc.time_by_category(start, end)
    time_occ = svc.time_by_occurrence(start, end)
    daily_prod = svc.production_by_day(start, end)
    machine_util = svc.machine_utilization(start, end)
    monthly_yield = svc.monthly_yield_trend(start, end)
    breakdown = svc.time_breakdown_summary(start, end)

# ── KPIs ──
total_pieces = sum(p for _, _, p in ranking)
avg_yield = sum(y for _, y, _ in ranking) / len(ranking) if ranking else 0
total_hours = sum(h for _, h in time_cat)

k1, k2, k3, k4 = st.columns(4)
k1.metric("Peças produzidas", f"{total_pieces:,.0f}".replace(",", "."))
k2.metric("Rendimento médio", f"{avg_yield:.1f}%")
k3.metric("Horas apontadas", f"{total_hours:,.0f}h")
k4.metric("Operadores ativos", str(len(ranking)))

# ── Time breakdown ──
st.subheader("Composição do tempo")
bd_col, comp_col = st.columns([3, 2])
with bd_col:
    if breakdown:
        labels = ["Produção", "Setup", "Sem peça", "Paradas", "Perdas operador"]
        values = [breakdown["production"], breakdown["setup"], breakdown["no_part"],
                  breakdown["stops"], breakdown["operator_loss"]]
        colors = [charts.POSITIVO, charts.ATENCAO, charts.NEUTRO, charts.NEGATIVO, charts.NEUTRO_CLARO]
        charts.render(charts.donut(labels, values, colors=colors))
        st.caption("Distribuição do tempo disponível entre as 5 categorias do chão de fábrica.")

with comp_col:
    st.markdown("**Horas por tipo de ocorrência**")
    if time_occ:
        for desc, hours in time_occ[:10]:
            st.text(f"{desc}: {hours:.1f}h")

# ── Yield ranking ──
st.subheader(f"Ranking de operadores — meta {YIELD_TARGET_PCT:.0f}%")
if not ranking:
    st.info("Nenhum apontamento produtivo no período selecionado.")
else:
    names = [n for n, _, _ in ranking]
    yields = [y for _, y, _ in ranking]
    colors = [charts.POSITIVO if y >= YIELD_TARGET_PCT else charts.NEGATIVO for y in yields]
    charts.render(charts.hbar(names, yields, colors=colors, suffix="%"))
    st.caption("Rendimento ponderado por operador — verde atinge a meta, vermelho exige atenção.")

# ── Machine utilization ──
st.subheader("Utilização de máquinas")
if not machine_util:
    st.info("Nenhum apontamento no período selecionado.")
else:
    m_names = [n for n, _, _ in machine_util]
    m_prod = [p for _, p, _ in machine_util]
    m_total = [t for _, _, t in machine_util]
    m_util_pct = [round(100 * p / t, 1) if t > 0 else 0 for p, t in zip(m_prod, m_total)]
    colors = [charts.POSITIVO if u >= 70 else charts.ATENCAO if u >= 50 else charts.NEGATIVO for u in m_util_pct]
    charts.render(charts.hbar(m_names, m_util_pct, colors=colors, suffix="%"))
    st.caption("% do tempo da máquina em produção efetiva — verde ≥70%, amarelo ≥50%.")

# ── Daily production ──
prod_col, yield_col = st.columns(2)
with prod_col:
    st.subheader("Produção por dia")
    if daily_prod:
        days, pieces = zip(*daily_prod)
        charts.render(charts.area(days, pieces))
    else:
        st.info("Sem dados de produção no período.")

with yield_col:
    st.subheader("Rendimento mensal da equipe")
    if monthly_yield:
        months, yields = zip(*monthly_yield)
        charts.render(charts.line_with_target(months, yields, YIELD_TARGET_PCT, f"Meta {YIELD_TARGET_PCT:.0f}%"))
    else:
        st.info("Sem dados de rendimento no período.")
