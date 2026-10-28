"""Pós-Vendas — como o cliente avalia a TAZZIN depois da entrega.

Três números de mercado (NPS, satisfação e taxa de resposta), de onde vem a
nota baixa e a fila de retorno aos detratores. O NPS é lido por zona (crítica,
aperfeiçoamento, qualidade, excelência), não só como número solto.
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

from app.core import charts, ui
from app.core.bootstrap import ensure_demo_data_once
from app.core.branding import apply_branding
from app.database.base import session_scope
from app.domain import postsales_rules as rules
from app.services.postsales_service import PostSalesService

apply_branding("Pós-Vendas")
ensure_demo_data_once()

SEGMENTOS = {"retail": "Varejo", "wholesale": "Atacado", "enterprise": "Corporativo"}
ZONAS = {
    "excelencia": ("Zona de excelência", "ok"),
    "qualidade": ("Zona de qualidade", "ok"),
    "aperfeicoamento": ("Zona de aperfeiçoamento", "atencao"),
    "critica": ("Zona crítica", "ruim"),
    "sem_dados": ("Sem respostas", "neutro"),
}
PRAZO = {"ok": "No prazo", "atencao": "Atenção", "vencido": "Vencido"}
RETORNO = {"pending": "Pendente", "in_contact": "Em contato", "resolved": "Resolvido", "none": "—"}
MIN_RESPOSTAS_MES = 8   # abaixo disso o NPS do mês é ruído
PERIODOS = {"Últimos 3 meses": 90, "Últimos 6 meses": 180, "Últimos 12 meses": 365}

ui.cabecalho(
    "Clientes", "Pós-Vendas",
    "Como o cliente avalia a entrega: nota de recomendação (NPS), satisfação (CSAT) "
    "e quem deu nota baixa e precisa de retorno.",
    direita_rotulo="Meta de NPS", direita_valor=f"{rules.NPS_TARGET}",
)

hoje = date.today()
escolha = st.selectbox("Período", list(PERIODOS), index=2)
inicio = hoje - timedelta(days=PERIODOS[escolha] - 1)

with session_scope() as session:
    service = PostSalesService(session)
    resumo = service.summary(inicio, hoje)
    mensal = service.monthly(inicio, hoje)
    segmentos = service.by_segment(inicio, hoje)
    notas = service.score_distribution(inicio, hoje)
    fila = service.detractor_queue(hoje, inicio, hoje)
    comentarios = service.comments(inicio, hoje)

atual, anterior = resumo["atual"], resumo["anterior"]
if not atual["enviadas"]:
    st.info("Nenhuma pesquisa enviada no período selecionado.")
    st.stop()


def _pts(a, b, casas: int = 0, unidade: str = " pts") -> str:
    """Variação sobre o período anterior, em texto curto."""
    if a is None or b is None:
        return ""
    d = a - b
    sinal = "▲" if d >= 0 else "▼"
    return f"{sinal} {abs(d):.{casas}f}{unidade} vs. período anterior".replace(".", ",")


zona_txt, zona_tom = ZONAS[rules.nps_zone(atual["nps"])]
vencidos = sum(1 for r in fila if r["prazo"] == "vencido")

st.markdown("#### Como estamos")
ui.kpis([
    dict(rotulo="NPS", valor="—" if atual["nps"] is None else f"{atual['nps']:+.0f}",
         tom=zona_tom, situacao=zona_txt,
         nota=f"Meta ≥ {rules.NPS_TARGET} · {_pts(atual['nps'], anterior['nps'])}".rstrip(" ·")),
    dict(rotulo="Satisfação (CSAT)",
         valor="—" if atual["csat"] is None else f"{atual['csat']:.1f}%".replace(".", ","),
         tom="ok" if (atual["csat"] or 0) >= rules.CSAT_TARGET else "atencao",
         situacao="Dentro da meta" if (atual["csat"] or 0) >= rules.CSAT_TARGET else "Abaixo da meta",
         nota=f"Meta ≥ {rules.CSAT_TARGET:.0f}% de notas 4 e 5"),
    dict(rotulo="Taxa de resposta",
         valor="—" if atual["taxa_resposta"] is None else f"{atual['taxa_resposta']:.1f}%".replace(".", ","),
         tom="ok" if (atual["taxa_resposta"] or 0) >= rules.RESPONSE_TARGET else "atencao",
         situacao="Dentro da meta" if (atual["taxa_resposta"] or 0) >= rules.RESPONSE_TARGET else "Abaixo da meta",
         nota=f"{atual['respondidas']} respostas de {atual['enviadas']} pesquisas · meta ≥ {rules.RESPONSE_TARGET:.0f}%"),
    dict(rotulo="Detratores a recontatar", valor=str(len(fila)),
         tom="ruim" if vencidos else ("atencao" if fila else "ok"),
         situacao=f"{vencidos} fora do prazo" if vencidos else ("Todos no prazo" if fila else "Fila zerada"),
         nota=f"Retorno em até {rules.FOLLOWUP_WARN_DAYS} dias"),
])

# ── Evolução e composição ──
col_a, col_b = st.columns([3, 2])
with col_a:
    st.subheader("O NPS está subindo?")
    # Mês com poucas respostas dá NPS de 100 ou -40 por acaso: fica fora do traço.
    com_nps = [m for m in mensal if m["nps"] is not None and m["respondidas"] >= MIN_RESPOSTAS_MES]
    if len(com_nps) >= 2:
        charts.render(charts.line_with_target(
            [m["mes"] for m in com_nps], [m["nps"] for m in com_nps],
            rules.NPS_TARGET, f"Meta {rules.NPS_TARGET}", suffix=""))
        st.caption(f"Linha acima da pontilhada = zona de qualidade. Só entram meses com {MIN_RESPOSTAS_MES}+ respostas.")
    else:
        st.info("Poucos meses com resposta para desenhar a evolução.")
with col_b:
    st.subheader("Quem são os respondentes?")
    charts.render(charts.donut(
        ["Promotores (9–10)", "Neutros (7–8)", "Detratores (0–6)"],
        [atual["promotores"], atual["neutros"], atual["detratores"]],
        colors=[charts.POSITIVO, charts.NEUTRO_CLARO, charts.NEGATIVO]))
    st.caption("NPS = % de promotores menos % de detratores.")

# ── Onde dói ──
col_c, col_d = st.columns(2)
with col_c:
    st.subheader("Qual segmento está menos satisfeito?")
    com_seg = sorted((s for s in segmentos if s["nps"] is not None), key=lambda s: s["nps"], reverse=True)
    if com_seg:
        charts.render(charts.hbar(
            [SEGMENTOS.get(s["segmento"], s["segmento"]) for s in com_seg],
            [s["nps"] for s in com_seg],
            colors=[charts.POSITIVO if s["nps"] >= rules.NPS_TARGET else charts.ATENCAO if s["nps"] >= 0
                    else charts.NEGATIVO for s in com_seg]))
        st.caption("Verde: dentro da meta de NPS. Âmbar: abaixo da meta. Vermelho: mais detratores que promotores.")
with col_d:
    st.subheader("Que notas os clientes dão?")
    nomes = [str(n) for n, _ in notas]
    cores = [charts.NEGATIVO if n <= 6 else charts.NEUTRO_CLARO if n <= 8 else charts.POSITIVO for n, _ in notas]
    fig_notas = charts.hbar(nomes, [q for _, q in notas], colors=cores)
    fig_notas.update_yaxes(tickmode="array", tickvals=nomes)   # mostra todas as notas, de 0 a 10
    charts.render(fig_notas)
    st.caption("De 0 a 10: vermelho = detratores, cinza = neutros, verde = promotores.")

# ── Fila de retorno ──
st.subheader("Detratores para recontatar")
if not fila:
    st.success("Nenhum detrator aguardando retorno.")
else:
    ui.tabela(pd.DataFrame({
        "Prazo": [PRAZO[r["prazo"]] for r in fila],
        "Dias": [r["dias"] for r in fila],
        "Cliente": [r["cliente"] for r in fila],
        "Segmento": [SEGMENTOS.get(r["segmento"], r["segmento"]) for r in fila],
        "Nota": [r["nps"] for r in fila],
        "Comentário": [r["comentario"] or "—" for r in fila],
        "Retorno": [RETORNO[r["retorno"]] for r in fila],
        "Responsável": [r["responsavel"] for r in fila],
    }))
    st.caption(
        f"No prazo até {rules.FOLLOWUP_WARN_DAYS} dias após a resposta, atenção até "
        f"{rules.FOLLOWUP_LATE_DAYS}, vencido acima disso."
    )

# ── Voz do cliente ──
st.subheader("O que os clientes dizem")
if comentarios:
    ui.tabela(pd.DataFrame({
        "Data": [r["respondida"].strftime("%d/%m/%Y") for r in comentarios],
        "Cliente": [r["cliente"] for r in comentarios],
        "Nota": [r["nps"] for r in comentarios],
        "Classe": [rules.classify(r["nps"]).capitalize() for r in comentarios],
        "Comentário": [r["comentario"] for r in comentarios],
    }))
    st.caption("Comentários mais recentes deixados na pesquisa.")
else:
    st.info("Nenhum comentário no período.")
