"""Recuperação de Clientes — quem parou de comprar, quem foi abordado e quem voltou.

A carteira é lida pela recência (há quantos dias o cliente não compra), a
abordagem pela taxa de reativação por canal e o resultado pela receita dos
pedidos feitos até 60 dias depois do contato.
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
from app.core.formatting import format_brl
from app.database.base import session_scope
from app.domain import recovery_rules as rules
from app.services.recovery_service import RecoveryService

apply_branding("Recuperação de Clientes")
ensure_demo_data_once()

SEGMENTOS = {"retail": "Varejo", "wholesale": "Atacado", "enterprise": "Corporativo"}
CANAIS = {"phone": "Telefone", "whatsapp": "WhatsApp", "email": "E-mail", "visit": "Visita"}
FAIXAS = {"em_risco": "Em risco", "inativo": "Inativo", "perdido": "Perdido"}
PRIORIDADE = {"alta": "Alta", "media": "Média", "baixa": "Baixa"}
FILTROS = {
    "Em risco e inativos": ("em_risco", "inativo"),
    "Só em risco (91–180 dias)": ("em_risco",),
    "Só inativos (181–365 dias)": ("inativo",),
    "Perdidos (+365 dias)": ("perdido",),
}
PERIODOS = {"Últimos 3 meses": 90, "Últimos 6 meses": 180, "Últimos 12 meses": 365}

ui.cabecalho(
    "Clientes", "Recuperação de Clientes",
    "Quem parou de comprar, quem já foi abordado e quanto voltou. Cliente só entra na fila "
    "depois de 90 dias sem compra.",
    direita_rotulo="Meta de reativação", direita_valor=f"{rules.REACTIVATION_TARGET:.0f}%",
)


def _mi(valor: float) -> str:
    """R$ em milhões, curto o bastante para caber no cartão."""
    return f"R$ {valor / 1_000_000:,.1f} mi".replace(",", "X").replace(".", ",").replace("X", ".")


hoje = date.today()
col_p, col_f = st.columns(2)
escolha = col_p.selectbox("Período dos contatos", list(PERIODOS), index=2)
filtro = col_f.selectbox("Fila de abordagem", list(FILTROS))
inicio = hoje - timedelta(days=PERIODOS[escolha] - 1)

with session_scope() as session:
    service = RecoveryService(session)
    faixas = service.bands(hoje)
    resumo = service.summary(inicio, hoje)
    canais = service.by_channel(inicio, hoje)
    mensal = service.monthly(inicio, hoje)
    mix = service.result_mix(inicio, hoje)
    fila = service.queue(hoje, FILTROS[filtro])
    ganhos = service.recent_wins(inicio, hoje)

atual, anterior = resumo["atual"], resumo["anterior"]
n, v = faixas["clientes"], faixas["valor_ref"]

variacao = ""
if atual["taxa"] is not None and anterior["taxa"] is not None:
    d = atual["taxa"] - anterior["taxa"]
    variacao = f" · {'▲' if d >= 0 else '▼'} {abs(d):.1f} pts vs. período anterior".replace(".", ",")
meta_ok = (atual["taxa"] or 0) >= rules.REACTIVATION_TARGET

st.markdown("#### Como está a carteira")
ui.kpis([
    dict(rotulo=f"Clientes em risco ({rules.AT_RISK_DAYS + 1}–{rules.DORMANT_DAYS} dias)",
         valor=str(n["em_risco"]), tom="atencao", situacao="Ainda dá tempo",
         nota=f"{_mi(v['em_risco'])} comprados no último ano de relacionamento"),
    dict(rotulo=f"Clientes inativos ({rules.DORMANT_DAYS + 1}–{rules.LOST_DAYS} dias)",
         valor=str(n["inativo"]), tom="ruim", situacao="Abordar agora",
         nota=f"{_mi(v['inativo'])} comprados no último ano de relacionamento"),
    dict(rotulo="Taxa de reativação",
         valor="—" if atual["taxa"] is None else f"{atual['taxa']:.1f}%".replace(".", ","),
         tom="ok" if meta_ok else "atencao",
         situacao="Dentro da meta" if meta_ok else "Abaixo da meta",
         nota=f"{atual['reativados']} de {atual['contatados']} contatados · meta ≥ "
              f"{rules.REACTIVATION_TARGET:.0f}%{variacao}"),
    dict(rotulo="Receita recuperada", valor=_mi(atual["recuperado"]), tom="ok",
         situacao=f"{atual['reativados']} clientes de volta",
         nota=f"Pedidos feitos até {rules.CONVERSION_WINDOW_DAYS} dias após o contato"),
])

# ── Carteira e canais ──
col_a, col_b = st.columns(2)
with col_a:
    st.subheader("Quanto da carteira está esfriando?")
    ordem = ["ativo", "em_risco", "inativo", "perdido"]
    nomes = {"ativo": "Ativos (até 90 dias)", "em_risco": "Em risco (91–180)",
             "inativo": "Inativos (181–365)", "perdido": "Perdidos (+365)"}
    cores = {"ativo": charts.POSITIVO, "em_risco": charts.ATENCAO,
             "inativo": charts.NEGATIVO, "perdido": charts.NEUTRO}
    charts.render(charts.hbar([nomes[f] for f in ordem], [n[f] for f in ordem],
                              colors=[cores[f] for f in ordem]))
    st.caption("Clientes por tempo desde a última compra. Quanto mais embaixo, mais difícil de trazer de volta.")
with col_b:
    st.subheader("Qual canal traz o cliente de volta?")
    com_taxa = sorted((c for c in canais if c["taxa"] is not None), key=lambda c: c["taxa"], reverse=True)
    if com_taxa:
        charts.render(charts.hbar(
            [CANAIS.get(c["canal"], c["canal"]) for c in com_taxa], [c["taxa"] for c in com_taxa],
            suffix="%",
            colors=[charts.POSITIVO if c["taxa"] >= rules.REACTIVATION_TARGET else charts.ATENCAO
                    for c in com_taxa]))
        st.caption("% dos contatados que voltaram a comprar. Verde = acima da meta.")
    else:
        st.info("Nenhum contato no período.")

# ── Resultado ──
col_c, col_d = st.columns([3, 2])
with col_c:
    st.subheader("Quanto já voltou?")
    if len(mensal) >= 2:
        meses, valores = zip(*mensal)
        charts.render(charts.area(list(meses), list(valores), money=True, color=charts.POSITIVO))
        st.caption("Receita dos pedidos de clientes recuperados, por mês do contato.")
    else:
        st.info("Poucos meses com recuperação para desenhar a evolução.")
with col_d:
    st.subheader("Como terminam os contatos?")
    rotulos = {"reactivated": "Voltou a comprar", "interested": "Interessado",
               "no_answer": "Sem resposta", "declined": "Recusou"}
    cor_res = {"reactivated": charts.POSITIVO, "interested": charts.PRIMARIA,
               "no_answer": charts.NEUTRO_CLARO, "declined": charts.NEGATIVO}
    chaves = [k for k in rotulos if mix.get(k)]
    if chaves:
        charts.render(charts.donut([rotulos[k] for k in chaves], [mix[k] for k in chaves],
                                   colors=[cor_res[k] for k in chaves]))

# ── Fila ──
st.subheader("Quem abordar primeiro")
if not fila:
    st.success("Nenhum cliente nessa faixa.")
else:
    st.caption(f"{len(fila)} clientes na faixa, do que mais comprava para o que menos comprava. Mostrando os 15 primeiros.")
    ui.tabela(pd.DataFrame({
        "Prioridade": [PRIORIDADE[c["prioridade"]] for c in fila[:15]],
        "Cliente": [c["nome"] for c in fila[:15]],
        "Segmento": [SEGMENTOS.get(c["segmento"], c["segmento"]) for c in fila[:15]],
        "Situação": [FAIXAS[c["faixa"]] for c in fila[:15]],
        "Dias sem comprar": [c["dias"] for c in fila[:15]],
        "Última compra": [c["ultima_compra"].strftime("%d/%m/%Y") for c in fila[:15]],
        "Comprava por ano": [format_brl(c["valor_ref"]) for c in fila[:15]],
        "Último contato": [c["ultimo_contato"].strftime("%d/%m/%Y") if c["ultimo_contato"] else "nunca"
                           for c in fila[:15]],
    }))

st.subheader("Últimos clientes recuperados")
if ganhos:
    ui.tabela(pd.DataFrame({
        "Data do contato": [g["data"].strftime("%d/%m/%Y") for g in ganhos],
        "Cliente": [g["cliente"] for g in ganhos],
        "Canal": [CANAIS.get(g["canal"], g["canal"]) for g in ganhos],
        "Pedido recuperado": [format_brl(g["recuperado"]) for g in ganhos],
        "Responsável": [g["responsavel"] for g in ganhos],
    }))
    st.caption("Clientes que voltaram a comprar até 60 dias depois do contato.")
else:
    st.info("Nenhum cliente recuperado no período.")
