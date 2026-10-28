"""Modo TV Comercial — painel de telão que gira entre os indicadores de clientes."""
# ruff: noqa: E402
from __future__ import annotations

import sys
from pathlib import Path as _Path

_PROJECT_ROOT = str(_Path(__file__).resolve().parents[2])
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from datetime import date, timedelta

import streamlit as st

from app.core import charts, tv
from app.core.bootstrap import ensure_demo_data_once
from app.core.branding import apply_branding
from app.database.base import session_scope
from app.domain import bonus_rules, delivery_rules, postsales_rules, recovery_rules
from app.services.bonus_service import BonusService
from app.services.delivery_service import DeliveryService
from app.services.postsales_service import PostSalesService
from app.services.recovery_service import RecoveryService

apply_branding("Modo TV Comercial")
ensure_demo_data_once()

hoje = date.today()
inicio = hoje - timedelta(days=89)
with session_scope() as session:
    pv = PostSalesService(session).summary(inicio, hoje)["atual"]
    pv_mes = [m for m in PostSalesService(session).monthly(hoje - timedelta(days=364), hoje) if m["respondidas"] >= 8]
    fila_pv = PostSalesService(session).detractor_queue(hoje, hoje - timedelta(days=364), hoje)
    ent = DeliveryService(session).summary(inicio, hoje, hoje)["atual"]
    ent_mes = DeliveryService(session).monthly(hoje - timedelta(days=364), hoje, hoje)
    atrasados = DeliveryService(session).open_late(hoje)
    rec_service = RecoveryService(session)
    rec = rec_service.summary(hoje - timedelta(days=179), hoje)["atual"]
    faixas = rec_service.bands(hoje)
    bonus = BonusService(session).summary(hoje.year)


def _mi(v: float) -> str:
    return f"R$ {v / 1_000_000:,.1f} mi".replace(",", "X").replace(".", ",").replace("X", ".")


def slide_satisfacao() -> None:
    tv.titulo("Satisfação dos clientes", "Últimos 90 dias · pesquisa depois da entrega")
    zona = postsales_rules.nps_zone(pv["nps"])
    tom = "ok" if zona in ("excelencia", "qualidade") else "atencao"
    tv.linha([
        tv.card("NPS", "—" if pv["nps"] is None else f"{pv['nps']:+.0f}", f"Meta ≥ {postsales_rules.NPS_TARGET}", tom),
        tv.card("Satisfação (CSAT)", f"{(pv['csat'] or 0):.0f}%", f"Meta ≥ {postsales_rules.CSAT_TARGET:.0f}%",
                "ok" if (pv["csat"] or 0) >= postsales_rules.CSAT_TARGET else "atencao"),
        tv.card("Detratores a recontatar", str(len(fila_pv)), "Retorno em até 2 dias",
                "ruim" if any(r["prazo"] == "vencido" for r in fila_pv) else "ok"),
    ])
    if len(pv_mes) >= 2:
        charts.render(charts.line_with_target([m["mes"] for m in pv_mes], [m["nps"] for m in pv_mes],
                                              postsales_rules.NPS_TARGET, "Meta", suffix=""))


def slide_entregas() -> None:
    tv.titulo("Entregas no prazo", "Últimos 90 dias · pedidos com prazo vencido")
    ok = (ent["otd"] or 0) >= delivery_rules.OTD_TARGET
    tv.linha([
        tv.card("OTD", f"{(ent['otd'] or 0):.1f}%".replace(".", ","), f"Meta ≥ {delivery_rules.OTD_TARGET:.0f}%",
                "ok" if ok else "atencao"),
        tv.card("Pedidos atrasados em aberto", str(len(atrasados)), "Prazo vencido, ainda não entregues",
                "ruim" if atrasados else "ok"),
        tv.card("Atraso médio", f"{ent['atraso_medio']:.1f} dias".replace(".", ","), "Só entre os atrasados", "info"),
    ])
    com = [m for m in ent_mes if m[1] is not None]
    if len(com) >= 2:
        charts.render(charts.line_with_target([m for m, _ in com], [v for _, v in com],
                                              delivery_rules.OTD_TARGET, "Meta"))


def slide_recuperacao() -> None:
    tv.titulo("Clientes de volta", "Últimos 6 meses · recuperação de quem parou de comprar")
    ok = (rec["taxa"] or 0) >= recovery_rules.REACTIVATION_TARGET
    tv.linha([
        tv.card("Taxa de reativação", f"{(rec['taxa'] or 0):.1f}%".replace(".", ","),
                f"{rec['reativados']} de {rec['contatados']} contatados", "ok" if ok else "atencao"),
        tv.card("Receita recuperada", _mi(rec["recuperado"]), "Pedidos até 60 dias após o contato", "ok"),
        tv.card("Clientes em risco + inativos", str(faixas["clientes"]["em_risco"] + faixas["clientes"]["inativo"]),
                "Sem comprar há mais de 90 dias", "atencao"),
    ])


def slide_distribuidores() -> None:
    tv.titulo("Distribuidores", f"Bônus de {hoje.year} · apurado ao vivo")
    tv.linha([
        tv.card("Bônus apurado", _mi(bonus["bonus"]), f"{bonus['distribuidores']} distribuidores", "ok"),
        tv.card("Compras no ano", _mi(bonus["compras"]), "Pedidos faturados", "info"),
        tv.card("Perto da próxima faixa", str(bonus["perto_da_proxima"]),
                f"Faixas de {bonus_rules.TIERS[1][1]:.0f}% a {bonus_rules.TIERS[-1][1]:.0f}%", "atencao"),
    ])


tv.rotacionar([slide_satisfacao, slide_entregas, slide_recuperacao, slide_distribuidores], intervalo=10)
st.caption("Troca de tela automática a cada 10 segundos. Dados fictícios.")
