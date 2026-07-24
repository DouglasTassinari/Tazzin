"""Calibração e Manutenção — vencimentos com semáforo (abas Lançamentos / Cadastro / Análises)."""
# ruff: noqa: E402  -- sys.path bootstrap below must run before the app.* imports
from __future__ import annotations

import sys
from pathlib import Path as _Path

# Streamlit only adds this script's own folder to sys.path, not the project
# root, so the "app.*" imports below would fail without this.
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
from app.database.models.maintenance import AssetCriticality, MaintenanceStatus
from app.domain.maintenance_rules import CALIBRATION_INTERVAL_MONTHS, CALIBRATION_WARN_DAYS
from app.services.maintenance_service import MaintenanceService

apply_branding("Calibração e Manutenção")

ensure_demo_data_once()

PRIORIDADES = {
    "urgent": ("Urgente", charts.NEGATIVO),
    "high": ("Alta", charts.PRIMARIA),
    "medium": ("Média", charts.NEUTRO_CLARO),
    "low": ("Baixa", charts.NEUTRO),
}
CATEGORIAS = {
    "machine": "Máquina",
    "vehicle": "Veículo",
    "facility": "Instalação",
    "it_equipment": "Equipamento de TI",
}
CRITICIDADES = {"low": "Baixa", "medium": "Média", "high": "Alta", "critical": "Crítica"}
FAROL = {"vencido": "🔴 Vencido", "atencao": "🟡 A vencer", "ok": "🟢 Em dia"}
TIPOS_SERVICO = ["Calibração", "Preventiva", "Corretiva"]
_CHAVE = "manutencao"

st.title("Calibração e Manutenção")
st.caption("Vencimentos de calibração, conservação de ativos e custo de manutenção.")

col1, col2 = st.columns(2)
default_start = date.today() - timedelta(days=365)
start = col1.date_input("De", value=default_start)
end = col2.date_input("Até", value=date.today())

hoje = date.today()
with session_scope() as session:
    service = MaintenanceService(session)
    cost_rows = service.monthly_maintenance_cost(start, end)
    priority_rows = service.open_requests_by_priority()
    cadastro = service.asset_registry(hoje)

    total_cost = sum(v for _, v in cost_rows)
    open_requests = sum(
        len(service.requests.by_status(status))
        for status in (
            MaintenanceStatus.OPEN,
            MaintenanceStatus.SCHEDULED,
            MaintenanceStatus.IN_PROGRESS,
        )
    )
    critical_assets = len(service.assets.by_criticality(AssetCriticality.CRITICAL))

lancamentos_tab, cadastro_tab, analises_tab = st.tabs(["Lançamentos", "Cadastro", "Análises"])

# --------------------------------------------------------------------------- #
# Lançamentos — registrar o serviço executado no ativo                         #
# --------------------------------------------------------------------------- #
with lancamentos_tab:
    st.subheader("Lançar serviço")

    ativos = [f"{item['tag']} — {item['nome']}" for item in cadastro]

    with st.form("lancar-manutencao", clear_on_submit=True):
        f1, f2, f3 = st.columns(3)
        data_lanc = f1.date_input("Data do serviço", value=hoje)
        ativo = f2.selectbox("Ativo", ativos) if ativos else f2.text_input("Ativo")
        tipo = f3.selectbox("Tipo", TIPOS_SERVICO)

        f4, f5 = st.columns(2)
        horas = f4.number_input("Horas gastas", min_value=0.5, step=0.5, value=1.0)
        custo = f5.number_input("Custo (R$)", min_value=0.0, step=50.0, value=0.0)

        observacao = st.text_input("Observação (opcional)")
        enviado = st.form_submit_button("Registrar serviço")

    if enviado:
        if not ativo:
            st.error("Selecione o ativo para registrar o serviço.")
        else:
            lancamentos.registrar(
                _CHAVE,
                {
                    "Data": data_lanc.strftime("%d/%m/%Y"),
                    "Ativo": ativo,
                    "Tipo": tipo,
                    "Horas": float(horas),
                    "Custo": format_brl(float(custo)),
                    "Observação": observacao or "—",
                },
            )
            st.success(f"{tipo} registrada em {ativo}.")

    registros = lancamentos.listar(_CHAVE)
    st.subheader("Lançamentos desta sessão")
    if not registros:
        st.info("Nenhum serviço lançado nesta sessão ainda.")
    else:
        horas_total = sum(item["Horas"] for item in registros)
        m1, m2 = st.columns(2)
        m1.metric("Lançamentos", len(registros))
        m2.metric("Horas registradas", f"{horas_total:.1f}h")
        st.dataframe(pd.DataFrame(list(reversed(registros))), hide_index=True)
        lancamentos.botao_limpar(_CHAVE)

    lancamentos.aviso_efemero()

