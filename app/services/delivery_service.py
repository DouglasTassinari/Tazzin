"""Prazo de Entrega — OTD, atrasos e pedidos ainda em aberto."""
from __future__ import annotations

from collections import defaultdict
from datetime import date, timedelta

from sqlalchemy.orm import Session

from app.core.metrics import track
from app.domain import delivery_rules as rules
from app.repositories.delivery_repository import DeliveryRepository


class DeliveryService:
    def __init__(self, session: Session):
        self.session = session
        self.repo = DeliveryRepository(session)

    def _due(self, start: date, end: date, today: date) -> list[dict]:
        linhas = []
        for r in self.repo.rows(start, end):
            if not rules.is_due(r["prometida"], r["entregue"], today):
                continue
            dias = rules.delay_days(r["prometida"], r["entregue"], today)
            linhas.append({**r, "atraso": dias, "faixa": rules.delay_band(dias)})
        return linhas

    @staticmethod
    def _otd(linhas: list[dict]) -> dict:
        no_prazo = sum(1 for r in linhas if r["atraso"] == 0)
        atrasados = [r["atraso"] for r in linhas if r["atraso"] > 0]
        return {
            "total": len(linhas), "no_prazo": no_prazo, "atrasados": len(atrasados),
            "otd": rules.otd_rate(no_prazo, len(linhas)),
            "atraso_medio": round(sum(atrasados) / len(atrasados), 1) if atrasados else 0.0,
        }

    @track("delivery.summary")
    def summary(self, start: date, end: date, today: date) -> dict:
        span = (end - start) + timedelta(days=1)
        return {
            "atual": self._otd(self._due(start, end, today)),
            "anterior": self._otd(self._due(start - span, start - timedelta(days=1), today)),
        }

    @track("delivery.monthly")
    def monthly(self, start: date, end: date, today: date) -> list[tuple[str, float]]:
        por_mes: dict[str, list[dict]] = defaultdict(list)
        for r in self._due(start, end, today):
            por_mes[r["prometida"].strftime("%Y-%m")].append(r)
        return [(m, self._otd(rs)["otd"]) for m, rs in sorted(por_mes.items())]

    @track("delivery.by_segment")
    def by_segment(self, start: date, end: date, today: date) -> list[dict]:
        por_seg: dict[str, list[dict]] = defaultdict(list)
        for r in self._due(start, end, today):
            por_seg[r["segmento"]].append(r)
        return [{"segmento": s, **self._otd(rs)} for s, rs in por_seg.items()]

    @track("delivery.delay_mix")
    def delay_mix(self, start: date, end: date, today: date) -> dict[str, int]:
        mix: dict[str, int] = defaultdict(int)
        for r in self._due(start, end, today):
            mix[r["faixa"]] += 1
        return dict(mix)

    @track("delivery.open_late")
    def open_late(self, today: date) -> list[dict]:
        """Pedidos que ainda não chegaram e já passaram da data prometida."""
        abertos = [r for r in self.repo.rows(today - timedelta(days=120), today - timedelta(days=1))
                   if r["entregue"] is None]
        for r in abertos:
            r["atraso"] = rules.delay_days(r["prometida"], None, today)
            r["faixa"] = rules.delay_band(r["atraso"])
        abertos.sort(key=lambda r: r["atraso"], reverse=True)
        return abertos

    @track("delivery.worst_customers")
    def worst_customers(self, start: date, end: date, today: date, limit: int = 8) -> list[dict]:
        por_cli: dict[str, list[dict]] = defaultdict(list)
        for r in self._due(start, end, today):
            por_cli[r["cliente"]].append(r)
        linhas = [{"cliente": c, **self._otd(rs)} for c, rs in por_cli.items() if len(rs) >= 4]
        linhas.sort(key=lambda x: (x["otd"], -x["total"]))
        return linhas[:limit]
