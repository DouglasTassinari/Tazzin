"""Sistema TAZZIN entrypoint: registra as páginas e roteia a navegação.

Execute via ``streamlit run app/main.py``. A estrutura da navegação (quais
grupos existem e quais painéis moram em cada um) vive em
``app/core/navigation.py`` — a **fonte única** que esta barra lateral e a
vitrine da home (``app/Início.py``) compartilham, para nunca mais divergirem.

Passar um dicionário para ``st.navigation`` transforma cada chave num
cabeçalho colapsável na barra lateral (a "setinha" que abre e fecha) e cada
página vira um painel dentro do grupo.
"""
# ruff: noqa: E402  -- sys.path bootstrap below must run before the app.* imports
from __future__ import annotations

import sys
from pathlib import Path

# Streamlit only adds this script's own folder to sys.path, not the project
# root, so the "app.*" imports below would fail without this.
_PROJECT_ROOT = str(Path(__file__).resolve().parents[1])
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

import streamlit as st

from app.core.navigation import nav_modulos

st.navigation(nav_modulos()).run()
