"""Data access for Pós-Vendas."""
from __future__ import annotations

from datetime import date

from sqlalchemy import select

from app.database.models.people import Employee
from app.database.models.postsales import PostSaleSurvey
from app.database.models.sales import Customer
from app.repositories.base import BaseRepository


class PostSaleSurveyRepository(BaseRepository[PostSaleSurvey]):
    model = PostSaleSurvey

    def rows(self, start: date, end: date) -> list[dict]:
        """Pesquisas enviadas na janela, uma por linha, já com cliente e responsável."""
        stmt = (
            select(PostSaleSurvey, Customer.name, Customer.segment, Employee.full_name)
            .join(Customer, Customer.id == PostSaleSurvey.customer_id)
            .join(Employee, Employee.id == PostSaleSurvey.owner_employee_id, isouter=True)
            .where(PostSaleSurvey.sent_date.between(start, end))
        )
        return [
            {
                "enviada": s.sent_date,
                "respondida": s.responded_date,
                "nps": s.nps_score,
                "csat": s.csat_score,
                "comentario": s.comment,
                "retorno": s.follow_up.value,
                "cliente": cliente,
                "segmento": segmento.value,
                "responsavel": responsavel or "sem dono",
            }
            for s, cliente, segmento, responsavel in self.session.execute(stmt).all()
        ]
