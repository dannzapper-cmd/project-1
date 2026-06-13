"""Schemas for the controlled Groq Live Demo Mode endpoints."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.lead import LeadIn
from app.schemas.live_pipeline import LivePipelineResponse


class LiveDemoLimits(BaseModel):
    """Safe limit snapshot exposed to the frontend."""

    model_config = ConfigDict(extra="ignore")

    max_live_leads_per_run: int
    max_live_runs_per_session_per_day: int
    max_live_runs_per_ip_per_day: int
    max_live_agent_steps_per_lead: int
    max_live_tokens_per_lead: int
    daily_live_demo_budget_usd: float
    live_model_timeout_seconds: int
    live_concurrency_limit: int


class LiveDemoStatusResponse(BaseModel):
    """GET /api/demo/live/status — availability without secrets."""

    model_config = ConfigDict(extra="ignore")

    available: bool
    groq_configured: bool
    live_mode_enabled: bool
    live_mode_unlocked: bool = False
    unlock_required: bool = True
    model_name: str | None = None
    limits: LiveDemoLimits
    unavailable_reasons: list[str] = Field(default_factory=list)
    session_runs_remaining_today: int | None = None
    ip_runs_remaining_today: int | None = None
    daily_budget_remaining_usd: float | None = None


class LiveDemoUnlockRequest(BaseModel):
    unlock_code: str = Field(..., min_length=1, max_length=64)


class LiveDemoUnlockResponse(BaseModel):
    unlocked: bool
    session_token: str | None = None
    message: str


class LiveDemoRunRequest(BaseModel):
    """Structured lead input for a controlled live demo run."""

    lead_ids: list[str] = Field(..., min_length=1, max_length=10)
    leads: list[LeadIn] | None = None


class LiveDemoRunMetadata(BaseModel):
    """Honest metadata for every live or fallback result."""

    model_config = ConfigDict(extra="ignore")

    run_mode: Literal["replay", "deterministic", "groq_live", "fallback"]
    model_provider: str | None = None
    model_name: str | None = None
    estimated_tokens: int | None = None
    estimated_cost_usd: float | None = None
    latency_ms: float | None = None
    parse_success: bool | None = None
    fallback_used: bool = False
    warnings: list[str] = Field(default_factory=list)
    limits_applied: list[str] = Field(default_factory=list)
    live_mode_unlocked: bool = False


class LiveDemoLeadResult(BaseModel):
    lead_id: str
    pipeline: LivePipelineResponse | None = None
    metadata: LiveDemoRunMetadata
    error: str | None = None


class LiveDemoRunResponse(BaseModel):
    results: list[LiveDemoLeadResult]
    rejected_lead_ids: list[str] = Field(default_factory=list)
    message: str | None = None


__all__ = [
    "LiveDemoLeadResult",
    "LiveDemoLimits",
    "LiveDemoRunMetadata",
    "LiveDemoRunRequest",
    "LiveDemoRunResponse",
    "LiveDemoStatusResponse",
    "LiveDemoUnlockRequest",
    "LiveDemoUnlockResponse",
]
