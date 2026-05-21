"""Pydantic v2 schemas for the Fase 4.2 demo data endpoints.

This module deliberately does NOT redefine the lead schema:
demo leads are exposed via `app.schemas.lead.LeadIn`, which already
mirrors the columns of `data/demo/leads.csv`.

Only research-specific and summary-specific schemas live here.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class DemoOpportunitySignal(BaseModel):
    model_config = ConfigDict(extra="ignore")

    signal: str
    why_it_matters: str | None = None
    source_type: str | None = None
    confidence: str | None = None


class DemoPainHypothesis(BaseModel):
    model_config = ConfigDict(extra="ignore")

    pain: str
    reasoning: str | None = None
    confidence: str | None = None


class DemoEvidenceCard(BaseModel):
    model_config = ConfigDict(extra="ignore")

    # The demo JSON uses `title` for evidence cards; the dashboard schema in
    # app/schemas/qa.py uses `headline`. We mirror the raw JSON here.
    title: str
    description: str | None = None
    source_type: str | None = None
    confidence: str | None = None


class DemoCompanyResearch(BaseModel):
    """One record from data/demo/company_research.json."""

    model_config = ConfigDict(extra="ignore")

    lead_id: str = Field(..., description="Joins to lead_id in leads.csv")
    company_name: str
    research_status: str

    company_summary: str | None = None
    business_model: str | None = None
    target_customers: list[str] = Field(default_factory=list)
    opportunity_signals: list[DemoOpportunitySignal] = Field(default_factory=list)
    pain_hypotheses: list[DemoPainHypothesis] = Field(default_factory=list)
    evidence_cards: list[DemoEvidenceCard] = Field(default_factory=list)
    information_risks: list[str] = Field(default_factory=list)
    recommended_research_summary: str | None = None


class DemoSummary(BaseModel):
    """Response body for GET /api/demo/summary."""

    model_config = ConfigDict(extra="ignore")

    total_leads: int = Field(..., ge=0)
    total_research_records: int = Field(..., ge=0)
    data_source: str = "synthetic_demo"
    status: str = "ready"
