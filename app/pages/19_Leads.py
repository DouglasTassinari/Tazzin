"""Relacionamento com Leads — a fila de contato de quem ainda não comprou.

O módulo Relacionamento cuida de quem já é cliente. Aqui é o outro lado: quem
entrou por algum canal, demonstrou interesse e ainda não virou pedido. A fila
é ordenada pelo que dói — há quantos dias ninguém encosta no lead.
"""
# ruff: noqa: E402
from __future__ import annotations

import sys
from pathlib import Path as _Path

_PROJECT_ROOT = str(_Path(__file__).resolve().parents[2])
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from datetime import date

import pandas as pd
import streamlit as st

from app.core import charts, lancamentos
from app.core.bootstrap import ensure_demo_data_once
from app.core.branding import apply_branding
from app.core.formatting import format_brl
from app.database.base import session_scope
from app.domain import leads_rules
from app.services.leads_service import LeadsService

apply_branding("Relacionamento com Leads")
ensure_demo_data_once()

ORIGENS = {
    "site": "Site",
    "indicacao": "Indicação",
    "feira": "Feira",
    "outbound": "Outbound",
    "marketplace": "Marketplace",
}
STATUS = {
    "novo": "Novo",
    "em_contato": "Em contato",
    "qualificado": "Qualificado",
    "descartado": "Descartado",
}
FAROL = {"vencido": "🔴 Vencido", "atencao": "🟡 Atenção", "ok": "🟢 Em dia"}
_CHAVE = "leads"

st.title("Relacionamento com Leads")
st.caption(
    "Quem demonstrou interesse e ainda não comprou. A fila é ordenada pelo lead "
    "mais abandonado — quem está há mais tempo sem contato aparece primeiro."
)

hoje = date.today()
with session_scope() as session:
    service = LeadsService(session)
    fila = service.queue(hoje)
    resumo = service.summary(hoje)
    distribuicao = service.distribution()

# ── KPIs ──
k1, k2, k3, k4 = st.columns(4)
k1.metric("Leads em jogo", resumo["total"])
k2.metric(
    f"Sem contato há +{leads_rules.LEAD_LATE_DAYS}d",
    resumo["vencidos"],
    delta="fila de resgate" if resumo["vencidos"] else None,
    delta_color="inverse",
)
k3.metric("Qualificados", resumo["qualificados"])
k4.metric("Valor potencial", format_brl(resumo["valor_potencial"]))

if not fila:
    st.info("Nenhum lead em jogo no momento.")
    st.stop()

vencidos = [lead for lead in fila if lead["farol"] == "vencido"]
if vencidos:
    st.warning(
        f"**{len(vencidos)} lead(s) passaram de {leads_rules.LEAD_LATE_DAYS} dias sem contato.** "
        f"O mais abandonado é {vencidos[0]['empresa']} — {vencidos[0]['dias_sem_contato']} dias."
    )

# ── A fila ──
st.subheader("Fila de contato")
tabela = pd.DataFrame(
    {
        "Farol": [FAROL[lead["farol"]] for lead in fila],
        "Dias": [lead["dias_sem_contato"] for lead in fila],
        "Empresa": [lead["empresa"] for lead in fila],
        "Contato": [lead["contato"] for lead in fila],
        "Cidade": [f"{lead['cidade']}/{lead['estado']}" for lead in fila],
        "Origem": [ORIGENS.get(lead["origem"], lead["origem"]) for lead in fila],
        "Status": [STATUS.get(lead["status"], lead["status"]) for lead in fila],
        "Responsável": [lead["responsavel"] for lead in fila],
        "Potencial": [format_brl(lead["valor_potencial"]) for lead in fila],
    }
)
st.dataframe(tabela, hide_index=True)
st.caption(
    f"Verde até {leads_rules.LEAD_WARN_DAYS} dias sem contato, amarelo até "
    f"{leads_rules.LEAD_LATE_DAYS}, vermelho acima disso."
)

# ── Registrar contato (escrita efêmera) ──
st.subheader("Registrar contato")
empresas = [lead["empresa"] for lead in fila]
with st.form("registrar-contato-lead", clear_on_submit=True):
    c1, c2, c3 = st.columns(3)
    empresa = c1.selectbox("Lead", empresas)
    data_contato = c2.date_input("Data do contato", value=hoje)
    desfecho = c3.selectbox("Desfecho", ["Em contato", "Qualificado", "Descartado"])
    anotacao = st.text_input("Anotação (opcional)")
    enviado = st.form_submit_button("Registrar contato")

if enviado:
    lancamentos.registrar(
        _CHAVE,
        {
            "Data": data_contato.strftime("%d/%m/%Y"),
            "Lead": empresa,
            "Desfecho": desfecho,
            "Anotação": anotacao or "—",
        },
    )
    st.success(f"Contato com {empresa} registrado como «{desfecho}».")

registros = lancamentos.listar(_CHAVE)
if registros:
    st.dataframe(pd.DataFrame(list(reversed(registros))), hide_index=True)
    lancamentos.botao_limpar(_CHAVE)
lancamentos.aviso_efemero()

# ── De onde vêm e em que pé estão ──
origem_col, status_col = st.columns(2)
with origem_col:
    st.subheader("De onde vêm os leads")
    if distribuicao["por_origem"]:
        nomes = [ORIGENS.get(o, o) for o, _ in distribuicao["por_origem"]]
        valores = [total for _, total in distribuicao["por_origem"]]
        charts.render(charts.hbar(nomes, valores))
        st.caption("Canal de entrada — mostra onde vale investir para encher o funil.")

with status_col:
    st.subheader("Em que pé está o funil")
    if distribuicao["por_status"]:
        nomes = [STATUS.get(s, s) for s, _ in distribuicao["por_status"]]
        valores = [total for _, total in distribuicao["por_status"]]
        charts.render(charts.donut(nomes, valores))
        st.caption("Distribuição por status, incluindo os descartados.")

st.subheader("Entrada de leads por mês")
if distribuicao["entrada_mensal"]:
    meses, quantidades = zip(*distribuicao["entrada_mensal"])
    charts.render(charts.area(list(meses), list(quantidades)))
    st.caption("Volume de novos leads mês a mês — queda aqui vira queda de venda lá na frente.")
