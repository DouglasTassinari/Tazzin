"""Página inicial: a **vitrine** do TAZZIN (registrada em ``app/main.py``).

Não é o painel de um produto fechado — é a porta de entrada de uma amostra de
módulos independentes. Cada cartão abaixo é uma ferramenta que resolve um
problema real da operação, funciona sozinha e pode ser contratada e
personalizada de forma individual. A home conta essa história e leva a
pessoa para o módulo que interessa.
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

apply_branding("Início")
ensure_demo_data_once()

# ── Catálogo: cada módulo pelo PROBLEMA que resolve, não pela tabela que tem. ──
# (grupo, [(caminho_da_página, título, ícone, o-que-resolve)])
CATALOGO: list[tuple[str, list[tuple[str, str, str, str]]]] = [
    ("Comercial", [
        ("pages/1_Vendas.py", "Vendas", ":material/sell:",
         "Quanto entrou, de quem, e quais clientes puxam o faturamento."),
        ("pages/11_Relacionamento.py", "Relacionamento", ":material/diversity_3:",
         "Cada cliente e o histórico da relação, sem planilha paralela."),
        ("pages/12_Radar.py", "Radar de Oportunidades", ":material/radar:",
         "Onde estão as próximas vendas antes de virarem pedido."),
    ]),
    ("Chão de Fábrica", [
        ("pages/2_Produção.py", "Produção", ":material/factory:",
         "Ordens, rendimento por linha e refugo, no ritmo da fábrica."),
        ("pages/13_Usinagem.py", "Usinagem", ":material/precision_manufacturing:",
         "Rendimento dos operadores, uso das máquinas e composição do tempo."),
        ("pages/17_Operadores.py", "Operadores", ":material/engineering:",
         "Visão 360º por pessoa: produção, setup, refugo e bonificação."),
        ("pages/14_Refugo.py", "Refugo", ":material/recycling:",
         "Onde o refugo se concentra, por que acontece e o que ele custa."),
        ("pages/15_Ajustes.py", "Ajustes", ":material/tune:",
         "Saldo de tempo ganho ou perdido em cada melhoria de processo."),
        ("pages/8_Manutenção.py", "Manutenção", ":material/build:",
         "Ativos, chamados abertos e o custo de manter tudo rodando."),
        ("pages/9_Qualidade.py", "Qualidade", ":material/verified:",
         "Taxa de defeito, não-conformidades e o que está reprovando."),
    ]),
    ("Suprimentos", [
        ("pages/3_Estoque.py", "Estoque", ":material/inventory_2:",
         "O que tem, o que está acabando e onde o capital está parado."),
        ("pages/4_Compras.py", "Compras", ":material/shopping_cart:",
         "Quanto se gasta, com quais fornecedores e como eles se saem."),
    ]),
    ("Gestão", [
        ("pages/5_Financeiro.py", "Financeiro", ":material/payments:",
         "A receber, a pagar e a saúde do caixa mês a mês."),
        ("pages/7_Projetos.py", "Projetos", ":material/folder_open:",
         "O que está em andamento, o avanço e os próximos marcos."),
        ("pages/0_Painel_Executivo.py", "Painel Executivo", ":material/insights:",
         "Opcional: a visão que cruza os módulos quando eles conversam."),
    ]),
    ("RH", [
        ("pages/6_Pessoas.py", "Pessoas", ":material/group:",
         "Quadro ativo, ausências e a estrutura por departamento."),
        ("pages/16_Cargos_e_Salários.py", "Cargos e Salários", ":material/badge:",
         "Faixas, enquadramento e simulação de mérito por cargo."),
    ]),
    ("Sistema", [
        ("pages/10_Administração.py", "Administração", ":material/admin_panel_settings:",
         "Saúde do sistema, acessos e auditoria dos eventos."),
    ]),
]

# ── CSS só do que o tema global não cobre (hero e pílulas de valor). ──
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

st.caption(
    "Os dados desta amostra são fictícios, gerados só para você navegar. "
    "Explore qualquer módulo pelo cartão ou pela barra lateral."
)
st.divider()

# ── Catálogo de módulos: um cartão clicável por ferramenta. ──
for grupo, modulos in CATALOGO:
    st.subheader(grupo)
    # Três cartões por linha; completa a última linha com espaços vazios.
    for inicio in range(0, len(modulos), 3):
        linha = modulos[inicio:inicio + 3]
        colunas = st.columns(3)
        for coluna, (caminho, titulo, icone, problema) in zip(colunas, linha):
            with coluna, st.container(border=True):
                st.markdown(f"**{titulo}**")
                st.caption(problema)
                st.page_link(caminho, label="Abrir painel", icon=icone)
    st.write("")

st.divider()
st.markdown(
    f"<p style='color:{CINZA_MEDIO};font-size:.92rem;'>"
    "Falta o módulo que resolveria o <i>seu</i> problema? Ele ainda não existe aqui — "
    "mas é exatamente isso que eu construo: a ferramenta sob medida para a sua operação."
    "</p>",
    unsafe_allow_html=True,
)
