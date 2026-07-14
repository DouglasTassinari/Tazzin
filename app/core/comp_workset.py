"""Session working-set for Compensation — the ephemeral write layer.

The Compensation module never persists user edits to the database. Instead, the
first access in a browser session loads a snapshot of the synthetic base into
``st.session_state`` (server-side, per-session memory). Every tab reads from — and,
in Phase 2, writes to — that working-set. A browser reload (F5) starts a fresh
session, ``st.session_state`` is empty, and the base is reloaded: no visitor's
simulation ever dirties the shared data.

This is the only place in the module that touches Streamlit; the domain and
repository layers stay pure and database-only.
"""
from __future__ import annotations

from typing import MutableMapping

import streamlit as st

from app.database.base import session_scope
from app.services.compensation_service import CompensationSnapshot, CompensationService

_STATE_KEY = "comp_workset"
# Todo widget da página usa este prefixo, para o "Restaurar base" conseguir
# limpá-los junto com o snapshot (ver reset_workset).
WIDGET_PREFIX = "comp_"


def get_workset() -> CompensationSnapshot:
    """Return this session's working-set, loading the base on first use."""
    if _STATE_KEY not in st.session_state:
        with session_scope() as session:
            st.session_state[_STATE_KEY] = CompensationService(session).load_snapshot()
    return st.session_state[_STATE_KEY]


def clear_state(state: MutableMapping) -> None:
    """Remove o snapshot e o estado dos widgets da página de um mapa de sessão.

    Separada de :func:`reset_workset` para poder ser testada com um dicionário
    comum, sem runtime do Streamlit. Além do snapshot, limpa os widgets: um
    ``selectbox`` que ficou apontando para um cargo excluído na sessão traria um
    valor que não existe mais na base recarregada. Zerar as duas coisas é o que
    faz o botão ser mesmo equivalente ao F5.
    """
    state.pop(_STATE_KEY, None)
    for key in [k for k in state if str(k).startswith(WIDGET_PREFIX)]:
        state.pop(key, None)


def reset_workset() -> None:
    """Discard the session's edits and reload the base (same effect as F5)."""
    clear_state(st.session_state)
