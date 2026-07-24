"""Escrita efêmera: lançamentos que vivem só na sessão do navegador.

O banco desta amostra é **somente leitura**. Um lançamento feito na tela entra
na sessão, aparece na hora nas listas e nos totais, e some no F5. É de
propósito: a amostra mostra o *fluxo de operação* (quem lança, o que lança,
como aparece) sem sujar a base de demonstração que todo mundo compartilha.

Num cliente real este mesmo formulário grava no banco — o que muda é só a
camada de persistência, não a tela.
"""
from __future__ import annotations

from typing import Any

import streamlit as st

_PREFIXO = "lancamentos:"


def listar(chave: str) -> list[dict[str, Any]]:
    """Lançamentos feitos nesta sessão para a chave informada (mais novo por último)."""
    return st.session_state.get(_PREFIXO + chave, [])


def registrar(chave: str, item: dict[str, Any]) -> None:
    """Adiciona um lançamento à sessão."""
    st.session_state.setdefault(_PREFIXO + chave, []).append(item)


def limpar(chave: str) -> None:
    """Descarta os lançamentos da sessão para a chave informada."""
    st.session_state.pop(_PREFIXO + chave, None)


def aviso_efemero() -> None:
    """Deixa explícito que o lançamento não persiste."""
    st.caption(
        "Os lançamentos ficam **apenas nesta sessão** — atualizar a página (F5) limpa a lista. "
        "A base desta amostra é somente leitura; num cliente real isto grava no banco."
    )


def botao_limpar(chave: str) -> None:
    """Mostra quantos lançamentos há na sessão e oferece o descarte."""
    itens = listar(chave)
    if not itens:
        return
    col_info, col_botao = st.columns([4, 1])
    col_info.caption(f"{len(itens)} lançamento(s) nesta sessão.")
    if col_botao.button("Limpar", key=f"limpar-{chave}"):
        limpar(chave)
        st.rerun()
