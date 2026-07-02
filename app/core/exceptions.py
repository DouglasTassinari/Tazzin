"""Exception hierarchy shared across all OpsVision layers.

Repositories raise ``DataAccessError`` subclasses; services translate
domain violations into ``BusinessRuleError`` subclasses. The interface
layer only needs to catch ``OpsVisionError`` to render a friendly message.
"""
from __future__ import annotations


class OpsVisionError(Exception):
    """Base class for all application-raised errors."""


class DataAccessError(OpsVisionError):
    """Raised when a repository operation cannot be completed."""


class EntityNotFoundError(DataAccessError):
    """Raised when a lookup by id finds no matching row."""

    def __init__(self, entity_name: str, entity_id: object):
        self.entity_name = entity_name
        self.entity_id = entity_id
        super().__init__(f"{entity_name} {entity_id!r} not found")


class BusinessRuleError(OpsVisionError):
    """Raised when an operation violates a domain business rule."""


class ValidationError(BusinessRuleError):
    """Raised when input data fails domain validation before persistence."""
