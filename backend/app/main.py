"""FastAPI application entry point.

Wires the LeadForge backend together:

- App factory with CORS middleware.
- Centralized logging configuration.
- SQLite schema initialization on startup (via lifespan).
- `/health` endpoint (mounted at the application root, kept stable since
  Fase 4.1).
- Read-only demo data endpoints under `/api/demo/*` (added in Fase 4.2),
  exposing the static files shipped under `data/demo/`.
- Smart lead intake preview at `POST /api/intake/preview` (added in
  Fase 4.3A): a preview-only normalization layer with no DB writes,
  agents, or LLM calls.

Out of scope at this layer (and intentionally NOT implemented yet): agents,
LangGraph orchestration, LLM/model calls, RAG, vector stores, and any real
lead processing or external side effects. Those belong to later phases.
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import assistant as assistant_routes
from app.api.routes import demo as demo_routes
from app.api.routes import health as health_routes
from app.api.routes import intake as intake_routes
from app.api.routes import research as research_routes
from app.api.routes import telemetry as telemetry_routes
from app.core.config import get_settings
from app.core.logging import configure_logging, get_logger
from app.core.safety import (
    InMemoryRateLimiter,
    build_request_safety_middleware,
    build_security_headers_middleware,
)
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
            "(`/health`), read-only demo data endpoints (`/api/demo/*`) "
            "served from the static files under `data/demo/`, and a "
            "smart lead intake preview at `POST /api/intake/preview` "
            "(Fase 4.3A). No agents, no LLM, no RAG, no real lead "
            "processing yet."
        ),
        lifespan=lifespan,
    )

    request_limiter = InMemoryRateLimiter()
    app.middleware("http")(
        build_request_safety_middleware(
            settings=settings,
            limiter=request_limiter,
            logger=logger,
        )
    )

    # Basic security headers for the public demo. Content-Security-Policy is
    # intentionally deferred because the current frontend setup needs a fuller
    # asset/script inventory before CSP can be added safely.
    app.middleware("http")(build_security_headers_middleware())

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_origin_regex=r"^https://v0-project-1-[a-z0-9-]+\.vercel\.app$",
        allow_credentials=True,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["*"],
    )

    app.include_router(health_routes.router)
    app.include_router(demo_routes.router)
    app.include_router(intake_routes.router)
    app.include_router(research_routes.router)
    app.include_router(assistant_routes.router)
    app.include_router(telemetry_routes.router)

    return app


app = create_app()
