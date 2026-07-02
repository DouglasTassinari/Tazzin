"""Administration module schema: Role, User, AuditLog."""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base
from app.database.models.core import TimestampMixin


class Role(TimestampMixin, Base):
    __tablename__ = "admin_roles"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(80))
    description: Mapped[str] = mapped_column(String(300), default="")


class User(TimestampMixin, Base):
    __tablename__ = "admin_users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    email: Mapped[str] = mapped_column(String(150), unique=True, index=True)
    employee_id: Mapped[int | None] = mapped_column(
        ForeignKey("people_employees.id"), nullable=True
    )
    role_id: Mapped[int] = mapped_column(ForeignKey("admin_roles.id"))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class AuditLog(Base):
    __tablename__ = "admin_audit_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    actor_user_id: Mapped[int | None] = mapped_column(ForeignKey("admin_users.id"), nullable=True)
    action: Mapped[str] = mapped_column(String(50))
    entity_name: Mapped[str] = mapped_column(String(80))
    entity_id: Mapped[int | None] = mapped_column(nullable=True)
    occurred_at: Mapped[datetime] = mapped_column(DateTime)
    detail: Mapped[str | None] = mapped_column(String(300), nullable=True)
