"""Shared FastAPI dependencies."""

from __future__ import annotations

from collections.abc import Iterator

from sqlalchemy.orm import Session

from app.db.session import get_db as _get_db


def get_db() -> Iterator[Session]:
    """Re-export of the SQLAlchemy session dependency for the API layer."""
    yield from _get_db()
