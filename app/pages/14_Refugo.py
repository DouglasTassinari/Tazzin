"""Scrap (Refugo) dashboard page — waste analysis and alerts."""
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
from app.services.scrap_service import ScrapService

apply_branding("Refugo")
ensure_demo_data_once()

ORIGIN_COLORS = {
    "fornecedor": charts.ATENCAO,
    "usinagem": charts.NEGATIVO,
    "indefinido": charts.NEUTRO,
}

st.title("Refugo")
st.caption("Análise de peças refugadas: por motivo, máquina, fornecedor e origem do defeito.")

col1, col2 = st.columns(2)
default_start = date.today() - timedelta(days=90)
start = col1.date_input("De", value=default_start)
end = col2.date_input("Até", value=date.today())

with session_scope() as session:
    svc = ScrapService(session)
    total = svc.total_in_period(start, end)
    by_reason = svc.by_reason(start, end)
    by_machine = svc.by_machine(start, end)
    by_operator = svc.by_operator(start, end)
    by_supplier = svc.by_supplier(start, end)
    by_origin = svc.by_origin(start, end)
    monthly = svc.monthly_trend(start, end)
    alerts = svc.concentration_alerts(start, end)

# ── KPIs ──
k1, k2, k3 = st.columns(3)
k1.metric("Total de peças refugadas", f"{total:,.0f}".replace(",", "."))
k2.metric("Motivos distintos", str(len(by_reason)))
k3.metric("Fornecedores envolvidos", str(len(by_supplier)))

# ── Alerts ──
any_alert = any(v for v in alerts.values())
if any_alert:
    st.warning("**Alertas de concentração detectados no período:**")
    for reason in alerts.get("reasons", []):
        st.markdown(f"- Motivo **{reason}** responde por ≥40% do refugo")
    for machine in alerts.get("machines", []):
        st.markdown(f"- Máquina **{machine}** responde por ≥40% do refugo")
    for supplier in alerts.get("suppliers", []):
        st.markdown(f"- Fornecedor **{supplier}** responde por ≥60% do refugo")

# ── Charts ──
reason_col, origin_col = st.columns(2)
with reason_col:
    st.subheader("Refugo por motivo")
    if by_reason:
        names, values = zip(*by_reason)
        charts.render(charts.hbar(list(names), list(values)))
    else:
        st.info("Nenhum registro de refugo no período.")

with origin_col:
    st.subheader("Origem do defeito")
    if by_origin:
        labels = [o for o, _ in by_origin]
        vals = [v for _, v in by_origin]
        colors = [ORIGIN_COLORS.get(l, charts.PRIMARIA) for l in labels]
        label_map = {"fornecedor": "Fornecedor", "usinagem": "Usinagem", "indefinido": "Indefinido"}
        charts.render(charts.donut([label_map.get(l, l) for l in labels], vals, colors=colors))
        st.caption("Classificação R34: defeitos de fornecedor (peça bruta) vs usinagem vs indefinido.")
    else:
        st.info("Sem dados para classificação de origem.")

machine_col, supplier_col = st.columns(2)
with machine_col:
    st.subheader("Refugo por máquina")
    if by_machine:
        names, values = zip(*by_machine)
        charts.render(charts.hbar(list(names), list(values)))
    else:
        st.info("Sem dados por máquina.")

with supplier_col:
    st.subheader("Refugo por fornecedor")
    if by_supplier:
        names, values = zip(*by_supplier[:10])
        charts.render(charts.hbar(list(names), list(values)))
    else:
        st.info("Sem dados por fornecedor.")

st.subheader("Refugo por operador")
if by_operator:
    names, values = zip(*by_operator)
    charts.render(charts.hbar(list(names), list(values)))

st.subheader("Tendência mensal")
if monthly:
    months, qtys = zip(*monthly)
    charts.render(charts.area(months, qtys))
    st.caption("Total de peças refugadas por mês — tendência de alta pode indicar problema sistêmico.")
else:
    st.info("Sem dados mensais no período selecionado.")
