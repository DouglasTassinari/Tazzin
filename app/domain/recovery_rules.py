"""Pure business rules for Recuperação de Clientes — no database, no I/O.

Régua de recência usual de carteira: quanto mais tempo sem comprar, menor a
chance de voltar. A reativação conta quando há compra até 60 dias depois do contato.
"""
from __future__ import annotations

AT_RISK_DAYS = 90        # passou do ciclo normal de compra
DORMANT_DAYS = 180       # esfriou: hora de abordar
LOST_DAYS = 365          # um ano parado: tratar como perdido
CONVERSION_WINDOW_DAYS = 60
REACTIVATION_TARGET = 15.0   # % dos contatados que voltam a comprar


def recency_band(days_since_purchase: int) -> str:
    """``ativo`` · ``em_risco`` · ``inativo`` · ``perdido``."""
    if days_since_purchase > LOST_DAYS:
        return "perdido"
    if days_since_purchase > DORMANT_DAYS:
        return "inativo"
    if days_since_purchase > AT_RISK_DAYS:
        return "em_risco"
    return "ativo"


def reactivation_rate(reactivated: int, contacted: int) -> float | None:
    if not contacted:
        return None
    return round(100 * reactivated / contacted, 1)


def priority(rank_pct: float) -> str:
    """Prioridade pela posição no ranking de valor (0 = maior cliente): ``alta`` · ``media`` · ``baixa``."""
    if rank_pct <= 0.25:
        return "alta"
    if rank_pct <= 0.60:
        return "media"
    return "baixa"
