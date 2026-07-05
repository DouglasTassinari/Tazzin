"""Number/currency formatting helpers using Brazilian conventions (pt-BR)."""
from __future__ import annotations


def format_brl(value: float | int | None) -> str:
    """Format a number as Brazilian Real: ``R$ 1.234.567,00``."""
    value = value or 0
    formatted = f"{value:,.2f}".replace(",", "|").replace(".", ",").replace("|", ".")
    return f"R$ {formatted}"
