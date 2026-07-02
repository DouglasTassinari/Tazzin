from datetime import date

import pytest

from app.core.exceptions import EntityNotFoundError, ValidationError
from app.database.models.projects import ProjectStatus, TaskStatus
from app.services.projects_service import ProjectsService


def test_create_project_persists_in_planning_status(session):
    service = ProjectsService(session)

    project = service.create_project(
        code="PRJ-100",
        name="New CRM",
        start_date=date(2026, 1, 1),
        target_end_date=date(2026, 12, 1),
        budget=100000,
    )

    assert project.id is not None
    assert project.status == ProjectStatus.PLANNING


def test_create_project_rejects_invalid_budget(session):
    service = ProjectsService(session)

    with pytest.raises(ValidationError):
        service.create_project(
            code="PRJ-101",
            name="Bad Budget",
            start_date=date(2026, 1, 1),
            target_end_date=date(2026, 12, 1),
            budget=0,
        )


def test_create_project_rejects_invalid_dates(session):
    service = ProjectsService(session)

    with pytest.raises(ValidationError):
        service.create_project(
            code="PRJ-102",
            name="Bad Dates",
            start_date=date(2026, 12, 1),
            target_end_date=date(2026, 1, 1),
            budget=1000,
        )


def test_transition_project_follows_allowed_path(session):
    service = ProjectsService(session)
    project = service.create_project(
        code="PRJ-103",
        name="Transition Me",
        start_date=date(2026, 1, 1),
        target_end_date=date(2026, 12, 1),
        budget=1000,
    )

    updated = service.transition_project(project.id, ProjectStatus.ACTIVE)
    assert updated.status == ProjectStatus.ACTIVE

    with pytest.raises(ValidationError):
        service.transition_project(project.id, ProjectStatus.PLANNING)


def test_transition_unknown_project_raises_not_found(session):
    service = ProjectsService(session)
    with pytest.raises(EntityNotFoundError):
        service.transition_project(999, ProjectStatus.ACTIVE)


def test_add_task_and_complete_task(session):
    service = ProjectsService(session)
    project = service.create_project(
        code="PRJ-104",
        name="Task Holder",
        start_date=date(2026, 1, 1),
        target_end_date=date(2026, 12, 1),
        budget=1000,
    )

    task = service.add_task(project.id, "Design schema", estimated_hours=8)
    assert task.status == TaskStatus.TODO

    completed = service.complete_task(task.id)
    assert completed.status == TaskStatus.DONE


def test_project_health_report_combines_active_projects_and_completion(session):
    service = ProjectsService(session)
    project = service.create_project(
        code="PRJ-105",
        name="Health Check",
        start_date=date(2026, 1, 1),
        target_end_date=date(2026, 12, 1),
        budget=1000,
    )
    service.transition_project(project.id, ProjectStatus.ACTIVE)
    task = service.add_task(project.id, "Only task", estimated_hours=2)
    service.complete_task(task.id)

    report = service.project_health_report()

    assert report == [{"project": "Health Check", "completion_rate": 100.0, "status": "active"}]
