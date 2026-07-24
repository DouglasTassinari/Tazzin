"""Pure business rules for Relacionamento com Leads — no database, no I/O."""
from __future__ import annotations

# Lead esfria rápido: quem entrou e não é procurado na primeira semana já
# perde tração. Passou de duas semanas sem contato, virou fila de resgate.
LEAD_WARN_DAYS = 7
LEAD_LATE_DAYS = 15


def contact_band(dias_sem_contato: int) -> str:
    """Farol da fila: ``ok`` · ``atencao`` · ``vencido``."""
    if dias_sem_contato > LEAD_LATE_DAYS:
        return "vencido"
    if dias_sem_contato > LEAD_WARN_DAYS:
        return "atencao"
    return "ok"
