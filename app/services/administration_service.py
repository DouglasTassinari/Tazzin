"""Administration module service: users, roles, audit trail and system
observability (health checks + in-process metrics).
"""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.core.health import HealthReport, run_health_checks
from app.core.logging import get_logger
from app.core.metrics import metrics, track
from app.database.models.administration import AuditLog, Role, User
from app.domain import administration_rules
from app.repositories.administration_repository import (
    AuditLogRepository,
    RoleRepository,
    UserRepository,
)

logger = get_logger("services.administration")


class AdministrationService:
    def __init__(self, session: Session):
        self.session = session
        self.roles = RoleRepository(session)
        self.users = UserRepository(session)
        self.audit_logs = AuditLogRepository(session)

    @track("administration.create_role")
    def create_role(self, code: str, name: str, description: str = "") -> Role:
        role = Role(code=code, name=name, description=description)
        self.roles.add(role)
        return role

    @track("administration.create_user")
    def create_user(self, username: str, email: str, role_id: int, employee_id: int | None = None) -> User:
        administration_rules.validate_username(username)
        administration_rules.validate_email(email)
        user = User(username=username, email=email, role_id=role_id, employee_id=employee_id)
        self.users.add(user)
        logger.info("Created user %s", username)
        return user

    @track("administration.record_audit_event")
    def record_audit_event(
        self, action: str, entity_name: str, entity_id: int | None, actor_user_id: int | None = None, detail: str | None = None
    ) -> AuditLog:
        entry = AuditLog(
            actor_user_id=actor_user_id,
            action=action,
            entity_name=entity_name,
            entity_id=entity_id,
            occurred_at=datetime.now(timezone.utc),
            detail=detail,
        )
        self.audit_logs.add(entry)
        return entry

    def recent_audit_events(self, limit: int = 20) -> list[AuditLog]:
        return self.audit_logs.recent(limit)

    def active_users(self) -> list[User]:
        return self.users.active_users()

    def system_health(self) -> HealthReport:
        return run_health_checks()

    def system_metrics(self) -> dict:
        return metrics.snapshot()
