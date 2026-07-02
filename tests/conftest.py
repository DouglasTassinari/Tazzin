"""Shared pytest fixtures: an isolated in-memory SQLite database per test."""
from __future__ import annotations

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import app.database.models  # noqa: F401 — registers every model on Base.metadata
from app.database.base import Base
from app.database.models.core import Location, LocationType
from app.database.models.inventory import Product, ProductCategory


@pytest.fixture()
def session():
    engine = create_engine("sqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    TestingSession = sessionmaker(bind=engine, future=True)
    db = TestingSession()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture()
def location(session):
    loc = Location(
        code="HQ1",
        name="Headquarters",
        city="Springfield",
        state="IL",
        location_type=LocationType.OFFICE,
    )
    session.add(loc)
    session.flush()
    return loc


@pytest.fixture()
def product(session):
    prod = Product(
        sku="SKU-0001",
        name="Sample Product",
        category=ProductCategory.FINISHED_GOOD,
        unit_cost=10.0,
        unit_price=25.0,
        reorder_point=50,
    )
    session.add(prod)
    session.flush()
    return prod
