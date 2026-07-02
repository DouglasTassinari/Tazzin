"""Data access for the Administration module."""
from __future__ import annotations

from sqlalchemy import select

from app.database.models.administration import AuditLog, Role, User
from app.repositories.base import BaseRepository


class RoleRepository(BaseRepository[Role]):
    model = Role

    def find_by_code(self, code: str) -> Role | None:
        stmt = select(Role).where(Role.code == code)
        return self.session.execute(stmt).scalar_one_or_none()


class UserRepository(BaseRepository[User]):
    model = User

    def find_by_username(self, username: str) -> User | None:
        stmt = select(User).where(User.username == username)
        return self.session.execute(stmt).scalar_one_or_none()

    def active_users(self) -> list[User]:
        stmt = select(User).where(User.is_active.is_(True))
        return list(self.session.execute(stmt).scalars().all())


class AuditLogRepository(BaseRepository[AuditLog]):
    model = AuditLog

    def recent(self, limit: int = 20) -> list[AuditLog]:
        stmt = select(AuditLog).order_by(AuditLog.occurred_at.desc()).limit(limit)
        return list(self.session.execute(stmt).scalars().all())

    def by_entity(self, entity_name: str, entity_id: int) -> list[AuditLog]:
        stmt = select(AuditLog).where(
            AuditLog.entity_name == entity_name, AuditLog.entity_id == entity_id
        )
        return list(self.session.execute(stmt).scalars().all())
