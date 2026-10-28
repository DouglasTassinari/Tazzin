"""Página inicial: a **vitrine** do TAZZIN (registrada em ``app/main.py``).

Não é o painel de um produto fechado — é a porta de entrada de uma amostra de
módulos independentes. Cada cartão abaixo é uma ferramenta que resolve um
problema real da operação, funciona sozinha e pode ser contratada e
personalizada de forma individual. A home conta essa história e leva a
pessoa para o módulo que interessa.

Os cartões vêm de ``app/core/navigation.py`` — a mesma ``ESTRUTURA`` que
monta o menu lateral, para vitrine e menu nunca divergirem.
"""
# ruff: noqa: E402  -- sys.path bootstrap below must run before the app.* imports
from __future__ import annotations

import os
import sys
from pathlib import Path

_PROJECT_ROOT = str(Path(__file__).resolve().parents[1])
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

import streamlit as st

from app.core.bootstrap import ensure_demo_data_once
from app.core.branding import (
    AZUL,
    CINZA_CLARO,
    CINZA_MEDIO,
    GRAFITE,
    LOGO_WORDMARK,
    MARINHO,
    VERDE,
    apply_branding,
)
from app.core.navigation import ESTRUTURA

apply_branding("Início")
ensure_demo_data_once()

# ── CSS só do que o tema global não cobre (hero, pílulas e tag "Em breve"). ──
st.markdown(
    f"""
    <style>
      .tz-hero {{
        background: linear-gradient(135deg, {MARINHO} 0%, {GRAFITE} 100%);
        border: 1px solid #1E3247; border-radius: 16px;
        padding: 32px 34px; margin: 4px 0 10px 0;
      }}
      .tz-hero h1 {{ color: {CINZA_CLARO}; font-size: 1.9rem; margin: 6px 0 2px 0; font-weight: 600; }}
      .tz-hero .tz-slogan {{ color: {VERDE}; font-weight: 600; letter-spacing: .3px; }}
      .tz-hero p {{ color: {CINZA_CLARO}; opacity: .92; font-size: 1.02rem; line-height: 1.55; margin: 12px 0 0 0; max-width: 760px; }}
      .tz-pills {{ display: flex; flex-wrap: wrap; gap: 10px; margin-top: 18px; }}
      .tz-pill {{ border: 1px solid {AZUL}; color: {CINZA_CLARO}; border-radius: 999px;
                  padding: 6px 14px; font-size: .86rem; background: rgba(74,144,217,.10); }}
      .tz-pill b {{ color: {AZUL}; }}
    </style>
    """,
    unsafe_allow_html=True,
)

st.image(LOGO_WORDMARK, width=230)

st.markdown(
    """
    <div class="tz-hero">
      <div class="tz-slogan">Menos planilhas. Mais controle.</div>
      <h1>Isto não é um produto fechado. É uma amostra de módulos.</h1>
      <p>
        Cada ferramenta abaixo resolve <b>um problema real</b> da operação e
        funciona <b>de forma independente</b>. Você pode adotar <b>uma só</b> —
        a que dói hoje — e ela já entrega valor sozinha. A partir daí, tudo é
        <b>personalizado</b> para a sua empresa: seus indicadores, suas regras,
        o seu jeito de trabalhar. Cresça no seu ritmo, um módulo de cada vez.
      </p>
      <div class="tz-pills">
        <span class="tz-pill"><b>Independente</b> · roda sozinho</span>
        <span class="tz-pill"><b>Personalizável</b> · feito sob medida</span>
        <span class="tz-pill"><b>Individual</b> · contrate só o que precisa</span>
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.caption("Os dados desta amostra são fictícios, gerados só para você navegar.")

# ── Um cartão grande por área, com os painéis que ela reúne. ─────────────────
_RESUMO_AREA = {
    "Comercial": "Encontre onde está a próxima venda, quem atender e que licitação vale a pena.",
    "Clientes": "Depois da venda: o que o cliente achou da entrega e quem precisa de retorno.",
    "Industrial": "A fábrica em tempo real: máquinas, operadores e produção.",
    "Pessoas": "Cargos, salários e o quadro de funcionários sem planilha paralela.",
    "Gestão": "A visão da diretoria: faturamento, caixa e o cruzamento de tudo.",
}

for inicio in range(0, len(ESTRUTURA), 2):
    colunas = st.columns(2)
    for coluna, (grupo, modulos) in zip(colunas, ESTRUTURA[inicio:inicio + 2]):
        with coluna, st.container(border=True):
            st.subheader(grupo)
            st.caption(_RESUMO_AREA.get(grupo, ""))
            for modulo in modulos:
                st.page_link(modulo.path, label=modulo.titulo, icon=modulo.icone)
                st.caption(modulo.resolve)

st.divider()
st.markdown(
    f"<p style='color:{CINZA_MEDIO};font-size:.92rem;'>"
    "Falta o módulo que resolveria o <i>seu</i> problema? "
    "É exatamente isso que eu construo: a ferramenta sob medida para a sua operação."
    "</p>",
    unsafe_allow_html=True,
)
_contato = os.getenv("TAZZIN_CONTATO_URL", "").strip()
if _contato:
    st.link_button("Falar sobre o meu caso", _contato, type="primary")
