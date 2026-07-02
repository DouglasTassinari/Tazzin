"""Projects module schema: Project, Task, Milestone."""
from __future__ import annotations

import enum
from datetime import date

from sqlalchemy import Date, Enum, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.database.models.core import TimestampMixin


class ProjectStatus(str, enum.Enum):
    PLANNING = "planning"
    ACTIVE = "active"
    ON_HOLD = "on_hold"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class TaskStatus(str, enum.Enum):
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    BLOCKED = "blocked"
    DONE = "done"


class Project(TimestampMixin, Base):
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(15), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(150))
    sponsor_department_id: Mapped[int | None] = mapped_column(
        ForeignKey("people_departments.id"), nullable=True
    )
    status: Mapped[ProjectStatus] = mapped_column(Enum(ProjectStatus), default=ProjectStatus.PLANNING)
    start_date: Mapped[date] = mapped_column(Date)
    target_end_date: Mapped[date] = mapped_column(Date)
    budget: Mapped[float] = mapped_column(Numeric(12, 2))

    tasks: Mapped[list["Task"]] = relationship(back_populates="project", cascade="all, delete-orphan")
    milestones: Mapped[list["Milestone"]] = relationship(
        back_populates="project", cascade="all, delete-orphan"
    )


class Task(Base):
    __tablename__ = "projects_tasks"

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), index=True)
    title: Mapped[str] = mapped_column(String(200))
    assignee_employee_id: Mapped[int | None] = mapped_column(
        ForeignKey("people_employees.id"), nullable=True
    )
    status: Mapped[TaskStatus] = mapped_column(Enum(TaskStatus), default=TaskStatus.TODO)
    due_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    estimated_hours: Mapped[float] = mapped_column(Numeric(6, 2), default=0)

    project: Mapped["Project"] = relationship(back_populates="tasks")


class Milestone(Base):
    __tablename__ = "projects_milestones"

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), index=True)
    name: Mapped[str] = mapped_column(String(150))
    due_date: Mapped[date] = mapped_column(Date)
    achieved: Mapped[bool] = mapped_column(default=False)
    achieved_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    project: Mapped["Project"] = relationship(back_populates="milestones")
