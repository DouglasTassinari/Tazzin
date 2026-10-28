"""Estrutura de navegação do Sistema TAZZIN — **fonte única** da amostra.

Tanto o menu lateral (``app/main.py``) quanto a vitrine da home
(``app/Início.py``) leem esta mesma ``ESTRUTURA``. Antes, cada um mantinha
sua própria cópia da lista de módulos e os dois viviam divergindo; agora há
um lugar só para descrever "quais grupos existem, quais painéis moram em
cada um e o que cada painel resolve".

Cada :class:`Modulo` aponta para um arquivo real em ``app/pages/`` **ou**, se
``path`` for ``None``, é um **esqueleto**: um painel previsto na amostra que
ainda não foi construído. O esqueleto vira uma página "Em breve" navegável,
gerada por uma função (``st.Page`` aceita um *callable*), sem precisar de um
arquivo físico por módulo.
"""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

import streamlit as st

from app.core.branding import (
    AZUL,
    CINZA_CLARO,
    GRAFITE,
    MARINHO,
    VERDE,
    apply_branding,
)


@dataclass(frozen=True)
class Modulo:
    """Um painel da amostra. ``path=None`` significa esqueleto "Em breve"."""

    titulo: str
    icone: str
    resolve: str                       # o problema que o painel resolve (uma linha)
    url_path: str
    path: str | None = None            # arquivo real; None => esqueleto "Em breve"
    abas: tuple[str, ...] = ()          # abas previstas (mostradas no "Em breve")

    @property
    def em_breve(self) -> bool:
        return self.path is None


# ── A vitrine do Sistema TAZZIN: só o que está pronto e impressiona. ─────────
# Regra: nada "Em breve" e nada de tela interna (admin/monitor) na amostra
# pública. Máximo de 3 painéis por grupo; a ordem é a exibida. Painéis fora
# daqui continuam em ``app/pages/`` mas não aparecem no menu nem na home.
ESTRUTURA: list[tuple[str, tuple[Modulo, ...]]] = [
    ("Comercial", (
        Modulo("Radar de Oportunidades", ":material/radar:",
               "Onde estão as próximas vendas antes de virarem pedido.",
               "radar", path="pages/12_Radar.py"),
        Modulo("Descoberta de Mercado", ":material/travel_explore:",
               "Onde estão as empresas que você deveria atender, por atividade, praça e porte.",
               "descoberta-mercado", path="pages/18_Descoberta_Mercado.py"),
        Modulo("Inteligência de Licitações", ":material/gavel:",
               "Licitações públicas do PNCP cruzadas por NCM com o seu catálogo.",
               "licitacoes", path="pages/20_Licitacoes.py"),
    )),
    ("Clientes", (
        Modulo("Pós-Vendas", ":material/sentiment_satisfied:",
               "Nota de recomendação (NPS), satisfação e quem precisa de retorno depois da entrega.",
               "pos-vendas", path="pages/21_Pos_Vendas.py"),
        Modulo("Recuperação de Clientes", ":material/replay:",
               "Quem parou de comprar, quem foi abordado e quanto voltou.",
               "recuperacao-clientes", path="pages/22_Recuperacao_Clientes.py"),
        Modulo("Indicador do Prazo de Entrega", ":material/local_shipping:",
               "Pedidos entregues na data prometida (OTD) e os atrasados em aberto.",
               "prazo-entrega", path="pages/24_Prazo_Entrega.py"),
    )),
    ("Industrial", (
        Modulo("Chão de Fábrica", ":material/precision_manufacturing:",
               "Visão de engenharia da fábrica: máquinas, tempos e processo.",
               "chao-de-fabrica", path="pages/13_Usinagem.py"),
        Modulo("Operadores", ":material/engineering:",
               "Visão 360º por operador: produção, setup, refugo e bonificação.",
               "operadores", path="pages/17_Operadores.py"),
        Modulo("Produção", ":material/factory:",
               "Ordens, rendimento por linha e produção no ritmo da fábrica.",
               "producao", path="pages/2_Produção.py"),
    )),
    ("Pessoas", (
        Modulo("Cargos e Salários", ":material/badge:",
               "Faixas, enquadramento e simulação de mérito por cargo.",
               "cargos-salarios", path="pages/16_Cargos_e_Salários.py"),
        Modulo("Funcionários", ":material/group:",
               "Cadastro e quadro de funcionários por departamento.",
               "funcionarios", path="pages/6_Pessoas.py"),
    )),
    ("Gestão", (
        Modulo("Painel Estratégico", ":material/insights:",
               "Visão de diretoria que cruza todos os módulos.",
               "painel-estrategico", path="pages/0_Painel_Executivo.py"),
        Modulo("Acompanhamento Faturamento", ":material/monitoring:",
               "Evolução do faturamento no período, por cliente e dia a dia.",
               "faturamento", path="pages/1_Vendas.py"),
        Modulo("Financeiro", ":material/payments:",
               "A receber, a pagar e a saúde do caixa mês a mês.",
               "financeiro", path="pages/5_Financeiro.py"),
        Modulo("Bônus Distribuidores", ":material/redeem:",
               "Desconto progressivo por faixa de compra, apurado ao vivo dos pedidos.",
               "bonus-distribuidores", path="pages/23_Bonus_Distribuidores.py"),
    )),
    ("Modo TV", (
        Modulo("Modo TV Comercial", ":material/tv:",
               "Telão que gira entre satisfação, entregas, clientes de volta e distribuidores.",
               "tv-comercial", path="pages/25_Modo_TV_Comercial.py"),
        Modulo("Modo TV Industrial", ":material/tv:",
               "Telão do chão de fábrica: produção, tempo e rendimento.",
               "tv-industrial", path="pages/26_Modo_TV_Industrial.py"),
    )),
]


