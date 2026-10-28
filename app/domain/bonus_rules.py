"""Pure business rules for Bônus dos Distribuidores — no database, no I/O.

Rebate progressivo por faixa de compra anual, prática comum em distribuição:
quanto mais o distribuidor compra no ano, maior o percentual devolvido sobre
o total comprado. Faixas e percentuais de demonstração.
"""
from __future__ import annotations

# (compra anual mínima em R$, % de bônus sobre o total comprado)
TIERS: list[tuple[float, float]] = [
    (0.0, 0.0),
    (150_000.0, 3.0),
    (300_000.0, 5.0),
    (450_000.0, 8.0),
    (600_000.0, 10.0),
]


def tier_index(purchases: float) -> int:
    """Índice da faixa atingida (0 = abaixo da primeira faixa de bônus)."""
    idx = 0
    for i, (minimo, _) in enumerate(TIERS):
        if purchases >= minimo:
            idx = i
    return idx


def bonus_pct(purchases: float) -> float:
    return TIERS[tier_index(purchases)][1]


def bonus_value(purchases: float) -> float:
    return round(purchases * bonus_pct(purchases) / 100, 2)


def next_tier_gap(purchases: float) -> tuple[float, float] | None:
    """(quanto falta comprar, % da próxima faixa) ou ``None`` se já está na última."""
    idx = tier_index(purchases)
    if idx >= len(TIERS) - 1:
        return None
    minimo, pct = TIERS[idx + 1]
    return round(minimo - purchases, 2), pct


def progress_to_next(purchases: float) -> float:
    """Avanço (0–100) dentro da faixa atual rumo à próxima; 100 na última faixa."""
    idx = tier_index(purchases)
    if idx >= len(TIERS) - 1:
        return 100.0
    base, topo = TIERS[idx][0], TIERS[idx + 1][0]
    return round(100 * (purchases - base) / (topo - base), 1)
