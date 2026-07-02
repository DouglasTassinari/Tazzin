"""SQLAlchemy engine, session factory and declarative base.

Every model module imports ``Base`` from here so a single
``Base.metadata.create_all`` (see :mod:`scripts.init_db`) builds the
whole schema regardless of which modules happen to be imported.
"""
from __future__ import annotations

from contextlib import contextmanager
from typing import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import settings

_connect_args = {"check_same_thread": False} if settings.is_sqlite else {}

engine = create_engine(settings.database_url, connect_args=_connect_args, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


class Base(DeclarativeBase):
    """Declarative base shared by every ORM model in the platform."""


@contextmanager
def session_scope() -> Iterator[Session]:
    """Provide a transactional session: commits on success, rolls back on error."""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