# ── Página "Em breve": o que o visitante vê ao abrir um esqueleto. ───────────
def _render_em_breve(m: Modulo) -> None:
    """Renderiza o painel-placeholder de um módulo ainda não construído."""
    apply_branding(m.titulo)

    st.markdown(
        f"""
        <style>
          .tz-soon {{
            background: linear-gradient(135deg, {MARINHO} 0%, {GRAFITE} 100%);
            border: 1px solid #1E3247; border-radius: 16px;
            padding: 30px 32px; margin: 6px 0 14px 0;
          }}
          .tz-soon-badge {{
            display: inline-block; background: rgba(76,175,80,.14);
            border: 1px solid {VERDE}; color: {VERDE}; border-radius: 999px;
            padding: 4px 12px; font-size: .78rem; font-weight: 600;
            letter-spacing: .4px; text-transform: uppercase;
          }}
          .tz-soon h1 {{ color: {CINZA_CLARO}; font-size: 1.7rem; margin: 14px 0 4px 0; font-weight: 600; }}
          .tz-soon p {{ color: {CINZA_CLARO}; opacity: .9; font-size: 1.02rem;
                        line-height: 1.55; margin: 8px 0 0 0; max-width: 720px; }}
          .tz-tabs {{ display: flex; flex-wrap: wrap; gap: 8px; margin: 4px 0 2px 0; }}
          .tz-tab {{ border: 1px solid {AZUL}; color: {CINZA_CLARO}; border-radius: 8px;
                     padding: 4px 12px; font-size: .84rem; background: rgba(74,144,217,.10); }}
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        f"""
        <div class="tz-soon">
          <span class="tz-soon-badge">Em breve</span>
          <h1>{m.titulo}</h1>
          <p>{m.resolve}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if m.abas:
        st.markdown("**Este painel vai ter as abas:**")
        pilulas = "".join(f'<span class="tz-tab">{aba}</span>' for aba in m.abas)
        st.markdown(f'<div class="tz-tabs">{pilulas}</div>', unsafe_allow_html=True)

    st.caption(
        "Módulo previsto na amostra do Sistema TAZZIN — ainda não construído "
        "nesta demonstração. É exatamente o tipo de painel que eu monto sob medida."
    )
    st.divider()
    st.page_link("Início.py", label="Voltar ao início", icon=":material/home:")


def _placeholder_page(m: Modulo) -> Callable[[], None]:
    """Fabrica um *callable* único (um por módulo) para o ``st.Page``."""
    def page() -> None:
        _render_em_breve(m)

    page.__name__ = "em_breve_" + m.url_path.replace("-", "_")
    return page


def _as_page(m: Modulo) -> st.Page:
    alvo = m.path if m.path is not None else _placeholder_page(m)
    return st.Page(alvo, title=m.titulo, icon=m.icone, url_path=m.url_path)


def nav_modulos() -> dict[str, list[st.Page]]:
    """Monta o dicionário de grupos → páginas para ``st.navigation``.

    O grupo sem nome ("") no topo mantém o Início visível e aberto por padrão,
    sem cabeçalho.
    """
    grupos: dict[str, list[st.Page]] = {
        "": [st.Page("Início.py", title="Início", icon=":material/home:", default=True)],
    }
    for grupo, modulos in ESTRUTURA:
        grupos[grupo] = [_as_page(m) for m in modulos]
    return grupos
