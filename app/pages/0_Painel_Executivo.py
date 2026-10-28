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

from app.core import charts, ui
from app.core.bootstrap import ensure_demo_data_once
from app.core.branding import apply_branding
from app.core.formatting import format_brl
from app.database.base import session_scope
from app.services.analytics_service import AnalyticsService

apply_branding("Painel Estratégico")
ensure_demo_data_once()

ui.cabecalho('Gestão', "Painel Estratégico", "Uma visão que cruza os módulos. Opcional: cada ferramenta funciona sozinha — "
    "este quadro só mostra o que dá para enxergar quando elas conversam.")

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

def _var(atual: float, anterior: float, bom_se_subir: bool = True) -> tuple[str, str]:
    """Selo da variação sobre o período anterior: texto e tom (ok/ruim/neutro)."""
    texto = _delta(atual, anterior)
    if texto is None:
        return "", "neutro"
    subiu = atual >= anterior
    tom = "ok" if subiu == bom_se_subir else "ruim"
    return f"{'▲' if subiu else '▼'} {texto} vs. período anterior".replace(".", ","), tom


s_rec, t_rec = _var(revenue, previous["revenue"])
s_gas, t_gas = _var(spend, previous["spend"], bom_se_subir=False)
s_cx, t_cx = _var(summary["net_cashflow"], previous["cashflow"])

st.markdown("#### Resultado do período")
ui.kpis([
    dict(rotulo="Receita", valor=format_brl(revenue), tom="info",
         situacao=s_rec, situacao_tom=t_rec),
    dict(rotulo="Gastos", valor=format_brl(spend), tom="neutro",
         situacao=s_gas, situacao_tom=t_gas),
    dict(rotulo="Fluxo de caixa líquido", valor=format_brl(summary["net_cashflow"]),
         tom="ok" if summary["net_cashflow"] >= 0 else "ruim",
         situacao=s_cx, situacao_tom=t_cx),
    dict(rotulo="Margem operacional", valor=f"{margin:.1f}%".replace(".", ","),
         tom="ok" if margin >= 20 else "atencao", nota="(Receita − Gastos) ÷ Receita"),
])

st.markdown("#### Operação e pessoas")
ui.kpis([
    dict(rotulo="Projetos ativos", valor=str(summary["active_projects"]), tom="info"),
    dict(rotulo="Rendimento médio de produção",
         valor=f"{summary['avg_production_yield']:.1f}%".replace(".", ","),
         tom="ok" if summary["avg_production_yield"] >= 90 else "atencao"),
    dict(rotulo="Taxa média de defeitos",
         valor=f"{summary['avg_defect_rate']:.1f}%".replace(".", ","),
         tom="ok" if summary["avg_defect_rate"] <= 2 else "ruim"),
    dict(rotulo="Quadro de funcionários ativo", valor=str(summary["active_headcount"]), tom="info"),
])

st.markdown("#### Pendências")
ui.kpis([
    dict(rotulo="Contas a receber pendentes", valor=format_brl(summary["outstanding_receivables"]), tom="info"),
    dict(rotulo="Contas a pagar pendentes", valor=format_brl(summary["outstanding_payables"]), tom="atencao"),
    dict(rotulo="Manutenções abertas", valor=str(summary["open_maintenance_requests"]), tom="atencao",
         nota="Solicitações ainda não concluídas"),
], por_linha=3)

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
