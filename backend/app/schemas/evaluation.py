"""Trace and evaluation report schemas (Phase 5.3).

Schema-only leaf module (Phase 5.3 FIX 4). It imports from
``app.schemas.common`` for shared enums and from Pydantic itself; it does
**not** import from ``app.schemas.agents``, ``app.schemas.simulation``,
``app.services.simulation_service``, FastAPI routes, or any agent /
model / orchestration runtime.

The view models defined here are derived from the existing simulation
outputs (``LeadDetail`` + ``TraceEntry`` + ``QAScores``). They are not
replacements for those schemas (FIX 2 — ``AgentTraceSummary`` is a
frontend-oriented view, not a substitute for ``TraceEntry``).

What lives here:

* Trace views: :class:`AgentTraceSummary`, :class:`LeadTraceReport`,
  :class:`RunTraceReport`.
* Evaluation views: :class:`EvaluationDimensionScore`,
  :class:`LeadEvaluationReport`, :class:`RunEvaluationSummary`.

All counts and token totals are non-negative; all scores are bounded
``0..100``; all weights are bounded ``0..1``.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.common import (
    HallucinationRisk,
    LeadStatus,
    Priority,
    Recommendation,
    RunMode,
)

# --------------------------------------------------------------------------- #
# Trace views                                                                 #
# --------------------------------------------------------------------------- #


class AgentTraceSummary(BaseModel):
    """Frontend-oriented view of a single ``TraceEntry``.

    This is intentionally a flat, JSON-friendly shape that mirrors what
    a trace-timeline UI consumes. It is **not** a replacement for the
    canonical ``app.schemas.run.TraceEntry`` (FIX 2). Field names match
    the ones already on ``TraceEntry`` so the projection in
    ``evaluation_service`` is a one-to-one copy.
    """

    model_config = ConfigDict(extra="ignore")

    agent: str
    status: str
    model: str = "none"
    simulated: bool = True
    latency: str = "0ms"
    tokens: int = Field(..., ge=0)
    prompt_version: str
    input_summary: str
    output_summary: str


class LeadTraceReport(BaseModel):
    """Trace report for a single lead."""

    model_config = ConfigDict(extra="ignore")

    run_id: str
    lead_id: str
    company_name: str
    run_mode: RunMode
    total_steps: int = Field(..., ge=0)
    total_tokens: int = Field(..., ge=0)
    total_estimated_cost: str
    model_used: str = "none"
    simulated: bool = True
    trace: list[AgentTraceSummary]


class RunTraceReport(BaseModel):
    """Run-level trace report for the full simulation run."""

    model_config = ConfigDict(extra="ignore")

    run_id: str
    run_mode: RunMode
    data_source: str = "demo"
    total_leads: int = Field(..., ge=0)
    total_steps: int = Field(..., ge=0)
    total_tokens: int = Field(..., ge=0)
    total_estimated_cost: str
    simulated: bool = True
    leads: list[LeadTraceReport]


# --------------------------------------------------------------------------- #
# Evaluation views                                                            #
# --------------------------------------------------------------------------- #


class EvaluationDimensionScore(BaseModel):
    """One scoring dimension inside a :class:`LeadEvaluationReport`."""

    model_config = ConfigDict(extra="ignore")

    name: str
    score: int = Field(..., ge=0, le=100)
    weight: float = Field(..., ge=0, le=1)
    notes: list[str] = Field(default_factory=list)


class LeadEvaluationReport(BaseModel):
    """Evaluation report for a single lead."""

    model_config = ConfigDict(extra="ignore")

    run_id: str
    lead_id: str
    company_name: str
    fit_score: int = Field(..., ge=0, le=100)
    qa_score: int = Field(..., ge=0, le=100)
    priority: Priority
    status: LeadStatus
    recommendation: Recommendation
    hallucination_risk: HallucinationRisk
    dimensions: list[EvaluationDimensionScore]
    strengths: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    simulated: bool = True


class RunEvaluationSummary(BaseModel):
    """Run-level evaluation report for the full simulation run."""

    model_config = ConfigDict(extra="ignore")

    run_id: str
    run_mode: RunMode
    data_source: str = "demo"
    total_leads: int = Field(..., ge=0)
    avg_fit_score: float = Field(..., ge=0, le=100)
    avg_qa_score: float = Field(..., ge=0, le=100)
    high_priority_leads: int = Field(..., ge=0)
    medium_priority_leads: int = Field(..., ge=0)
    low_priority_leads: int = Field(..., ge=0)
    needs_edit_or_review: int = Field(..., ge=0)
    total_estimated_cost: str
    total_tokens: int = Field(..., ge=0)
    simulated: bool = True
    leads: list[LeadEvaluationReport]
