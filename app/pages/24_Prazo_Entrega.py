"""Indicador do Prazo de Entrega — pedidos entregues dentro da data prometida (OTD).

OTD (on-time delivery) é o indicador padrão de logística: pedidos entregues até
a data prometida ÷ pedidos cujo prazo já venceu. A leitura vai da meta ao pedido
atrasado que precisa de ação hoje.
"""
# ruff: noqa: E402
from __future__ import annotations

import sys
from pathlib import Path as _Path

_PROJECT_ROOT = str(_Path(__file__).resolve().parents[2])
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from datetime import date, timedelta

import pandas as pd
import streamlit as st

from app.core import charts, ui
from app.core.bootstrap import ensure_demo_data_once
from app.core.branding import apply_branding
from app.database.base import session_scope
from app.domain import delivery_rules as rules
from app.services.delivery_service import DeliveryService

apply_branding("Prazo de Entrega")
ensure_demo_data_once()

SEGMENTOS = {"retail": "Varejo", "wholesale": "Atacado", "enterprise": "Corporativo"}
FAIXA = {"no_prazo": "No prazo", "leve": "Atraso leve", "medio": "Atraso médio", "grave": "Atraso grave"}
PERIODOS = {"Últimos 3 meses": 90, "Últimos 6 meses": 180, "Últimos 12 meses": 365}

ui.cabecalho(
    "Clientes", "Indicador do Prazo de Entrega",
    "Quantos pedidos chegaram na data prometida (OTD) e quais estão atrasados agora.",
    direita_rotulo="Meta de OTD", direita_valor=f"{rules.OTD_TARGET:.0f}%",
)

hoje = date.today()
escolha = st.selectbox("Período (pela data prometida)", list(PERIODOS), index=2)
inicio = hoje - timedelta(days=PERIODOS[escolha] - 1)

with session_scope() as session:
    service = DeliveryService(session)
    resumo = service.summary(inicio, hoje, hoje)
    mensal = service.monthly(inicio, hoje, hoje)
    segmentos = service.by_segment(inicio, hoje, hoje)
    mix = service.delay_mix(inicio, hoje, hoje)
    abertos = service.open_late(hoje)
    piores = service.worst_customers(inicio, hoje, hoje)

atual, anterior = resumo["atual"], resumo["anterior"]
if not atual["total"]:
    st.info("Nenhuma entrega com prazo vencido no período.")
    st.stop()

meta_ok = (atual["otd"] or 0) >= rules.OTD_TARGET
variacao = ""
if anterior["otd"] is not None:
    d = atual["otd"] - anterior["otd"]
    variacao = f" · {'▲' if d >= 0 else '▼'} {abs(d):.1f} pts vs. período anterior".replace(".", ",")

st.markdown("#### Como estamos")
ui.kpis([
    dict(rotulo="Entregas no prazo (OTD)", valor=f"{atual['otd']:.1f}%".replace(".", ","),
         tom="ok" if meta_ok else "atencao",
         situacao="Dentro da meta" if meta_ok else "Abaixo da meta",
         nota=f"Meta ≥ {rules.OTD_TARGET:.0f}%{variacao}"),
    dict(rotulo="Pedidos com prazo vencido", valor=str(atual["total"]), tom="info",
         nota=f"{atual['no_prazo']} no prazo · {atual['atrasados']} atrasados"),
    dict(rotulo="Atraso médio", valor=f"{atual['atraso_medio']:.1f} dias".replace(".", ","),
         tom="ok" if atual["atraso_medio"] <= 3 else "atencao", nota="Só entre os pedidos atrasados"),
    dict(rotulo="Atrasados em aberto", valor=str(len(abertos)),
         tom="ruim" if abertos else "ok", situacao="Cobrar a transportadora" if abertos else "Nenhum",
         nota="Prazo vencido e pedido ainda não entregue"),
])

col_a, col_b = st.columns([3, 2])
with col_a:
    st.subheader("O OTD está melhorando?")
    if len(mensal) >= 2:
        meses, valores = zip(*mensal)
        charts.render(charts.line_with_target(list(meses), list(valores), rules.OTD_TARGET,
                                              f"Meta {rules.OTD_TARGET:.0f}%"))
        st.caption("Linha acima da pontilhada = meta cumprida no mês.")
with col_b:
    st.subheader("Como são os atrasos?")
    chaves = [k for k in FAIXA if mix.get(k)]
    cor = {"no_prazo": charts.POSITIVO, "leve": charts.PRIMARIA, "medio": charts.ATENCAO, "grave": charts.NEGATIVO}
    charts.render(charts.donut([FAIXA[k] for k in chaves], [mix[k] for k in chaves],
                               colors=[cor[k] for k in chaves]))
    st.caption("Leve: até 3 dias · médio: 4 a 7 · grave: 8 ou mais.")

col_c, col_d = st.columns(2)
with col_c:
    st.subheader("Qual segmento recebe mais atraso?")
    seg = sorted((s for s in segmentos if s["otd"] is not None), key=lambda s: s["otd"], reverse=True)
    charts.render(charts.hbar([SEGMENTOS.get(s["segmento"], s["segmento"]) for s in seg], [s["otd"] for s in seg],
                              suffix="%",
                              colors=[charts.POSITIVO if s["otd"] >= rules.OTD_TARGET else charts.ATENCAO
                                      for s in seg]))
    st.caption("OTD por segmento. Verde = dentro da meta.")
with col_d:
    st.subheader("Quais clientes mais sofrem com atraso?")
    if piores:
        ui.tabela(pd.DataFrame({
            "Cliente": [p["cliente"] for p in piores],
            "Pedidos": [p["total"] for p in piores],
            "Atrasados": [p["atrasados"] for p in piores],
            "OTD (%)": [p["otd"] for p in piores],
        }))
        st.caption("Clientes com 4+ pedidos no período, do pior OTD para o melhor.")

st.subheader("Pedidos atrasados em aberto")
if abertos:
    ui.tabela(pd.DataFrame({
        "Situação": [FAIXA[a["faixa"]].replace("Atraso ", "").capitalize() for a in abertos],
        "Dias de atraso": [a["atraso"] for a in abertos],
        "Pedido": [a["pedido"] for a in abertos],
        "Cliente": [a["cliente"] for a in abertos],
        "Segmento": [SEGMENTOS.get(a["segmento"], a["segmento"]) for a in abertos],
        "Prometida para": [a["prometida"].strftime("%d/%m/%Y") for a in abertos],
    }))
    st.caption("Do mais atrasado para o menos. Cada linha é um cliente esperando.")
else:
    st.success("Nenhum pedido atrasado em aberto.")
