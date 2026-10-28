"""Recuperação de Clientes — quem esfriou, quem foi abordado e quanto voltou."""
from __future__ import annotations

from collections import defaultdict
from datetime import date, timedelta

from sqlalchemy.orm import Session

from app.core.metrics import track
from app.domain import recovery_rules as rules
from app.repositories.recovery_repository import RecoveryRepository


class RecoveryService:
    def __init__(self, session: Session):
        self.session = session
        self.repo = RecoveryRepository(session)

    def _portfolio(self, today: date) -> list[dict]:
        """Carteira com recência: última compra, dias parado e valor de referência.

        Valor de referência = quanto o cliente comprou nos 12 meses até a última
        compra: mede o tamanho do que está parado, não do que sobrou.
        """
        compras: dict[int, list[dict]] = defaultdict(list)
        for p in self.repo.purchases():
            compras[p["cliente_id"]].append(p)
        clientes = self.repo.customers()
        ultimos = self.repo.last_contacts()
        carteira = []
        for cid, lista in compras.items():
            ultima = max(p["data"] for p in lista)
            ref = sum(p["valor"] for p in lista if (ultima - p["data"]).days <= 365)
            dias = (today - ultima).days
            carteira.append({
                "cliente_id": cid, **clientes[cid], "ultima_compra": ultima, "dias": dias,
                "faixa": rules.recency_band(dias), "valor_ref": round(ref, 2),
                "ultimo_contato": ultimos.get(cid),
            })
        return carteira

    @track("recovery.bands")
    def bands(self, today: date) -> dict:
        carteira = self._portfolio(today)
        contagem = {f: 0 for f in ("ativo", "em_risco", "inativo", "perdido")}
        valor = {f: 0.0 for f in contagem}
        for c in carteira:
            contagem[c["faixa"]] += 1
            valor[c["faixa"]] += c["valor_ref"]
        return {"clientes": contagem, "valor_ref": valor, "total": len(carteira)}

    @track("recovery.queue")
    def queue(self, today: date, faixas: tuple[str, ...] = ("inativo", "em_risco")) -> list[dict]:
        """Quem abordar: clientes nas faixas pedidas, do maior valor para o menor."""
        fila = [c for c in self._portfolio(today) if c["faixa"] in faixas]
        fila.sort(key=lambda c: c["valor_ref"], reverse=True)
        total = max(len(fila), 1)
        for i, c in enumerate(fila):
            c["prioridade"] = rules.priority(i / total)
        return fila

    @track("recovery.summary")
    def summary(self, start: date, end: date) -> dict:
        span = (end - start) + timedelta(days=1)
        return {
            "atual": self._results(self.repo.contacts(start, end)),
            "anterior": self._results(self.repo.contacts(start - span, start - timedelta(days=1))),
        }

    @staticmethod
    def _results(contatos: list[dict]) -> dict:
        reativados = [c for c in contatos if c["resultado"] == "reactivated"]
        return {
            "contatados": len(contatos),
            "reativados": len(reativados),
            "taxa": rules.reactivation_rate(len(reativados), len(contatos)),
            "recuperado": round(sum(c["recuperado"] for c in reativados), 2),
        }

    @track("recovery.by_channel")
    def by_channel(self, start: date, end: date) -> list[dict]:
        por_canal: dict[str, list[dict]] = defaultdict(list)
        for c in self.repo.contacts(start, end):
            por_canal[c["canal"]].append(c)
        return [{"canal": canal, **self._results(lista)} for canal, lista in por_canal.items()]

    @track("recovery.monthly")
    def monthly(self, start: date, end: date) -> list[tuple[str, float]]:
        por_mes: dict[str, float] = defaultdict(float)
        for c in self.repo.contacts(start, end):
            if c["resultado"] == "reactivated":
                por_mes[c["data"].strftime("%Y-%m")] += c["recuperado"]
        return sorted(por_mes.items())

    @track("recovery.results")
    def result_mix(self, start: date, end: date) -> dict[str, int]:
        mix: dict[str, int] = defaultdict(int)
        for c in self.repo.contacts(start, end):
            mix[c["resultado"]] += 1
        return dict(mix)

    @track("recovery.recent")
    def recent_wins(self, start: date, end: date, limit: int = 8) -> list[dict]:
        ganhos = [c for c in self.repo.contacts(start, end) if c["resultado"] == "reactivated"]
        ganhos.sort(key=lambda c: c["data"], reverse=True)
        return ganhos[:limit]
