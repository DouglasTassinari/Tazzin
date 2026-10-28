"""Pós-Vendas — NPS, satisfação, resposta da pesquisa e fila de retorno."""
from __future__ import annotations

from collections import defaultdict
from datetime import date, timedelta

from sqlalchemy.orm import Session

from app.core.metrics import track
from app.domain import postsales_rules as rules
from app.repositories.postsales_repository import PostSaleSurveyRepository


def _indicators(rows: list[dict]) -> dict:
    answered = [r for r in rows if r["nps"] is not None]
    scores = [r["nps"] for r in answered]
    classes = [rules.classify(s) for s in scores]
    return {
        "enviadas": len(rows),
        "respondidas": len(answered),
        "taxa_resposta": rules.response_rate(len(answered), len(rows)),
        "nps": rules.nps(scores),
        "csat": rules.csat_pct([r["csat"] for r in answered if r["csat"] is not None]),
        "promotores": classes.count("promotor"),
        "neutros": classes.count("neutro"),
        "detratores": classes.count("detrator"),
    }


class PostSalesService:
    def __init__(self, session: Session):
        self.session = session
        self.surveys = PostSaleSurveyRepository(session)

    @track("postsales.summary")
    def summary(self, start: date, end: date) -> dict:
        """Indicadores do período e o mesmo recorte do período anterior (para variação)."""
        span = (end - start) + timedelta(days=1)
        atual = _indicators(self.surveys.rows(start, end))
        anterior = _indicators(self.surveys.rows(start - span, start - timedelta(days=1)))
        return {"atual": atual, "anterior": anterior}

    @track("postsales.monthly")
    def monthly(self, start: date, end: date) -> list[dict]:
        por_mes: dict[str, list[dict]] = defaultdict(list)
        for row in self.surveys.rows(start, end):
            por_mes[row["enviada"].strftime("%Y-%m")].append(row)
        return [{"mes": mes, **_indicators(rows)} for mes, rows in sorted(por_mes.items())]

    @track("postsales.by_segment")
    def by_segment(self, start: date, end: date) -> list[dict]:
        por_seg: dict[str, list[dict]] = defaultdict(list)
        for row in self.surveys.rows(start, end):
            por_seg[row["segmento"]].append(row)
        return [{"segmento": seg, **_indicators(rows)} for seg, rows in por_seg.items()]

    @track("postsales.score_distribution")
    def score_distribution(self, start: date, end: date) -> list[tuple[int, int]]:
        contagem = {n: 0 for n in range(11)}
        for row in self.surveys.rows(start, end):
            if row["nps"] is not None:
                contagem[row["nps"]] += 1
        return sorted(contagem.items())

    @track("postsales.detractor_queue")
    def detractor_queue(self, today: date, start: date, end: date) -> list[dict]:
        """Detratores sem retorno concluído, do mais antigo para o mais novo."""
        fila = []
        for row in self.surveys.rows(start, end):
            if row["nps"] is None or rules.classify(row["nps"]) != "detrator":
                continue
            if row["retorno"] == "resolved":
                continue
            dias = (today - row["respondida"]).days
            fila.append({**row, "dias": dias, "prazo": rules.followup_band(dias)})
        fila.sort(key=lambda r: r["dias"], reverse=True)
        return fila

    @track("postsales.comments")
    def comments(self, start: date, end: date, limit: int = 8) -> list[dict]:
        com = [r for r in self.surveys.rows(start, end) if r["comentario"] and r["nps"] is not None]
        com.sort(key=lambda r: r["respondida"], reverse=True)
        return com[:limit]