# --------------------------------------------------------------------------- #
# Cadastro — os ativos e o semáforo de vencimento da calibração                #
# --------------------------------------------------------------------------- #
with cadastro_tab:
    st.subheader("Ativos e vencimento de calibração")

    if not cadastro:
        st.info("Nenhum ativo cadastrado.")
    else:
        vencidos = [item for item in cadastro if item["farol"] == "vencido"]
        a_vencer = [item for item in cadastro if item["farol"] == "atencao"]

        c1, c2, c3 = st.columns(3)
        c1.metric("Ativos cadastrados", len(cadastro))
        c2.metric("Vencidos", len(vencidos), delta="ação imediata" if vencidos else None, delta_color="inverse")
        c3.metric("Vencem em 30 dias", len(a_vencer))

        if vencidos:
            st.warning(
                f"**{len(vencidos)} ativo(s) com calibração vencida** — "
                f"o mais atrasado é {vencidos[0]['nome']} ({abs(vencidos[0]['dias'])} dias)."
            )

        tabela = pd.DataFrame(
            {
                "Farol": [FAROL[item["farol"]] for item in cadastro],
                "Tag": [item["tag"] for item in cadastro],
                "Ativo": [item["nome"] for item in cadastro],
                "Categoria": [CATEGORIAS.get(item["categoria"], item["categoria"]) for item in cadastro],
                "Criticidade": [CRITICIDADES.get(item["criticidade"], item["criticidade"]) for item in cadastro],
                "Último serviço": [
                    item["ultimo_servico"].strftime("%d/%m/%Y") if item["ultimo_servico"] else "nunca"
                    for item in cadastro
                ],
                "Vence em": [item["vencimento"].strftime("%d/%m/%Y") for item in cadastro],
                "Dias": [item["dias"] for item in cadastro],
            }
        )
        st.dataframe(tabela, hide_index=True)

        intervalos = " · ".join(
            f"{CRITICIDADES[c.value]}: {m} meses" for c, m in CALIBRATION_INTERVAL_MONTHS.items()
        )
        st.caption(
            f"O vencimento conta a partir do último serviço registrado (ou da instalação, se o ativo "
            f"nunca foi atendido) somado ao intervalo da criticidade — {intervalos}. "
            f"O farol fica amarelo {CALIBRATION_WARN_DAYS} dias antes de vencer."
        )

# --------------------------------------------------------------------------- #
# Análises — custo e backlog                                                   #
# --------------------------------------------------------------------------- #
with analises_tab:
    kpi1, kpi2, kpi3 = st.columns(3)
    kpi1.metric("Solicitações abertas", open_requests)
    kpi2.metric("Custo de manutenção no período", format_brl(total_cost))
    kpi3.metric("Ativos críticos", critical_assets)

    cost_col, backlog_col = st.columns([3, 2])
    with cost_col:
        st.subheader("Custo de manutenção por mês")
        if not cost_rows:
            st.info("Nenhum registro de manutenção no período selecionado.")
        else:
            months, values = zip(*cost_rows)
            charts.render(charts.area(months, values, money=True))
            st.caption("Gasto mensal com manutenção — alta contínua pode indicar ativos em fim de vida.")

    with backlog_col:
        st.subheader("Backlog por prioridade")
        if not priority_rows:
            st.info("Nenhuma solicitação de manutenção aberta.")
        else:
            by_priority = dict(priority_rows)
            items = [
                (label, by_priority[key], color)
                for key, (label, color) in PRIORIDADES.items()
                if key in by_priority
            ]
            charts.render(
                charts.hbar(
                    [i[0] for i in items], [i[1] for i in items], colors=[i[2] for i in items]
                )
            )
            st.caption("Solicitações abertas: vermelho = urgente, deve ser tratado primeiro.")
