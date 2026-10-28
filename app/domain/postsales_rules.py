"""Pure business rules for Pós-Vendas — no database, no I/O.

Régua de mercado: NPS (promotores 9–10, neutros 7–8, detratores 0–6), CSAT como
percentual de notas 4 e 5, e taxa de resposta da pesquisa.
"""
from __future__ import annotations

PROMOTER_MIN = 9
NEUTRAL_MIN = 7

NPS_TARGET = 50          # zona de qualidade
CSAT_TARGET = 85.0       # % de notas 4 e 5
RESPONSE_TARGET = 30.0   # % de pesquisas respondidas

# Detrator pede retorno rápido: em até dois dias a conversa ainda é sobre o
# problema; depois de uma semana já virou desistência.
FOLLOWUP_WARN_DAYS = 2
FOLLOWUP_LATE_DAYS = 7


def classify(score: int) -> str:
    """``promotor`` · ``neutro`` · ``detrator``."""
    if score >= PROMOTER_MIN:
        return "promotor"
    if score >= NEUTRAL_MIN:
        return "neutro"
    return "detrator"


def nps(scores: list[int]) -> float | None:
    """% de promotores menos % de detratores (de -100 a +100)."""
    if not scores:
        return None
    promoters = sum(1 for s in scores if classify(s) == "promotor")
    detractors = sum(1 for s in scores if classify(s) == "detrator")
    return round(100 * (promoters - detractors) / len(scores), 1)


def csat_pct(scores: list[int]) -> float | None:
    """% de respostas com nota 4 ou 5 (escala de 1 a 5)."""
    if not scores:
        return None
    return round(100 * sum(1 for s in scores if s >= 4) / len(scores), 1)


def response_rate(responded: int, sent: int) -> float | None:
    if not sent:
        return None
    return round(100 * responded / sent, 1)


def nps_zone(value: float | None) -> str:
    """Zonas usuais do NPS: ``excelencia`` ≥ 75 · ``qualidade`` ≥ 50 · ``aperfeicoamento`` ≥ 0 · ``critica``."""
    if value is None:
        return "sem_dados"
    if value >= 75:
        return "excelencia"
    if value >= NPS_TARGET:
        return "qualidade"
    if value >= 0:
        return "aperfeicoamento"
    return "critica"


def followup_band(days_waiting: int) -> str:
    """Prazo do retorno ao detrator: ``ok`` · ``atencao`` · ``vencido``."""
    if days_waiting > FOLLOWUP_LATE_DAYS:
        return "vencido"
    if days_waiting > FOLLOWUP_WARN_DAYS:
        return "atencao"
    return "ok"
