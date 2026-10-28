"""Bônus dos Distribuidores — rebate progressivo por faixa de compra anual.

Mostra quanto cada distribuidor já comprou no ano, em que faixa está, o bônus
apurado até agora e quanto falta para subir de faixa.
"""
# ruff: noqa: E402
from __future__ import annotations

import sys
from pathlib import Path as _Path

_PROJECT_ROOT = str(_Path(__file__).resolve().parents[2])
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from datetime import date

import pandas as pd
import streamlit as st

from app.core import charts, ui
from app.core.bootstrap import ensure_demo_data_once
from app.core.branding import apply_branding
from app.core.formatting import format_brl
from app.database.base import session_scope
from app.domain import bonus_rules as rules
from app.services.bonus_service import BonusService

apply_branding("Bônus Distribuidores")
ensure_demo_data_once()

ui.cabecalho(
    "Gestão", "Bônus dos Distribuidores",
    "Desconto progressivo sobre o total comprado no ano: quanto mais o distribuidor compra, "
    "maior a faixa. Apurado ao vivo a partir dos pedidos faturados.",
    direita_rotulo="Faixas de bônus", direita_valor=f"{rules.TIERS[1][1]:.0f}% a {rules.TIERS[-1][1]:.0f}%",
)

ano = st.selectbox("Ano de apuração", list(range(date.today().year, date.today().year - 3, -1)))
with session_scope() as session:
    service = BonusService(session)
    ranking = service.ranking(ano)
    resumo = service.summary(ano)
    por_faixa = service.by_tier(ano)
    mensal = service.monthly(ano)

if not ranking:
    st.info("Nenhum pedido de distribuidor faturado no ano selecionado.")
    st.stop()


def _mi(v: float) -> str:
    return f"R$ {v / 1_000_000:,.2f} mi".replace(",", "X").replace(".", ",").replace("X", ".")


st.markdown("#### Resultado da apuração")
ui.kpis([
    dict(rotulo="Distribuidores ativos", valor=str(resumo["distribuidores"]), tom="info",
         nota=f"{resumo['na_ultima_faixa']} na faixa máxima"),
    dict(rotulo="Compras no ano", valor=_mi(resumo["compras"]), tom="info", nota="Pedidos faturados, líquidos de desconto"),
    dict(rotulo="Bônus apurado", valor=format_brl(resumo["bonus"]), tom="ok",
         situacao="A devolver no fechamento",
         nota=f"{100 * resumo['bonus'] / resumo['compras']:.1f}% das compras".replace(".", ",")),
    dict(rotulo="Perto da próxima faixa", valor=str(resumo["perto_da_proxima"]),
         tom="atencao", situacao="Oportunidade de venda",
         nota="Já percorreram 75% do caminho para subir"),
])

col_a, col_b = st.columns(2)
with col_a:
    st.subheader("Em que faixa estão os distribuidores?")
    nomes = [("Abaixo da 1ª faixa" if i == 0 else f"Faixa {i} · {rules.TIERS[i][1]:.0f}%") for i, _ in por_faixa]
    charts.render(charts.hbar(nomes, [q for _, q in por_faixa],
                              colors=[charts.NEUTRO if i == 0 else charts.POSITIVO if i >= 3 else charts.PRIMARIA
                                      for i, _ in por_faixa]))
    st.caption("Quantidade de distribuidores por faixa de bônus. Quem está abaixo da primeira ainda não gera bônus.")
with col_b:
    st.subheader("Quanto os distribuidores compram por mês?")
    if mensal:
        meses, valores = zip(*mensal)
        charts.render(charts.area(list(meses), list(valores), money=True))
        st.caption("Compras mensais dos distribuidores — sustentam a subida de faixa até o fim do ano.")

st.subheader("Quem está perto de subir de faixa")
perto = sorted((x for x in ranking if x["faltam"] is not None and x["avanco"] >= 50),
               key=lambda x: x["faltam"])[:12]
if perto:
    ui.tabela(pd.DataFrame({
        "Distribuidor": [x["nome"] for x in perto],
        "UF": [x["uf"] for x in perto],
        "Faixa atual": [f"{x['pct']:.0f}%" for x in perto],
        "Compras no ano": [format_brl(x["compras"]) for x in perto],
        "Falta para a próxima": [format_brl(x["faltam"]) for x in perto],
        "Próxima faixa": [f"{x['prox_pct']:.0f}%" for x in perto],
        "Avanço (%)": [x["avanco"] for x in perto],
    }))
    st.caption("Uma proposta a mais pode levar o distribuidor à faixa seguinte: o bônus passa a valer sobre todo o total comprado.")

st.subheader("Apuração por distribuidor")
ui.tabela(pd.DataFrame({
    "Distribuidor": [x["nome"] for x in ranking[:25]],
    "UF": [x["uf"] for x in ranking[:25]],
    "Compras no ano": [x["compras"] for x in ranking[:25]],
    "Faixa": [f"{x['pct']:.0f}%" if x["pct"] else "—" for x in ranking[:25]],
    "Bônus apurado": [x["bonus"] for x in ranking[:25]],
}), column_config={
    "Compras no ano": st.column_config.NumberColumn(format="R$ %.2f"),
    "Bônus apurado": st.column_config.NumberColumn(format="R$ %.2f"),
})
st.caption(f"Mostrando os 25 maiores de {len(ranking)} distribuidores.")
