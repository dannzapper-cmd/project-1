"""Lightweight telemetry schemas for deterministic pipeline runs.

These models intentionally carry summary-level observability only. They do
not include prompts, raw agent inputs, private lead payloads, generated email
bodies, or raw provider responses.
"""

from __future__ import annotations

from datetime import datetime, timezone

from pydantic import BaseModel, ConfigDict, Field


def utc_now_iso() -> str:
    """Return a stable UTC timestamp string for telemetry records."""

    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


class RunTelemetryEntry(BaseModel):
    """One safe telemetry entry for one agent step in one pipeline run."""

    model_config = ConfigDict(extra="ignore")

    run_id: str
    lead_id: str | None = None
    agent_name: str
    status: str
    run_mode: str
    model_mode: str
    model_used: str | None = None
    prompt_version: str | None = None
    latency_ms: int | None = Field(default=None, ge=0)
    input_tokens_estimate: int | None = Field(default=None, ge=0)
    output_tokens_estimate: int | None = Field(default=None, ge=0)
    total_tokens_estimate: int | None = Field(default=None, ge=0)
    estimated_cost_usd: float | None = Field(default=None, ge=0.0)
    parse_success: bool | None = None
    fallback_used: bool | None = None
    qa_score: int | None = Field(default=None, ge=0, le=100)
    hallucination_risk: str | None = None
    recommendation: str | None = None
    warning_count: int = Field(default=0, ge=0)
    error_category: str | None = None
    created_at: str = Field(default_factory=utc_now_iso)


class RunTelemetrySummary(BaseModel):
    """Aggregated safe telemetry summary for one pipeline run."""

    model_config = ConfigDict(extra="ignore")

    run_id: str
    lead_count: int = Field(..., ge=0)
    agent_step_count: int = Field(..., ge=0)
    success_count: int = Field(..., ge=0)
    warning_count: int = Field(..., ge=0)
    failed_count: int = Field(..., ge=0)
    total_latency_ms: int | None = Field(default=None, ge=0)
    estimated_total_cost_usd: float = Field(..., ge=0.0)
    average_qa_score: float | None = None
    highest_hallucination_risk: str | None = None
    model_modes: list[str] = Field(default_factory=list)
    run_mode: str
    created_at: str


class RunTelemetryDetail(BaseModel):
    """Run summary plus the safe agent-step entries that produced it."""

    model_config = ConfigDict(extra="ignore")

    run_id: str
    summary: RunTelemetrySummary
    entries: list[RunTelemetryEntry]
