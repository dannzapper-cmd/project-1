"""FastAPI application entry point — Fase 4.1.

Strict scope: app factory, CORS, logging, DB init on startup, /health route.
No agents, no LangGraph, no LLM, no RAG, no real lead processing.
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import health as health_routes
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
            "Backend foundation for LeadForge-Agentic Core. "
            "Fase 4.1: skeleton only (no agents, no LLM, no RAG)."
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

    return app


app = create_app()
