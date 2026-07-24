"""Relacionamento com Leads — fila de contato de quem ainda não comprou."""
from __future__ import annotations

from datetime import date

from sqlalchemy.orm import Session

from app.core.metrics import track
from app.domain import leads_rules
from app.repositories.leads_repository import LeadRepository


class LeadsService:
    def __init__(self, session: Session):
        self.session = session
        self.leads = LeadRepository(session)

    @track("leads.queue")
    def queue(self, today: date) -> list[dict]:
        """Fila ordenada pelo mais abandonado, já com o farol de cada lead."""
        fila = self.leads.queue(today)
        for item in fila:
            item["farol"] = leads_rules.contact_band(item["dias_sem_contato"])
        return fila

    @track("leads.summary")
    def summary(self, today: date) -> dict:
        fila = self.queue(today)
        vencidos = [item for item in fila if item["farol"] == "vencido"]
        qualificados = [item for item in fila if item["status"] == "qualificado"]
        return {
            "total": len(fila),
            "vencidos": len(vencidos),
            "qualificados": len(qualificados),
            "valor_potencial": sum(item["valor_potencial"] for item in fila),
        }

    @track("leads.distribution")
    def distribution(self) -> dict:
        return {
            "por_origem": self.leads.by_origin(),
            "por_status": self.leads.by_status(),
            "entrada_mensal": self.leads.monthly_intake(),
        }
