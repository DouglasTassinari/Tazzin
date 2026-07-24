"""Data access for Descoberta de Mercado (base pública de empresas)."""
from __future__ import annotations

from sqlalchemy import func, select

from app.database.models.market import CompanyStatus, MarketCompany
from app.repositories.base import BaseRepository


class MarketCompanyRepository(BaseRepository[MarketCompany]):
    model = MarketCompany

    # -- filtros compartilhados por todas as agregações ---------------------- #
    @staticmethod
    def _conditions(
        states: list[str] | None,
        cnaes: list[str] | None,
        sizes: list[str] | None,
        active_only: bool,
    ) -> list:
        conditions = []
        if states:
            conditions.append(MarketCompany.state.in_(states))
        if cnaes:
            conditions.append(MarketCompany.cnae_code.in_(cnaes))
        if sizes:
            conditions.append(MarketCompany.size.in_(sizes))
        if active_only:
            conditions.append(MarketCompany.status == CompanyStatus.ATIVA)
        return conditions

    def distinct_states(self) -> list[str]:
        stmt = select(MarketCompany.state).distinct().order_by(MarketCompany.state)
        return [uf for (uf,) in self.session.execute(stmt).all()]

    def distinct_cnaes(self) -> list[tuple[str, str]]:
        stmt = (
            select(MarketCompany.cnae_code, MarketCompany.cnae_label)
            .distinct()
            .order_by(MarketCompany.cnae_label)
        )
        return [(codigo, rotulo) for codigo, rotulo in self.session.execute(stmt).all()]

    def summary(self, states, cnaes, sizes, active_only) -> dict:
        conditions = self._conditions(states, cnaes, sizes, active_only)
        stmt = select(
            func.count(MarketCompany.id),
            func.avg(MarketCompany.share_capital),
        ).where(*conditions)
        total, capital_medio = self.session.execute(stmt).one()

        ativas_stmt = (
            select(func.count(MarketCompany.id))
            .where(*conditions)
            .where(MarketCompany.status == CompanyStatus.ATIVA)
        )
        ativas = self.session.execute(ativas_stmt).scalar_one()
        return {
            "total": int(total or 0),
            "ativas": int(ativas or 0),
            "capital_medio": float(capital_medio or 0),
        }

    def _group_count(self, coluna, states, cnaes, sizes, active_only, limit=None):
        stmt = (
            select(coluna, func.count(MarketCompany.id).label("total"))
            .where(*self._conditions(states, cnaes, sizes, active_only))
            .group_by(coluna)
            .order_by(func.count(MarketCompany.id).desc())
        )
        if limit:
            stmt = stmt.limit(limit)
        return self.session.execute(stmt).all()

    def by_state(self, states, cnaes, sizes, active_only, limit=12) -> list[tuple[str, int]]:
        rows = self._group_count(MarketCompany.state, states, cnaes, sizes, active_only, limit)
        return [(uf, int(total)) for uf, total in rows]

    def by_cnae(self, states, cnaes, sizes, active_only, limit=10) -> list[tuple[str, int]]:
        rows = self._group_count(MarketCompany.cnae_label, states, cnaes, sizes, active_only, limit)
        return [(rotulo, int(total)) for rotulo, total in rows]

    def by_size(self, states, cnaes, sizes, active_only) -> list[tuple[str, int]]:
        rows = self._group_count(MarketCompany.size, states, cnaes, sizes, active_only)
        return [(porte.value, int(total)) for porte, total in rows]

    def openings_by_year(self, states, cnaes, sizes, active_only) -> list[tuple[str, int]]:
        ano = func.strftime("%Y", MarketCompany.opening_date).label("ano")
        stmt = (
            select(ano, func.count(MarketCompany.id))
            .where(*self._conditions(states, cnaes, sizes, active_only))
            .group_by(ano)
            .order_by(ano)
        )
        return [(str(a), int(total)) for a, total in self.session.execute(stmt).all()]

    def sample(self, states, cnaes, sizes, active_only, limit=300) -> list[MarketCompany]:
        stmt = (
            select(MarketCompany)
            .where(*self._conditions(states, cnaes, sizes, active_only))
            .order_by(MarketCompany.share_capital.desc())
            .limit(limit)
        )
        return list(self.session.execute(stmt).scalars().all())
