"""Pure business rules for Prazo de Entrega — no database, no I/O.

Indicador de mercado OTD (on-time delivery): pedidos entregues até a data
prometida ÷ pedidos cujo prazo já venceu.
"""
from __future__ import annotations

from datetime import date

OTD_TARGET = 95.0   # % entregue no prazo


def delay_days(promised: date, delivered: date | None, today: date) -> int:
    """Dias de atraso (0 se no prazo). Pedido não entregue conta até hoje."""
    ref = delivered or today
    return max((ref - promised).days, 0)


def is_due(promised: date, delivered: date | None, today: date) -> bool:
    """O prazo entra na conta se já foi entregue ou se a data prometida passou."""
    return delivered is not None or promised < today


def delay_band(days: int) -> str:
    """``no_prazo`` · ``leve`` (1–3) · ``medio`` (4–7) · ``grave`` (8+)."""
    if days <= 0:
        return "no_prazo"
    if days <= 3:
        return "leve"
    if days <= 7:
        return "medio"
    return "grave"


def otd_rate(on_time: int, due: int) -> float | None:
    if not due:
        return None
    return round(100 * on_time / due, 1)
