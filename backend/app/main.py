"""FastAPI application entry point.

Wires the LeadForge backend together:

- App factory with CORS middleware.
- Centralized logging configuration.
- SQLite schema initialization on startup (via lifespan).
- `/health` endpoint (mounted at the application root, kept stable since
  Fase 4.1).
- Read-only demo data endpoints under `/api/demo/*` (added in Fase 4.2),
  exposing the static files shipped under `data/demo/`.
- Smart intake preview endpoint `/api/intake/preview` (added in Fase 4.3A).

Out of scope at this layer (and intentionally NOT implemented yet): agents,
LangGraph orchestration, LLM/model calls, RAG, vector stores, and any real
lead processing or external side effects. Those belong to later phases.
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import demo as demo_routes
from app.api.routes import health as health_routes
from app.api.routes import intake as intake_routes
from app.core.config import get_settings
from app.core.logging import configure_logging, get_logger
from app.db.init_db import init_db


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging(settings.log_level)
    logger = get_logger(__name__)

    @asynccontextmanager
    async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
        logger.info(
            "Starting %s v%s (env=%s)",
            settings.app_name,
            settings.app_version,
            settings.app_env,
        )
        init_db()
        yield
        logger.info("Shutting down %s", settings.app_name)

    app = FastAPI(
        title="LeadForge Backend",
        version=settings.app_version,
        description=(
            "Backend for LeadForge-Agentic Core. Exposes a health probe "
            "(`/health`) and read-only demo data endpoints (`/api/demo/*`) "
            "served from the static files under `data/demo/`, plus the "
            "Fase 4.3A preview-only intake endpoint (`/api/intake/preview`). "
            "No agents, no LLM, no RAG, no real lead processing yet."
        ),
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health_routes.router)
    app.include_router(demo_routes.router)
    app.include_router(intake_routes.router, prefix="/api/intake")

    return app


app = create_app()
