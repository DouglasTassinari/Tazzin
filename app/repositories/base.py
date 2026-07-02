"""Generic repository providing CRUD + filtering for any ORM model.

Module-specific repositories subclass :class:`BaseRepository` and add
only the domain-specific queries (aggregations, joins, KPI lookups),
keeping the boilerplate CRUD code in exactly one place.
"""
from __future__ import annotations

from typing import Generic, Sequence, Type, TypeVar

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exceptions import EntityNotFoundError
from app.core.logging import get_logger

ModelT = TypeVar("ModelT")

logger = get_logger("repository")


class BaseRepository(Generic[ModelT]):
    """CRUD operations shared by every repository in the platform."""

    model: Type[ModelT]

    def __init__(self, session: Session):
        self.session = session

    def get(self, entity_id: int) -> ModelT:
        entity = self.session.get(self.model, entity_id)
        if entity is None:
            raise EntityNotFoundError(self.model.__name__, entity_id)
        return entity

    def get_or_none(self, entity_id: int) -> ModelT | None:
        return self.session.get(self.model, entity_id)

    def list(self, limit: int | None = None, offset: int = 0) -> Sequence[ModelT]:
        stmt = select(self.model).offset(offset)
        if limit is not None:
            stmt = stmt.limit(limit)
        return self.session.execute(stmt).scalars().all()

    def add(self, entity: ModelT) -> ModelT:
        self.session.add(entity)
        self.session.flush()
        return entity

    def add_many(self, entities: Sequence[ModelT]) -> Sequence[ModelT]:
        self.session.add_all(entities)
        self.session.flush()
        return entities

    def delete(self, entity: ModelT) -> None:
        self.session.delete(entity)
        self.session.flush()

    def count(self) -> int:
        from sqlalchemy import func

        stmt = select(func.count()).select_from(self.model)
        return self.session.execute(stmt).scalar_one()
