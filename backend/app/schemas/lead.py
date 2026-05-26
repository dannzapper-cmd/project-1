"""Lead-related Pydantic v2 schemas.

`LeadIn` mirrors the columns of `data/demo/leads.csv`.
`LeadOut` / `LeadDetail` mirror the shapes consumed by the frontend
(`lib/types.ts: Lead`, `LeadDetail`). No endpoints use these yet — they
define the contract for Block 4.2.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.common import Confidence, LeadStatus, Priority, RunMode
from app.schemas.qa import EvidenceCard, QAScores
from app.schemas.run import TraceEntry


class LeadIn(BaseModel):
    """Raw lead row as ingested from CSV / API input."""

    model_config = ConfigDict(from_attributes=True)

    lead_id: str = Field(..., description="External lead identifier")
    company_name: str
    website: str | None = None
    industry: str | None = None
    country: str | None = None
    employee_count: int | None = Field(default=None, ge=0)
    contact_name: str | None = None
    contact_role: str | None = None
    notes: str | None = None


class LeadOut(BaseModel):
    """Lead as displayed in the dashboard table row."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    company: str
    website: str
    industry: str
    country: str
    employees: str
    contact_name: str
    contact_role: str
    fit_score: int = Field(..., ge=0, le=100)
    priority: Priority
    qa_score: int = Field(..., ge=0, le=100)
    status: LeadStatus
    est_cost: str
    email_subject: str
    run_mode: RunMode


class LeadDetail(LeadOut):
    """Full lead detail used by the side drawer / detail view."""

    company_summary: str
    opportunity_signals: list[str] = Field(default_factory=list)
    evidence_cards: list[EvidenceCard] = Field(default_factory=list)
    fit_reasons: list[str] = Field(default_factory=list)
    fit_risks: list[str] = Field(default_factory=list)
    pain_hypothesis: str
    pain_confidence: Confidence
    sales_angle: str
    core_message: str
    likely_objection: str
    email_body: str
    personalization_notes: list[str] = Field(default_factory=list)
    qa_scores: QAScores
    est_total_latency: str
    model_used: str
    agent_steps: int = Field(..., ge=0)
    est_tokens: int = Field(..., ge=0)
    trace: list[TraceEntry] = Field(default_factory=list)


class LeadBatchProcessRequest(BaseModel):
    """User-provided leads to run through the deterministic batch pipeline."""

    model_config = ConfigDict(extra="ignore")

    leads: list[LeadIn] = Field(
        ...,
        min_length=1,
        max_length=10,
        description="Normalized, preview-confirmed leads. Max 10 per run.",
    )
    source_name: str | None = None
