"""Data access for Relacionamento com Leads."""
from __future__ import annotations

from datetime import date

from sqlalchemy import func, select

from app.database.models.leads import Lead, LeadStatus
from app.database.models.people import Employee
from app.repositories.base import BaseRepository

# Leads descartados saem da fila: não adianta cobrar contato de quem já morreu.
_EM_JOGO = (LeadStatus.NOVO, LeadStatus.EM_CONTATO, LeadStatus.QUALIFICADO)


class LeadRepository(BaseRepository[Lead]):
    model = Lead

    def queue(self, today: date) -> list[dict]:
        """Fila de contato: um lead por linha, com há quantos dias ninguém encosta."""
        stmt = (
            select(Lead, Employee.full_name)
            .join(Employee, Employee.id == Lead.owner_employee_id, isouter=True)
            .where(Lead.status.in_(_EM_JOGO))
        )
        fila = []
        for lead, responsavel in self.session.execute(stmt).all():
            referencia = lead.last_contact_date or lead.created_date
            fila.append(
                {
                    "empresa": lead.company_name,
                    "contato": lead.contact_name,
                    "cidade": lead.city,
                    "estado": lead.state,
                    "segmento": lead.segment,
                    "origem": lead.origin.value,
                    "status": lead.status.value,
                    "responsavel": responsavel or "sem dono",
                    "entrada": lead.created_date,
                    "ultimo_contato": lead.last_contact_date,
                    "dias_sem_contato": (today - referencia).days,
                    "valor_potencial": float(lead.potential_value or 0),
                }
            )
        fila.sort(key=lambda item: item["dias_sem_contato"], reverse=True)
        return fila

    def by_origin(self) -> list[tuple[str, int]]:
        stmt = (
            select(Lead.origin, func.count(Lead.id))
            .group_by(Lead.origin)
            .order_by(func.count(Lead.id).desc())
        )
        return [(origem.value, int(total)) for origem, total in self.session.execute(stmt).all()]

    def by_status(self) -> list[tuple[str, int]]:
        stmt = (
            select(Lead.status, func.count(Lead.id))
            .group_by(Lead.status)
            .order_by(func.count(Lead.id).desc())
        )
        return [(status.value, int(total)) for status, total in self.session.execute(stmt).all()]

    def monthly_intake(self) -> list[tuple[str, int]]:
        mes = func.strftime("%Y-%m", Lead.created_date).label("mes")
        stmt = select(mes, func.count(Lead.id)).group_by(mes).order_by(mes)
        return [(str(m), int(total)) for m, total in self.session.execute(stmt).all()]
