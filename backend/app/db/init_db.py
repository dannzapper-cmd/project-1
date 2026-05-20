"""Database initialization helpers.

Fase 4.1 uses a simple `create_all()` strategy. Alembic migrations will be
introduced in a later phase if/when the schema starts evolving.
"""

from __future__ import annotations

from app.core.logging import get_logger
from app.db.base import Base
from app.db.session import engine

# Import models so they are registered on Base.metadata before create_all.
from app.db import models  # noqa: F401

logger = get_logger(__name__)


def init_db() -> None:
    """Create all tables if they do not exist yet."""
    logger.info("Initializing database schema (create_all)")
    Base.metadata.create_all(bind=engine)
