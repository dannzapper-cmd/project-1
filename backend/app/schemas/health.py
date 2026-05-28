"""Health endpoint response schema."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: Literal["ok", "degraded"] = "ok"
    app: str = Field(..., description="Application name")
    version: str = Field(..., description="Application version")
    env: str = Field(..., description="Application environment")
    db: Literal["ok", "error"] = Field(..., description="Database connectivity status")


class SystemStatusResponse(BaseModel):
    backend_alive: bool = True
    demo_mode_available: bool = True
    demo_access_required: bool
    live_research_configured: bool
    live_model_pipeline_configured: bool = False
    live_email_regenerate_configured: bool = False
    assistant_configured: bool
    rate_limit_enabled: bool
    max_leads_per_run: int
    max_upload_size_mb: int
    live_single_lead_only: bool = True
    public_live_batch_enabled: bool = False
    storage_mode: Literal["ephemeral"] = "ephemeral"
    build_sha: str = ""
