"""Inteligência de Licitações — compras públicas (PNCP) cruzadas por NCM.

Sete recortes do mesmo dado: o tamanho do mercado público, o que dá para
disputar hoje, o que os concorrentes conseguiram segurar em ata, a consulta
crua, o catálogo próprio, o quanto desse mercado o catálogo alcança e a fila
de operação. O NCM é a dobradiça: sem ele, licitação é ruído.
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

from app.core import charts, lancamentos
from app.core.bootstrap import ensure_demo_data_once
from app.core.branding import apply_branding
from app.core.formatting import format_brl
from app.database.base import session_scope
from app.services.bidding_service import BiddingService

apply_branding("Inteligência de Licitações")
ensure_demo_data_once()

MODALIDADES = {
    "pregao_eletronico": "Pregão eletrônico",
    "dispensa": "Dispensa",
    "concorrencia": "Concorrência",
    "inexigibilidade": "Inexigibilidade",
}
SITUACOES = {
    "aberta": "Aberta",
    "homologada": "Homologada",
    "fracassada": "Fracassada",
    "cancelada": "Cancelada",
}
_CHAVE = "licitacoes"

st.title("Inteligência de Licitações")
st.caption(
    "O que o poder público está comprando, cruzado por NCM com o que a empresa "
    "vende. Fonte pública (PNCP) virando fila de decisão."
)

hoje = date.today()
col1, col2 = st.columns(2)
inicio = col1.date_input("De", value=hoje - timedelta(days=730))
fim = col2.date_input("Até", value=hoje)

with session_scope() as session:
    service = BiddingService(session)
    mercado = service.market(inicio, fim)
    oportunidades = service.opportunities(hoje)
    atas = service.active_price_records(hoje)
    catalogo = service.catalog_items()
    cobertura = service.coverage(inicio, fim)
    licitacoes = service.search(inicio, fim)

(
    mercado_tab,
    oportunidades_tab,
    atas_tab,
    licitacoes_tab,
    catalogo_tab,
    cobertura_tab,
    operacao_tab,
) = st.tabs(
    ["Mercado", "Oportunidades", "Atas", "Licitações", "Catálogo", "Cobertura", "Operação"]
)

# --------------------------------------------------------------------------- #
# Mercado — o tamanho do jogo                                                  #
# --------------------------------------------------------------------------- #
with mercado_tab:
    valor_total = sum(valor for _, valor in mercado["mensal"])
    k1, k2, k3 = st.columns(3)
    k1.metric("Valor licitado no período", format_brl(valor_total))
    k2.metric("Licitações publicadas", f"{len(licitacoes):,.0f}".replace(",", "."))
    k3.metric("Órgãos compradores", len(mercado["top_orgaos"]))

    st.subheader("Evolução do valor licitado")
    if mercado["mensal"]:
        meses, valores = zip(*mercado["mensal"])
        charts.render(charts.area(list(meses), list(valores), money=True))
        st.caption("Volume publicado mês a mês — sazonalidade de compra pública é forte no fim do exercício.")
    else:
        st.info("Nenhuma licitação publicada no período.")

    uf_col, modalidade_col = st.columns([3, 2])
    with uf_col:
        st.subheader("Por estado")
        if mercado["por_estado"]:
            ufs, valores = zip(*mercado["por_estado"])
            charts.render(charts.hbar(list(ufs), list(valores), money=True))
    with modalidade_col:
        st.subheader("Por modalidade")
        if mercado["por_modalidade"]:
            nomes = [MODALIDADES.get(m, m) for m, _ in mercado["por_modalidade"]]
            valores = [valor for _, valor in mercado["por_modalidade"]]
            charts.render(charts.donut(nomes, valores, money=True))
            st.caption("Pregão eletrônico domina — é onde a disputa é por preço.")

    st.subheader("Órgãos que mais compram")
    if mercado["top_orgaos"]:
        nomes, valores = zip(*mercado["top_orgaos"])
        charts.render(charts.hbar(list(nomes), list(valores), money=True))
        st.caption("Concentração por comprador — relacionamento com estes órgãos rende mais.")

# --------------------------------------------------------------------------- #
# Oportunidades — o que dá para disputar agora                                 #
# --------------------------------------------------------------------------- #
with oportunidades_tab:
    st.subheader("Licitações abertas que batem com o catálogo")
    if not oportunidades:
        st.info("Nenhuma licitação aberta cruzando com o catálogo no momento.")
    else:
        valor_potencial = sum(item["valor"] for item in oportunidades)
        urgentes = [item for item in oportunidades if 0 <= item["dias"] <= 7]
        o1, o2, o3 = st.columns(3)
        o1.metric("Oportunidades abertas", len(oportunidades))
        o2.metric("Valor potencial", format_brl(valor_potencial))
        o3.metric("Abrem em até 7 dias", len(urgentes), delta="prioridade" if urgentes else None,
                  delta_color="inverse")

        tabela = pd.DataFrame(
            {
                "Abre em": [f"{item['dias']}d" for item in oportunidades],
                "Data": [item["abertura"].strftime("%d/%m/%Y") for item in oportunidades],
                "Órgão": [item["orgao"] for item in oportunidades],
                "Cidade": [f"{item['cidade']}/{item['estado']}" for item in oportunidades],
                "Modalidade": [MODALIDADES.get(item["modalidade"], item["modalidade"]) for item in oportunidades],
                "Itens nossos": [item["itens"] for item in oportunidades],
                "Valor": [format_brl(item["valor"]) for item in oportunidades],
                "PNCP": [item["pncp"] for item in oportunidades],
            }
        )
        st.dataframe(tabela, hide_index=True)
        st.caption(
            "Só entram licitações cujo NCM existe no catálogo — o resto é ruído. "
            "«Itens nossos» é quantos itens daquela licitação a empresa sabe fornecer."
        )

# --------------------------------------------------------------------------- #
# Atas — o preço que o concorrente segurou                                     #
# --------------------------------------------------------------------------- #
with atas_tab:
    st.subheader("Atas de registro de preços vigentes")
    if not atas:
        st.info("Nenhuma ata vigente no momento.")
    else:
        comparaveis = [ata for ata in atas if ata["gap_pct"] is not None]
        acima = [ata for ata in comparaveis if ata["gap_pct"] > 0]
        a1, a2, a3 = st.columns(3)
        a1.metric("Atas vigentes", len(atas))
        a2.metric("Com preço comparável", len(comparaveis))
        a3.metric(
            "Ata acima do nosso preço", len(acima),
            delta="espaço para entrar" if acima else None, delta_color="off",
        )

        tabela = pd.DataFrame(
            {
                "NCM": [ata["ncm"] for ata in atas],
                "Item": [ata["descricao"] for ata in atas],
                "Órgão": [ata["orgao"] for ata in atas],
                "Fornecedor": [ata["fornecedor"] for ata in atas],
                "Preço da ata": [format_brl(ata["preco_ata"]) for ata in atas],
                "Nosso preço": [
                    format_brl(ata["nosso_preco"]) if ata["nosso_preco"] is not None else "—"
                    for ata in atas
                ],
                "Gap": [
                    f"{ata['gap_pct']:+.1f}%" if ata["gap_pct"] is not None else "—" for ata in atas
                ],
                "Vence em": [ata["valida_ate"].strftime("%d/%m/%Y") for ata in atas],
            }
        )
        st.dataframe(tabela, hide_index=True)
        st.caption(
            "Gap positivo = a ata paga mais do que a empresa cobra, ou seja, há margem para "
            "disputar a próxima. Gap negativo = o concorrente entrou abaixo do nosso preço."
        )

# --------------------------------------------------------------------------- #
# Licitações — a consulta crua                                                 #
# --------------------------------------------------------------------------- #
with licitacoes_tab:
    st.subheader("Consultar licitações")
    c1, c2, c3 = st.columns(3)
    ufs_disponiveis = sorted({item["estado"] for item in licitacoes})
    ufs = c1.multiselect("Estado (UF)", ufs_disponiveis)
    modalidades_escolhidas = c2.multiselect("Modalidade", list(MODALIDADES.values()))
    situacoes_escolhidas = c3.multiselect("Situação", list(SITUACOES.values()))

    codigo_modalidade = {rotulo: codigo for codigo, rotulo in MODALIDADES.items()}
    codigo_situacao = {rotulo: codigo for codigo, rotulo in SITUACOES.items()}

    with session_scope() as session:
        filtradas = BiddingService(session).search(
            inicio,
            fim,
            states=ufs or None,
            modalities=[codigo_modalidade[m] for m in modalidades_escolhidas] or None,
            statuses=[codigo_situacao[s] for s in situacoes_escolhidas] or None,
        )

    if not filtradas:
        st.info("Nenhuma licitação com esses filtros.")
    else:
        st.caption(f"{len(filtradas)} licitação(ões) — as mais recentes primeiro.")
        tabela = pd.DataFrame(
            {
                "Publicação": [item["publicacao"].strftime("%d/%m/%Y") for item in filtradas],
                "Abertura": [item["abertura"].strftime("%d/%m/%Y") for item in filtradas],
                "Órgão": [item["orgao"] for item in filtradas],
                "Cidade": [f"{item['cidade']}/{item['estado']}" for item in filtradas],
                "Modalidade": [MODALIDADES.get(item["modalidade"], item["modalidade"]) for item in filtradas],
                "Situação": [SITUACOES.get(item["situacao"], item["situacao"]) for item in filtradas],
                "Valor estimado": [format_brl(item["valor"]) for item in filtradas],
                "PNCP": [item["pncp"] for item in filtradas],
            }
        )
        st.dataframe(tabela, hide_index=True)

# --------------------------------------------------------------------------- #
# Catálogo — o que a empresa sabe vender                                       #
# --------------------------------------------------------------------------- #
with catalogo_tab:
    st.subheader("Catálogo próprio por NCM")
    if not catalogo:
        st.info("Catálogo vazio.")
    else:
        familias = sorted({item["familia"] for item in catalogo})
        c1, c2 = st.columns(2)
        c1.metric("NCMs no catálogo", len(catalogo))
        c2.metric("Famílias de produto", len(familias))

        tabela = pd.DataFrame(
            {
                "NCM": [item["ncm"] for item in catalogo],
                "Descrição": [item["descricao"] for item in catalogo],
                "Família": [item["familia"] for item in catalogo],
                "Nosso preço": [format_brl(item["nosso_preco"]) for item in catalogo],
            }
        )
        st.dataframe(tabela, hide_index=True)
        st.caption(
            "É este cadastro que decide o que é oportunidade. Incluir um NCM aqui "
            "faz o módulo passar a enxergar todas as licitações daquele item."
        )

# --------------------------------------------------------------------------- #
# Cobertura — quanto do mercado o catálogo alcança                             #
# --------------------------------------------------------------------------- #
with cobertura_tab:
    st.subheader("Cobertura do catálogo sobre a demanda pública")
    if not cobertura["demanda"]:
        st.info("Sem demanda no período para calcular cobertura.")
    else:
        descoberto = cobertura["valor_total"] - cobertura["valor_coberto"]
        c1, c2, c3 = st.columns(3)
        c1.metric("Demanda mapeada", format_brl(cobertura["valor_total"]))
        c2.metric("Coberta pelo catálogo", f"{cobertura['pct_coberto']:.1f}%")
        c3.metric("Fora do catálogo", format_brl(descoberto))

        grafico_col, texto_col = st.columns([2, 3])
        with grafico_col:
            charts.render(
                charts.donut(
                    ["Coberto pelo catálogo", "Fora do catálogo"],
                    [cobertura["valor_coberto"], descoberto],
                    colors=[charts.POSITIVO, charts.NEGATIVO],
                    money=True,
                )
            )
        with texto_col:
            st.markdown("**NCMs mais licitados que não estão no catálogo**")
            fora = cobertura["fora_do_catalogo"][:8]
            if not fora:
                st.success("O catálogo cobre todos os NCMs licitados no período.")
            else:
                for item in fora:
                    st.text(f"{item['ncm']} · {item['descricao'][:38]} — {format_brl(item['valor'])}")
                st.caption("Cada linha é receita pública que a empresa hoje não consegue disputar.")

        st.subheader("Demanda por NCM")
        demanda = cobertura["demanda"]
        tabela = pd.DataFrame(
            {
                "No catálogo": ["✅" if item["no_catalogo"] else "❌" for item in demanda],
                "NCM": [item["ncm"] for item in demanda],
                "Item": [item["descricao"] for item in demanda],
                "Licitações": [item["licitacoes"] for item in demanda],
                "Valor licitado": [format_brl(item["valor"]) for item in demanda],
            }
        )
        st.dataframe(tabela, hide_index=True)

# --------------------------------------------------------------------------- #
# Operação — a fila de quem vai disputar                                       #
# --------------------------------------------------------------------------- #
with operacao_tab:
    st.subheader("Fila de participação")
    if not oportunidades:
        st.info("Nenhuma oportunidade aberta para trabalhar.")
    else:
        proximas = [item for item in oportunidades if item["dias"] >= 0][:40]
        rotulos = {
            f"{item['pncp']} — {item['orgao'][:40]}": item for item in proximas
        }

        with st.form("marcar-licitacao", clear_on_submit=True):
            f1, f2 = st.columns([3, 2])
            escolhida = f1.selectbox("Licitação", list(rotulos)) if rotulos else None
            responsavel = f2.text_input("Responsável")
            decisao = st.selectbox("Decisão", ["Vamos participar", "Em análise", "Não participar"])
            observacao = st.text_input("Observação (opcional)")
            enviado = st.form_submit_button("Registrar decisão")

        if enviado:
            if not escolhida or not responsavel:
                st.error("Escolha a licitação e informe o responsável.")
            else:
                item = rotulos[escolhida]
                lancamentos.registrar(
                    _CHAVE,
                    {
                        "PNCP": item["pncp"],
                        "Órgão": item["orgao"],
                        "Abertura": item["abertura"].strftime("%d/%m/%Y"),
                        "Decisão": decisao,
                        "Responsável": responsavel,
                        "Valor": format_brl(item["valor"]),
                        "Observação": observacao or "—",
                    },
                )
                st.success(f"«{decisao}» registrado para {item['orgao']}.")

        registros = lancamentos.listar(_CHAVE)
        if registros:
            st.markdown("**Decisões desta sessão**")
            st.dataframe(pd.DataFrame(list(reversed(registros))), hide_index=True)
            lancamentos.botao_limpar(_CHAVE)
        lancamentos.aviso_efemero()

st.caption(
    "Dados sintéticos nesta amostra. Num cliente real o módulo consome o PNCP "
    "e cruza automaticamente com o catálogo de NCMs da empresa."
)
