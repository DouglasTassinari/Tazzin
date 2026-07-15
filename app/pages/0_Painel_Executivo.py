"""Painel Executivo — a visão consolidada que cruza os módulos.

Antes era a página inicial. Com a home virando vitrine, este painel passou a
ser um módulo como os outros: uma amostra de que, se a empresa quiser, os
módulos independentes também conversam entre si num quadro único.
"""
# ruff: noqa: E402  -- sys.path bootstrap below must run before the app.* imports
from __future__ import annotations

import sys
from pathlib import Path

_PROJECT_ROOT = str(Path(__file__).resolve().parents[2])
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from datetime import date, timedelta

import streamlit as st

from app.core import charts
from app.core.bootstrap import ensure_demo_data_once
from app.core.branding import apply_branding
from app.core.formatting import format_brl
from app.database.base import session_scope
from app.services.analytics_service import AnalyticsService

apply_branding("Painel Executivo")
ensure_demo_data_once()

st.title("Painel Executivo")
st.caption(
    "Uma visão que cruza os módulos. Opcional: cada ferramenta funciona sozinha — "
    "este quadro só mostra o que dá para enxergar quando elas conversam."
)

col1, col2 = st.columns(2)
default_start = date.today() - timedelta(days=365)
start = col1.date_input("De", value=default_start, key="dash_start")
end = col2.date_input("Até", value=date.today(), key="dash_end")

# Janela imediatamente anterior, do mesmo tamanho, para os comparativos.
window = (end - start) + timedelta(days=1)
prev_start, prev_end = start - window, start - timedelta(days=1)

with session_scope() as session:
    service = AnalyticsService(session)
    summary = service.executive_summary(start, end)
    previous = service.period_totals(prev_start, prev_end)
    revenue_rows = service.revenue_trend(start, end)
    spend_rows = service.spend_trend(start, end)
    cashflow_rows = service.cashflow_trend(start, end)


def _delta(current: float, reference: float) -> str | None:
    if not reference:
        return None
    return f"{(current - reference) / abs(reference) * 100:+.1f}%"


revenue = summary["total_revenue"]
spend = summary["total_spend"]
margin = (revenue - spend) / revenue * 100 if revenue else 0.0

row1 = st.columns(4)
row1[0].metric(
    "Receita", format_brl(revenue), delta=_delta(revenue, previous["revenue"]),
    help="Variação sobre o período anterior de mesma duração.",
)
row1[1].metric(
    "Gastos", format_brl(spend), delta=_delta(spend, previous["spend"]),
    delta_color="inverse", help="Variação sobre o período anterior de mesma duração.",
)
row1[2].metric(
    "Fluxo de caixa líquido", format_brl(summary["net_cashflow"]),
    delta=_delta(summary["net_cashflow"], previous["cashflow"]),
    help="Variação sobre o período anterior de mesma duração.",
)
row1[3].metric(
    "Margem operacional", f"{margin:.1f}%",
    help="(Receita - Gastos) / Receita no período selecionado.",
)

row2 = st.columns(4)
row2[0].metric("Projetos ativos", summary["active_projects"])
row2[1].metric("Rendimento médio de produção", f"{summary['avg_production_yield']:.1f}%")
row2[2].metric("Taxa média de defeitos", f"{summary['avg_defect_rate']:.1f}%")
row2[3].metric("Quadro de funcionários ativo", summary["active_headcount"])

row3 = st.columns(3)
row3[0].metric("Contas a receber pendentes", format_brl(summary["outstanding_receivables"]))
row3[1].metric("Contas a pagar pendentes", format_brl(summary["outstanding_payables"]))
row3[2].metric("Solicitações de manutenção abertas", summary["open_maintenance_requests"])

st.divider()

chart_col1, chart_col2 = st.columns(2)
with chart_col1:
    st.subheader("A operação é lucrativa?")
    if not revenue_rows and not spend_rows:
        st.info("Ainda não há dados de vendas e compras no período selecionado.")
    else:
        revenue_by_month = dict(revenue_rows)
        spend_by_month = dict(spend_rows)
        months = sorted(set(revenue_by_month) | set(spend_by_month))
        charts.render(
            charts.lines_compare(
                months,
                {
                    "Receita": ([revenue_by_month.get(m, 0) for m in months], charts.PRIMARIA),
                    "Gastos": ([spend_by_month.get(m, 0) for m in months], charts.NEUTRO),
                },
                money=True,
            )
        )
        st.caption("Quando a linha azul (Receita) corre acima da cinza (Gastos), o mês gerou lucro.")

with chart_col2:
    st.subheader("O caixa está saudável?")
    if not cashflow_rows:
        st.info("Ainda não há dados financeiros no período selecionado.")
    else:
        months, values = zip(*cashflow_rows)
        charts.render(charts.cashflow(months, values))
        st.caption(
            "Barras verdes = meses com caixa positivo; vermelhas = negativo. "
            "A linha pontilhada acumula o saldo do período."
        )
