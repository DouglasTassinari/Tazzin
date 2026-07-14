"""Time Adjustments (Ajustes) dashboard page — operation time improvements and worsenings."""
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
from app.services.adjustments_service import AdjustmentsService

apply_branding("Ajustes")
ensure_demo_data_once()

st.title("Ajustes de Tempo")
st.caption("Melhorias e pioras no tempo padrão de operação — impacto por operador, máquina e tendência.")

col1, col2 = st.columns(2)
default_start = date.today() - timedelta(days=90)
start = col1.date_input("De", value=default_start)
end = col2.date_input("Até", value=date.today())

with session_scope() as session:
    svc = AdjustmentsService(session)
    by_operator = svc.by_operator(start, end)
    by_machine = svc.by_machine(start, end)
    monthly = svc.monthly_trend(start, end)
    op_alerts = svc.operator_alerts(start, end)
    mc_alerts = svc.machine_alerts(start, end)

# ── KPIs ──
total_imp = sum(imp for _, imp, _, _ in by_operator)
total_wor = sum(wor for _, _, wor, _ in by_operator)
net_saved = sum(net for _, _, _, net in by_operator)

k1, k2, k3, k4 = st.columns(4)
k1.metric("Melhorias", str(total_imp))
k2.metric("Pioras", str(total_wor))
net_label = f"{net_saved:+,.0f}s".replace(",", ".")
k3.metric("Saldo líquido", net_label)
k4.metric("Operadores com registro", str(len(by_operator)))

# ── Alerts ──
if op_alerts or mc_alerts:
    st.warning("**Alertas de piora detectados:**")
    for op in op_alerts:
        st.markdown(f"- Operador **{op}** tem mais pioras que melhorias (mín. 3 ajustes)")
    for mc in mc_alerts:
        st.markdown(f"- Máquina **{mc}** tem mais pioras que melhorias (mín. 3 ajustes)")

# ── By operator ──
st.subheader("Ajustes por operador")
if by_operator:
    names = [n for n, _, _, _ in by_operator]
    net_vals = [round(n, 1) for _, _, _, n in by_operator]
    colors = [charts.POSITIVO if v > 0 else charts.NEGATIVO for v in net_vals]
    charts.render(charts.hbar(names, net_vals, colors=colors, suffix="s"))
    st.caption("Tempo líquido economizado (positivo = melhoria) por operador, em segundos por peça.")

    with st.expander("Detalhamento por operador"):
        for name, imp, wor, net in by_operator:
            sinal = "+" if net > 0 else ""
            st.text(f"{name}: {imp} melhorias · {wor} pioras · saldo {sinal}{net:.0f}s")
else:
    st.info("Nenhum ajuste registrado no período.")

# ── By machine ──
st.subheader("Ajustes por máquina")
if by_machine:
    names = [n for n, _, _, _ in by_machine]
    net_vals = [round(n, 1) for _, _, _, n in by_machine]
    colors = [charts.POSITIVO if v > 0 else charts.NEGATIVO for v in net_vals]
    charts.render(charts.hbar(names, net_vals, colors=colors, suffix="s"))
    st.caption("Saldo líquido por máquina — verde indica ganho de tempo, vermelho indica piora.")
else:
    st.info("Sem dados por máquina no período.")

# ── Monthly trend ──
st.subheader("Tendência mensal — melhorias vs pioras")
if monthly:
    months = [m for m, _, _ in monthly]
    improvements = [imp for _, imp, _ in monthly]
    worsenings = [wor for _, _, wor in monthly]
    charts.render(
        charts.lines_compare(
            months,
            {
                "Melhorias": (improvements, charts.POSITIVO),
                "Pioras": (worsenings, charts.NEGATIVO),
            },
        )
    )
    st.caption("Evolução mensal do volume de ajustes — cruzamento das linhas indica inversão de tendência.")
else:
    st.info("Sem dados mensais no período selecionado.")
