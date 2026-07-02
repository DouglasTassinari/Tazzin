from datetime import datetime

from app.database.models.administration import AuditLog, Role, User
from app.repositories.administration_repository import AuditLogRepository, RoleRepository, UserRepository


def test_find_by_code_and_username(session):
    role = Role(code="ADMIN", name="Administrator")
    session.add(role)
    session.flush()
    user = User(username="jdoe", email="jdoe@example.com", role_id=role.id)
    session.add(user)
    session.flush()

    assert RoleRepository(session).find_by_code("ADMIN").id == role.id
    assert UserRepository(session).find_by_username("jdoe").id == user.id
    assert UserRepository(session).find_by_username("missing") is None


def test_active_users_filters_inactive(session):
    role = Role(code="OPS", name="Operator")
    session.add(role)
    session.flush()
    session.add_all(
        [
            User(username="active1", email="a1@example.com", role_id=role.id, is_active=True),
            User(username="inactive1", email="i1@example.com", role_id=role.id, is_active=False),
        ]
    )
    session.flush()

    active = UserRepository(session).active_users()
    assert [u.username for u in active] == ["active1"]


def test_audit_log_recent_orders_by_most_recent(session):
    repo = AuditLogRepository(session)
    session.add_all(
        [
            AuditLog(action="create", entity_name="Project", entity_id=1, occurred_at=datetime(2026, 1, 1)),
            AuditLog(action="update", entity_name="Project", entity_id=1, occurred_at=datetime(2026, 1, 3)),
        ]
    )
    session.flush()

    recent = repo.recent(limit=5)
    assert recent[0].action == "update"
    assert len(repo.by_entity("Project", 1)) == 2
