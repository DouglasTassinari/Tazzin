"""Modo TV Industrial — painel de telão que gira entre os indicadores do chão de fábrica."""
# ruff: noqa: E402
from __future__ import annotations

import sys
from pathlib import Path as _Path

_PROJECT_ROOT = str(_Path(__file__).resolve().parents[2])
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from datetime import date, timedelta

import streamlit as st

from app.core import charts, tv
from app.core.bootstrap import ensure_demo_data_once
from app.core.branding import apply_branding
from app.database.base import session_scope
from app.services.machining_service import MachiningService

apply_branding("Modo TV Industrial")
ensure_demo_data_once()

META_RENDIMENTO = 85.0
hoje = date.today()
inicio = hoje - timedelta(days=29)
with session_scope() as session:
    svc = MachiningService(session)
    ranking = svc.operator_yield_ranking(inicio, hoje)
    breakdown = svc.time_breakdown_summary(inicio, hoje)
    tendencia = svc.monthly_yield_trend(hoje - timedelta(days=364), hoje)
    maquinas = svc.machine_utilization(inicio, hoje)

pecas = sum(p for _, _, p in ranking)
medio = sum(y for _, y, _ in ranking) / len(ranking) if ranking else 0.0


def slide_producao() -> None:
    tv.titulo("Produção", "Últimos 30 dias · chão de fábrica")
    tv.linha([
        tv.card("Peças produzidas", f"{pecas:,.0f}".replace(",", "."), "Soma dos apontamentos", "info"),
        tv.card("Rendimento médio", f"{medio:.1f}%".replace(".", ","), f"Meta ≥ {META_RENDIMENTO:.0f}%",
                "ok" if medio >= META_RENDIMENTO else "atencao"),
        tv.card("Operadores ativos", str(len(ranking)), "Com apontamento no período", "info"),
    ])
    if tendencia:
        meses, valores = zip(*tendencia)
        charts.render(charts.line_with_target(list(meses), list(valores), META_RENDIMENTO, "Meta"))


def slide_tempo() -> None:
    tv.titulo("Onde vai o tempo da fábrica", "Últimos 30 dias · horas por categoria")
    if breakdown:
        rotulos = ["Produção", "Setup", "Sem peça", "Paradas", "Perdas operador"]
        valores = [breakdown["production"], breakdown["setup"], breakdown["no_part"],
                   breakdown["stops"], breakdown["operator_loss"]]
        total = sum(valores) or 1
        tv.linha([
            tv.card("Produção", f"{100 * valores[0] / total:.0f}%", "Do tempo disponível", "ok"),
            tv.card("Setup", f"{100 * valores[1] / total:.0f}%", "Preparação de máquina", "atencao"),
            tv.card("Paradas e perdas", f"{100 * (valores[3] + valores[4]) / total:.0f}%",
                    "Parada de máquina e perdas", "ruim"),
        ])
        charts.render(charts.donut(rotulos, valores, colors=[charts.POSITIVO, charts.ATENCAO, charts.NEUTRO,
                                                             charts.NEGATIVO, charts.NEUTRO_CLARO]))


def slide_ranking() -> None:
    tv.titulo("Rendimento por operador", f"Últimos 30 dias · meta {META_RENDIMENTO:.0f}%")
    top = sorted(ranking, key=lambda r: r[1], reverse=True)[:8]
    if top:
        charts.render(charts.hbar([n for n, _, _ in top], [y for _, y, _ in top], suffix="%",
                                  colors=[charts.POSITIVO if y >= META_RENDIMENTO else charts.NEGATIVO
                                          for _, y, _ in top]))


tv.rotacionar([slide_producao, slide_tempo, slide_ranking], intervalo=10)
st.caption(f"Troca de tela automática a cada 10 segundos. {len(maquinas)} máquinas monitoradas. Dados fictícios.")
