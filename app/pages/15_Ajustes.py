"""Ajustes / Melhorias — tempo ganho ou perdido no padrão (abas Operação / Análises)."""
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
from app.database.base import session_scope
from app.services.adjustments_service import AdjustmentsService

apply_branding("Ajustes / Melhorias")
ensure_demo_data_once()

TIPOS = ["Melhoria", "Piora"]
_CHAVE = "ajustes"

st.title("Ajustes / Melhorias")
st.caption("Melhorias e pioras no tempo padrão de operação — impacto por operador, máquina e tendência.")

col1, col2 = st.columns(2)
default_start = date.today() - timedelta(days=90)
start = col1.date_input("De", value=default_start)
end = col2.date_input("Até", value=date.today())

with session_scope() as session:
    svc = AdjustmentsService(session)
    by_operator = svc.by_operator(start, end)
    by_machine = svc.by_machine(start, end)
    monthly = svc.monthly_trend(start, end)
    op_alerts = svc.operator_alerts(start, end)
    mc_alerts = svc.machine_alerts(start, end)

operacao_tab, analises_tab = st.tabs(["Operação", "Análises"])

# --------------------------------------------------------------------------- #
# Operação — registrar o ajuste feito no processo                              #
# --------------------------------------------------------------------------- #
with operacao_tab:
    st.subheader("Lançar ajuste")

    operadores = [nome for nome, _, _, _ in by_operator]
    maquinas = [nome for nome, _, _, _ in by_machine]

    with st.form("lancar-ajuste", clear_on_submit=True):
        f1, f2, f3 = st.columns(3)
        data_lanc = f1.date_input("Data", value=date.today())
        operador = (
            f2.selectbox("Operador", operadores) if operadores else f2.text_input("Operador")
        )
        maquina = f3.selectbox("Máquina", maquinas) if maquinas else f3.text_input("Máquina")

        f4, f5 = st.columns(2)
        tipo = f4.selectbox("Tipo", TIPOS)
        segundos = f5.number_input(
            "Segundos por peça", min_value=0.1, step=0.5, value=1.0,
            help="Quanto o tempo padrão mudou por peça — o sinal vem do tipo escolhido.",
        )

        observacao = st.text_input("O que foi alterado (opcional)")
        enviado = st.form_submit_button("Registrar ajuste")

    if enviado:
        if not operador or not maquina:
            st.error("Preencha operador e máquina para registrar.")
        else:
            saldo = float(segundos) if tipo == "Melhoria" else -float(segundos)
            lancamentos.registrar(
                _CHAVE,
                {
                    "Data": data_lanc.strftime("%d/%m/%Y"),
                    "Operador": operador,
                    "Máquina": maquina,
                    "Tipo": tipo,
                    "Saldo (s/peça)": round(saldo, 1),
                    "Alteração": observacao or "—",
                },
            )
            st.success(f"{tipo} de {segundos:.1f}s/peça registrada em {maquina}.")

    registros = lancamentos.listar(_CHAVE)
    st.subheader("Lançamentos desta sessão")
    if not registros:
        st.info("Nenhum ajuste lançado nesta sessão ainda.")
    else:
        saldo_total = sum(item["Saldo (s/peça)"] for item in registros)
        melhorias = sum(1 for item in registros if item["Tipo"] == "Melhoria")
        m1, m2, m3 = st.columns(3)
        m1.metric("Lançamentos", len(registros))
        m2.metric("Melhorias", melhorias)
        m3.metric("Saldo da sessão", f"{saldo_total:+.1f}s")
        st.dataframe(pd.DataFrame(list(reversed(registros))), hide_index=True)
        lancamentos.botao_limpar(_CHAVE)

    lancamentos.aviso_efemero()

# --------------------------------------------------------------------------- #
# Análises — o saldo de tempo por operador, máquina e mês                      #
# --------------------------------------------------------------------------- #
with analises_tab:
    # ── KPIs ──
    total_imp = sum(imp for _, imp, _, _ in by_operator)
    total_wor = sum(wor for _, _, wor, _ in by_operator)
    net_saved = sum(net for _, _, _, net in by_operator)

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Melhorias", str(total_imp))
    k2.metric("Pioras", str(total_wor))
    net_label = f"{net_saved:+,.0f}s".replace(",", ".")
    k3.metric("Saldo líquido", net_label)
    k4.metric("Operadores com registro", str(len(by_operator)))

    # ── Alerts ──
    if op_alerts or mc_alerts:
        st.warning("**Alertas de piora detectados:**")
        for op in op_alerts:
            st.markdown(f"- Operador **{op}** tem mais pioras que melhorias (mín. 3 ajustes)")
        for mc in mc_alerts:
            st.markdown(f"- Máquina **{mc}** tem mais pioras que melhorias (mín. 3 ajustes)")

    # ── By operator ──
    st.subheader("Ajustes por operador")
    if by_operator:
        names = [n for n, _, _, _ in by_operator]
        net_vals = [round(n, 1) for _, _, _, n in by_operator]
        colors = [charts.POSITIVO if v > 0 else charts.NEGATIVO for v in net_vals]
        charts.render(charts.hbar(names, net_vals, colors=colors, suffix="s"))
        st.caption("Tempo líquido economizado (positivo = melhoria) por operador, em segundos por peça.")

        with st.expander("Detalhamento por operador"):
            for name, imp, wor, net in by_operator:
                sinal = "+" if net > 0 else ""
                st.text(f"{name}: {imp} melhorias · {wor} pioras · saldo {sinal}{net:.0f}s")
    else:
        st.info("Nenhum ajuste registrado no período.")

    # ── By machine ──
    st.subheader("Ajustes por máquina")
    if by_machine:
        names = [n for n, _, _, _ in by_machine]
        net_vals = [round(n, 1) for _, _, _, n in by_machine]
        colors = [charts.POSITIVO if v > 0 else charts.NEGATIVO for v in net_vals]
        charts.render(charts.hbar(names, net_vals, colors=colors, suffix="s"))
        st.caption("Saldo líquido por máquina — verde indica ganho de tempo, vermelho indica piora.")
    else:
        st.info("Sem dados por máquina no período.")

    # ── Monthly trend ──
    st.subheader("Tendência mensal — melhorias vs pioras")
    if monthly:
        months = [m for m, _, _ in monthly]
        improvements = [imp for _, imp, _ in monthly]
        worsenings = [wor for _, _, wor in monthly]
        charts.render(
            charts.lines_compare(
                months,
                {
                    "Melhorias": (improvements, charts.POSITIVO),
                    "Pioras": (worsenings, charts.NEGATIVO),
                },
            )
        )
        st.caption("Evolução mensal do volume de ajustes — cruzamento das linhas indica inversão de tendência.")
    else:
        st.info("Sem dados mensais no período selecionado.")
