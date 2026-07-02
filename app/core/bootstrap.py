"""First-run bootstrap: create the schema and seed demo data if empty.

Called by the Streamlit entrypoint so cloud deployments (e.g. Streamlit
Community Cloud), which start without the gitignored SQLite file, come up
with a populated dashboard instead of empty pages. A database that already
has data is left untouched.
"""
from __future__ import annotations

from pathlib import Path

from sqlalchemy import select

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger("bootstrap")


def ensure_demo_data() -> None:
    import app.database.models  # noqa: F401 — registers every model on Base.metadata
    from app.database.base import Base, SessionLocal, engine
    from app.database.models.sales import Customer

    if settings.is_sqlite and engine.url.database:
        Path(engine.url.database).parent.mkdir(parents=True, exist_ok=True)

    Base.metadata.create_all(engine)

    session = SessionLocal()
    try:
        has_data = session.execute(select(Customer.id).limit(1)).first() is not None
    finally:
        session.close()

    if has_data:
        return

    logger.info("empty database detected; generating synthetic demo dataset")
    from scripts.generate_synthetic_data import run

    run()
    logger.info("synthetic demo dataset generated")


def ensure_demo_data_once() -> None:
    """Streamlit-cached wrapper, safe to call at the top of every page.

    Pages are standalone scripts in Streamlit, so each one must trigger the
    bootstrap itself — a visitor may deep-link to a page before the home
    page has ever run. ``st.cache_resource`` makes this a no-op after the
    first call in the process.
    """
    import streamlit as st

    @st.cache_resource(show_spinner="Preparando o banco de dados de demonstração...")
    def _cached() -> bool:
        ensure_demo_data()
        return True

    _cached()
