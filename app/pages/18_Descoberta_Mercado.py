"""Descoberta de Mercado — BI sobre a base pública de empresas.

Responde a pergunta que antecede a prospecção: *onde estão as empresas que
eu deveria estar atendendo?* Filtra a base por atividade (CNAE), praça e
porte, e mostra onde o mercado se concentra antes de qualquer contato.
"""
# ruff: noqa: E402
from __future__ import annotations

import sys
from pathlib import Path as _Path

_PROJECT_ROOT = str(_Path(__file__).resolve().parents[2])
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

import pandas as pd
import streamlit as st

from app.core import charts
from app.core.bootstrap import ensure_demo_data_once
from app.core.branding import apply_branding
from app.core.formatting import format_brl
from app.database.base import session_scope
from app.services.market_service import MarketService

apply_branding("Descoberta de Mercado")
ensure_demo_data_once()

PORTES = {"mei": "MEI", "me": "Microempresa", "epp": "Empresa de pequeno porte", "demais": "Demais"}
SITUACOES = {"ativa": "Ativa", "baixada": "Baixada", "suspensa": "Suspensa", "inapta": "Inapta"}

st.title("Descoberta de Mercado")
st.caption(
    "A base nacional de empresas recortada pelo que interessa à prospecção: "
    "atividade econômica, praça e porte. O mercado antes da primeira ligação."
)

with session_scope() as session:
    service = MarketService(session)
    opcoes = service.filter_options()

# ── Filtros ──
f1, f2, f3 = st.columns([2, 3, 2])
estados = f1.multiselect("Estado (UF)", opcoes["estados"])

rotulo_por_cnae = {rotulo: codigo for codigo, rotulo in opcoes["cnaes"]}
cnaes_escolhidos = f2.multiselect("Atividade (CNAE)", list(rotulo_por_cnae))
cnaes = [rotulo_por_cnae[r] for r in cnaes_escolhidos]

portes_escolhidos = f3.multiselect("Porte", list(PORTES.values()))
codigo_por_porte = {rotulo: codigo for codigo, rotulo in PORTES.items()}
portes = [codigo_por_porte[r] for r in portes_escolhidos]

somente_ativas = st.checkbox(
    "Considerar apenas empresas ativas", value=False,
    help="Desmarcado, a base inclui baixadas, suspensas e inaptas — útil para medir mortalidade.",
)

with session_scope() as session:
    service = MarketService(session)
    visao = service.overview(estados, cnaes, portes, somente_ativas)
    amostra = service.sample(estados, cnaes, portes, somente_ativas, limit=300)

resumo = visao["resumo"]

if resumo["total"] == 0:
    st.info("Nenhuma empresa encontrada com esses filtros. Tente ampliar o recorte.")
    st.stop()

# ── KPIs ──
pct_ativas = 100 * resumo["ativas"] / resumo["total"] if resumo["total"] else 0
k1, k2, k3 = st.columns(3)
k1.metric("Empresas no recorte", f"{resumo['total']:,.0f}".replace(",", "."))
k2.metric("Ativas", f"{resumo['ativas']:,.0f}".replace(",", "."), delta=f"{pct_ativas:.0f}% da base", delta_color="off")
k3.metric("Capital social médio", format_brl(resumo["capital_medio"]))

# ── Onde o mercado está ──
uf_col, porte_col = st.columns([3, 2])
with uf_col:
    st.subheader("Onde estão as empresas")
    if visao["por_estado"]:
        ufs, totais = zip(*visao["por_estado"])
        charts.render(charts.hbar(list(ufs), list(totais)))
        st.caption("Concentração por estado — a praça que responde pela maior parte do mercado.")
    else:
        st.info("Sem dados por estado.")

with porte_col:
    st.subheader("Perfil por porte")
    if visao["por_porte"]:
        rotulos = [PORTES.get(p, p) for p, _ in visao["por_porte"]]
        valores = [total for _, total in visao["por_porte"]]
        charts.render(charts.donut(rotulos, valores))
        st.caption("Porte define ticket e ciclo de venda — atacar MEI e Demais exige abordagens distintas.")
    else:
        st.info("Sem dados por porte.")

st.subheader("Atividades que mais aparecem")
if visao["por_cnae"]:
    nomes, totais = zip(*visao["por_cnae"])
    charts.render(charts.hbar(list(nomes), list(totais)))
    st.caption("Top CNAEs do recorte — é por aqui que se escolhe a lista de prospecção.")

st.subheader("Aberturas por ano")
if visao["aberturas"]:
    anos, quantidades = zip(*visao["aberturas"])
    charts.render(charts.area(list(anos), list(quantidades)))
    st.caption("Ritmo de novas empresas na praça — mercado que abre é mercado que compra.")

# ── A lista ──
st.subheader("Empresas do recorte")
st.caption(f"As {len(amostra)} maiores por capital social dentro do filtro atual.")
tabela = pd.DataFrame(
    {
        "CNPJ": [e["cnpj"] for e in amostra],
        "Razão social": [e["razao_social"] for e in amostra],
        "Atividade": [e["cnae"] for e in amostra],
        "Cidade": [e["cidade"] for e in amostra],
        "UF": [e["estado"] for e in amostra],
        "Porte": [PORTES.get(e["porte"], e["porte"]) for e in amostra],
        "Situação": [SITUACOES.get(e["situacao"], e["situacao"]) for e in amostra],
        "Abertura": [e["abertura"].strftime("%d/%m/%Y") for e in amostra],
        "Capital social": [format_brl(e["capital_social"]) for e in amostra],
    }
)
st.dataframe(tabela, hide_index=True)

st.caption(
    "Base sintética nesta amostra. Num cliente real este módulo lê a base pública "
    "da Receita Federal e cruza com a carteira para separar quem já é cliente de quem não é."
)
