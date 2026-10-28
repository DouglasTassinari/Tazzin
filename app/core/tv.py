"""Modo TV: telas para telão, com slides que giram sozinhos.

Cada slide é uma função que desenha cartões grandes. O fragmento reexecuta a
cada ``intervalo`` segundos e passa para o próximo slide, sem recarregar a
página inteira (nem o menu).
"""
from __future__ import annotations

import time
from collections.abc import Callable
from html import escape

import streamlit as st

from app.core.branding import AZUL, CINZA_CLARO, CINZA_MEDIO, GRAFITE, MARINHO, VERDE
from app.core.ui import AMBAR, BORDA, VERMELHO

_TOM = {"ok": VERDE, "atencao": AMBAR, "ruim": VERMELHO, "info": AZUL, "neutro": CINZA_MEDIO}

_CSS = f"""
<style>
  header[data-testid="stHeader"] {{ background: transparent; }}
  .tz-tv-titulo {{ font-size: 2.4rem; font-weight: 700; color: #fff; margin: 0 0 .2rem 0; }}
  .tz-tv-sub {{ font-size: 1.15rem; color: #9DB7D5; margin-bottom: 1.4rem; }}
  .tz-tv-card {{
    background: linear-gradient(135deg, #14304D 0%, {GRAFITE} 100%);
    border: 1px solid {BORDA}; border-radius: 18px; padding: 28px 30px; height: 100%;
  }}
  .tz-tv-rot {{ font-size: 1.05rem; font-weight: 700; letter-spacing: 1px; text-transform: uppercase;
                color: {CINZA_CLARO}; opacity: .85; }}
  .tz-tv-val {{ font-size: 3.6rem; font-weight: 700; line-height: 1.05; margin: 10px 0 6px 0; white-space: nowrap; }}
  .tz-tv-nota {{ font-size: 1.1rem; color: #9DB7D5; }}
  .tz-tv-pontos {{ display:flex; gap:10px; justify-content:center; margin-top: 1.6rem; }}
  .tz-tv-pontos span {{ width: 14px; height: 14px; border-radius: 50%; background: {BORDA}; }}
  .tz-tv-pontos span.ativo {{ background: {VERDE}; }}
  .tz-tv-fundo {{ background: {MARINHO}; }}
</style>
"""


def card(rotulo: str, valor: str, nota: str = "", tom: str = "info") -> str:
    cor = _TOM.get(tom, AZUL)
    return (f"<div class='tz-tv-card' style='border-left:8px solid {cor};'>"
            f"<div class='tz-tv-rot'>{escape(rotulo)}</div>"
            f"<div class='tz-tv-val' style='color:{cor};'>{escape(valor)}</div>"
            f"<div class='tz-tv-nota'>{escape(nota)}</div></div>")


def linha(cartoes: list[str]) -> None:
    for coluna, html in zip(st.columns(len(cartoes)), cartoes):
        coluna.markdown(html, unsafe_allow_html=True)


def titulo(texto: str, subtitulo: str = "") -> None:
    st.markdown(f"<div class='tz-tv-titulo'>{escape(texto)}</div>"
                f"<div class='tz-tv-sub'>{escape(subtitulo)}</div>", unsafe_allow_html=True)


def rotacionar(slides: list[Callable[[], None]], intervalo: int = 10, chave: str = "tv") -> None:
    """Mostra um slide por vez e troca sozinho a cada ``intervalo`` segundos."""
    st.markdown(_CSS, unsafe_allow_html=True)

    @st.fragment(run_every=intervalo)
    def _tela() -> None:
        indice = int(time.time() // intervalo) % len(slides)
        slides[indice]()
        pontos = "".join(f"<span class='{'ativo' if i == indice else ''}'></span>" for i in range(len(slides)))
        st.markdown(f"<div class='tz-tv-pontos'>{pontos}</div>", unsafe_allow_html=True)

    _tela()
