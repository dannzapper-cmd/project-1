"""Health endpoint.

Performs a lightweight `SELECT 1` against the database so that broken DB
wiring is surfaced immediately rather than at first real query.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core.config import get_settings
from app.core.logging import get_logger
from app.schemas.health import HealthResponse, SystemStatusResponse

router = APIRouter(tags=["health"])
logger = get_logger(__name__)


@router.get("/health", response_model=HealthResponse)
def health(db: Session = Depends(get_db)) -> HealthResponse:
    settings = get_settings()

    db_status: str = "ok"
    try:
        db.execute(text("SELECT 1"))
    except Exception:  # noqa: BLE001
        logger.exception("Database health check failed")
        db_status = "error"

    return HealthResponse(
        status="ok" if db_status == "ok" else "degraded",
        app=settings.app_name,
        version=settings.app_version,
        env=settings.app_env,
        db=db_status,  # type: ignore[arg-type]
    )


@router.get("/api/system/status", response_model=SystemStatusResponse)
def system_status() -> SystemStatusResponse:
    """Return safe deployment diagnostics without exposing secret values."""

    settings = get_settings()
    groq_live_configured = bool(
        settings.enable_live_model_pipeline and settings.groq_api_key
    )
    controlled_email_regenerate_configured = bool(
        groq_live_configured
        and settings.rate_limit_enabled
        and (settings.demo_access_code or "").strip()
    )
    return SystemStatusResponse(
        demo_access_required=bool((settings.demo_access_code or "").strip()),
        live_research_configured=bool(
            settings.enable_live_research and settings.exa_api_key
        ),
        live_model_pipeline_configured=groq_live_configured,
        live_email_regenerate_configured=controlled_email_regenerate_configured,
        assistant_configured=bool(
            settings.enable_llm_assistant and settings.groq_api_key
        ),
        rate_limit_enabled=settings.rate_limit_enabled,
        max_leads_per_run=settings.max_leads_per_run,
        max_upload_size_mb=settings.intake_max_upload_mb,
        build_sha=settings.build_sha,
    )
