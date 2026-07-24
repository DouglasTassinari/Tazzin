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
      .tz-soon-tag {{ display: inline-block; background: rgba(76,175,80,.12);
                      border: 1px solid {VERDE}; color: {VERDE}; border-radius: 999px;
                      padding: 3px 12px; font-size: .78rem; font-weight: 600; }}
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

st.caption(
    "Os dados desta amostra são fictícios, gerados só para você navegar. Alguns "
    "painéis já estão prontos; outros aparecem como **Em breve** — juntos, formam "
    "o mapa completo do sistema. Explore pelo cartão ou pela barra lateral."
)
st.divider()

# ── Catálogo de módulos: um cartão por painel, no mesmo agrupamento do menu. ──
for grupo, modulos in ESTRUTURA:
    st.subheader(grupo)
    # Três cartões por linha; completa a última linha com espaços vazios.
    for inicio in range(0, len(modulos), 3):
        linha = modulos[inicio:inicio + 3]
        colunas = st.columns(3)
        for coluna, modulo in zip(colunas, linha):
            with coluna, st.container(border=True):
                marca = " 🔒" if modulo.locked else ""
                st.markdown(f"**{modulo.titulo}**{marca}")
                st.caption(modulo.resolve)
                if modulo.em_breve:
                    st.markdown('<span class="tz-soon-tag">Em breve</span>', unsafe_allow_html=True)
                else:
                    st.page_link(modulo.path, label="Abrir painel", icon=modulo.icone)
    st.write("")

st.divider()
st.markdown(
    f"<p style='color:{CINZA_MEDIO};font-size:.92rem;'>"
    "Falta o módulo que resolveria o <i>seu</i> problema? Ele ainda não existe aqui — "
    "mas é exatamente isso que eu construo: a ferramenta sob medida para a sua operação."
    "</p>",
    unsafe_allow_html=True,
)
