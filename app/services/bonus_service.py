"""Bônus dos Distribuidores — compra acumulada no ano, faixa e bônus apurado."""
from __future__ import annotations

from collections import defaultdict
from datetime import date

from sqlalchemy.orm import Session

from app.core.metrics import track
from app.domain import bonus_rules as rules
from app.repositories.bonus_repository import BonusRepository


class BonusService:
    def __init__(self, session: Session):
        self.session = session
        self.repo = BonusRepository(session)

    @track("bonus.ranking")
    def ranking(self, year: int) -> list[dict]:
        """Um distribuidor por linha, do maior comprador para o menor."""
        acumulado: dict[int, dict] = {}
        for o in self.repo.distributor_orders(date(year, 1, 1), date(year, 12, 31)):
            item = acumulado.setdefault(o["cliente_id"], {"nome": o["nome"], "uf": o["uf"], "compras": 0.0})
            item["compras"] += o["valor"]
        linhas = []
        for item in acumulado.values():
            compras = round(item["compras"], 2)
            faltam = rules.next_tier_gap(compras)
            linhas.append({
                **item, "compras": compras,
                "faixa": rules.tier_index(compras), "pct": rules.bonus_pct(compras),
                "bonus": rules.bonus_value(compras),
                "faltam": faltam[0] if faltam else None,
                "prox_pct": faltam[1] if faltam else None,
                "avanco": rules.progress_to_next(compras),
            })
        linhas.sort(key=lambda x: x["compras"], reverse=True)
        return linhas

    @track("bonus.summary")
    def summary(self, year: int) -> dict:
        r = self.ranking(year)
        perto = [x for x in r if x["faltam"] is not None and x["avanco"] >= 75]
        return {
            "distribuidores": len(r),
            "compras": round(sum(x["compras"] for x in r), 2),
            "bonus": round(sum(x["bonus"] for x in r), 2),
            "na_ultima_faixa": sum(1 for x in r if x["faltam"] is None),
            "perto_da_proxima": len(perto),
        }

    @track("bonus.by_tier")
    def by_tier(self, year: int) -> list[tuple[int, int]]:
        contagem: dict[int, int] = defaultdict(int)
        for x in self.ranking(year):
            contagem[x["faixa"]] += 1
        return [(i, contagem.get(i, 0)) for i in range(len(rules.TIERS))]

    @track("bonus.monthly")
    def monthly(self, year: int) -> list[tuple[str, float]]:
        por_mes: dict[str, float] = defaultdict(float)
        for o in self.repo.distributor_orders(date(year, 1, 1), date(year, 12, 31)):
            por_mes[o["data"].strftime("%Y-%m")] += o["valor"]
        return sorted((m, round(v, 2)) for m, v in por_mes.items())
