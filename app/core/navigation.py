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


# ── A amostra do Sistema TAZZIN: (grupo, painéis). A ordem é a exibida. ──────
ESTRUTURA: list[tuple[str, tuple[Modulo, ...]]] = [
    ("Geral", (
        Modulo("Acompanhamento Faturamento", ":material/monitoring:",
               "Evolução do faturamento no período, por cliente e dia a dia.",
               "faturamento", path="pages/1_Vendas.py"),
        Modulo("Indicador do Prazo de Entrega", ":material/local_shipping:",
               "Acompanhamento do prazo de entrega dos pedidos.",
               "prazo-entrega"),
        Modulo("Projetos", ":material/folder_open:",
               "O que está em andamento, o avanço e os próximos marcos.",
               "projetos", path="pages/7_Projetos.py"),
    )),
    ("Comercial", (
        Modulo("Acompanhamento CRM", ":material/hub:",
               "Desempenho comercial puxado direto do CRM.",
               "crm"),
        Modulo("Acompanhamento Pré-Vendas", ":material/filter_alt:",
               "Funil de pré-vendas, das contas novas aos qualificados.",
               "pre-vendas", abas=("Contas Novas", "Qualificados")),
        Modulo("Performance Comercial", ":material/leaderboard:",
               "Indicadores de performance do time comercial.",
               "performance-comercial"),
        Modulo("Recuperação de Clientes", ":material/cardiology:",
               "Efetividade da recuperação de clientes que esfriaram.",
               "recuperacao-clientes"),
        Modulo("Clientes por Linha de Produto", ":material/category:",
               "Carteira cruzada por linha de produto.",
               "clientes-linha-produto"),
        Modulo("Radar de Oportunidades", ":material/radar:",
               "Onde estão as próximas vendas antes de virarem pedido.",
               "radar", path="pages/12_Radar.py"),
        Modulo("Relacionamento com Cliente", ":material/diversity_3:",
               "Fila de contato da carteira ativa, sem planilha paralela.",
               "relacionamento", path="pages/11_Relacionamento.py"),
        Modulo("Descoberta de Mercado", ":material/travel_explore:",
               "Onde estão as empresas que você deveria atender, por atividade, praça e porte.",
               "descoberta-mercado", path="pages/18_Descoberta_Mercado.py"),
        Modulo("Relacionamento com Leads", ":material/person_search:",
               "Fila de contato de quem demonstrou interesse e ainda não comprou.",
               "relacionamento-leads", path="pages/19_Leads.py"),
        Modulo("Inteligência de Licitações", ":material/gavel:",
               "Licitações públicas do PNCP cruzadas por NCM com o seu catálogo.",
               "licitacoes", path="pages/20_Licitacoes.py"),
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
        Modulo("Cobertura de Estoque", ":material/inventory_2:",
               "Cobertura de estoque do PCP: o que falta e o que sobra.",
               "cobertura-estoque", path="pages/3_Estoque.py"),
        Modulo("Registro de Refugo", ":material/recycling:",
               "Lança o refugo e mostra onde ele se concentra, por que acontece e o que custa.",
               "refugo", path="pages/14_Refugo.py"),
        Modulo("Ajustes / Melhorias", ":material/tune:",
               "Registra o ajuste e apura o saldo de tempo ganho ou perdido em cada melhoria.",
               "ajustes", path="pages/15_Ajustes.py"),
        Modulo("Calibração e Manutenção", ":material/build:",
               "Vencimentos de calibração com semáforo, cadastro de ativos e lançamento de serviço.",
               "manutencao", path="pages/8_Manutenção.py"),
        Modulo("Qualidade", ":material/verified:",
               "Taxa de defeito, não-conformidades e o que está reprovando.",
               "qualidade", path="pages/9_Qualidade.py"),
        Modulo("Compras", ":material/shopping_cart:",
               "Quanto se gasta, com quais fornecedores e como eles se saem.",
               "compras", path="pages/4_Compras.py"),
    )),
    ("TI", (
        Modulo("Manutenção de TI", ":material/computer:",
               "Manutenção de computadores e equipamentos de TI.",
               "ti-manutencao", abas=("Lançamentos", "Cadastro", "Análises")),
    )),
    ("RH", (
        Modulo("Visão Geral", ":material/dashboard:",
               "Painel executivo do RH.",
               "rh-visao-geral"),
        Modulo("Frequência", ":material/fingerprint:",
               "Presença, atrasos, horas extras e banco de horas.",
               "rh-frequencia"),
        Modulo("Funcionários", ":material/group:",
               "Cadastro e quadro de funcionários por departamento.",
               "funcionarios", path="pages/6_Pessoas.py"),
        Modulo("Aniversários", ":material/cake:",
               "Aniversários da equipe.",
               "rh-aniversarios"),
        Modulo("Gestão de Férias", ":material/beach_access:",
               "Saldo, vencimento e programação de férias.",
               "rh-ferias",
               abas=("Painel", "Histórico", "Programação", "Saldo e Ajustes")),
        Modulo("Pendências de Cadastro", ":material/assignment_late:",
               "O que ainda falta preencher no cadastro.",
               "rh-pendencias"),
        Modulo("Perfil do Colaborador", ":material/account_circle:",
               "Ficha individual de cada colaborador.",
               "rh-perfil"),
        Modulo("Quadro Previsto", ":material/groups:",
               "Quadro de pessoal previsto x atual.",
               "rh-quadro-previsto"),
        Modulo("Rotatividade", ":material/swap_horiz:",
               "Turnover da equipe, entradas e saídas.",
               "rh-rotatividade"),
        Modulo("Cargos e Salários", ":material/badge:",
               "Faixas, enquadramento e simulação de mérito por cargo.",
               "cargos-salarios", path="pages/16_Cargos_e_Salários.py"),
    )),
    ("Financeiro", (
        Modulo("Bônus Distribuidores", ":material/redeem:",
               "Desconto progressivo apurado ao vivo do ERP.",
               "bonus-distribuidores",
               abas=("Apuração", "Rastreamento", "Histórico", "Cadastro", "Análises")),
        Modulo("Financeiro", ":material/payments:",
               "A receber, a pagar e a saúde do caixa mês a mês.",
               "financeiro", path="pages/5_Financeiro.py"),
    )),
    ("Modo TV", (
        Modulo("Modo TV Comercial", ":material/tv:",
               "Painel para telão — indicadores comerciais.",
               "tv-comercial"),
        Modulo("Modo TV Industrial", ":material/tv:",
               "Painel para telão — chão de fábrica.",
               "tv-industrial"),
    )),
    ("Admin · Indicadores", (
        Modulo("Painel Site", ":material/public:",
               "Visão executiva e análise do site institucional.",
               "painel-site", abas=("Visão Executiva", "Análise do Site")),
        Modulo("Painel Estratégico", ":material/insights:",
               "Visão de diretoria que cruza todos os módulos.",
               "painel-estrategico", path="pages/0_Painel_Executivo.py"),
        Modulo("Clientes Novos e Recuperados", ":material/person_add:",
               "Entradas e recuperações da carteira.",
               "clientes-novos-recuperados"),
        Modulo("Mapa Institucional", ":material/map:",
               "Mapa institucional da operação.",
               "mapa-institucional"),
    )),
    ("Admin · Monitor", (
        Modulo("Sistema", ":material/admin_panel_settings:",
               "Saúde do sistema, acessos e auditoria dos eventos.",
               "monitor-sistema", path="pages/10_Administração.py"),
        Modulo("ETL", ":material/sync:",
               "Monitoramento das cargas de dados (ETL).",
               "monitor-etl"),
        Modulo("Distribuição", ":material/lan:",
               "Monitoramento da distribuição de dados.",
               "monitor-distribuicao"),
        Modulo("Infraestrutura", ":material/dns:",
               "Monitoramento da infraestrutura.",
               "monitor-infra"),
        Modulo("Acessos", ":material/key:",
               "Monitoramento de acessos ao sistema.",
               "monitor-acessos"),
        Modulo("Novidades", ":material/campaign:",
               "Novidades e histórico de versões.",
               "monitor-novidades"),
        Modulo("Controle de Acesso", ":material/lock_person:",
               "Permissões e usuários do sistema.",
               "controle-acesso", abas=("Permissões", "Usuários")),
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
