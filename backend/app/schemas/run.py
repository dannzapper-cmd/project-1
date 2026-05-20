"""Run / agent metrics schemas."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.common import AgentRunStatus, RunMode


class AgentStatus(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: str
    status: AgentRunStatus
    success_rate: str
    avg_latency: str


class RunMetrics(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    total_processed: int = Field(..., ge=0)
    high_fit_leads: int = Field(..., ge=0)
    avg_qa_score: float = Field(..., ge=0, le=100)
    total_cost: str
    run_timestamp: str
    model_used: str
    run_mode: RunMode


class TraceEntry(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    agent: str
    status: AgentRunStatus
    input_summary: str
    output_summary: str
    latency: str
    tokens: int = Field(..., ge=0)
    prompt_version: str
