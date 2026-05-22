"""Run / agent metrics schemas.

Phase 4.4 appends two replay-run models (``RunSummary`` and
``ReplayRunResponse``) used by ``GET /api/demo/run``. The replay-run
contract intentionally uses lowercase string literals (``"replay"``,
``"completed"``, ``"demo"``) instead of the existing ``RunMode`` enum so
the replay-only response object stays self-contained and does not imply
that real agent execution occurred. The existing ``RunMode`` enum is
preserved for future real-run contracts.
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Literal

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.common import AgentRunStatus, RunMode

if TYPE_CHECKING:  # pragma: no cover — circular-import-safe type hint
    # ``app.schemas.lead`` imports ``TraceEntry`` from this module, so
    # importing ``LeadIn`` at runtime here would create a cycle. The
    # forward reference is resolved by ``model_rebuild()`` from
    # ``app.services.run_service`` once both modules are loaded.
    from app.schemas.lead import LeadIn


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
    # Phase 5.1 additions. Optional with defaults so existing callers and
    # tests that build TraceEntry without these fields keep working.
    # ``model`` records which LLM (if any) produced the step; "none" is
    # used by the simulation layer to make it impossible to confuse a
    # simulated trace with a real model call. ``simulated`` is the
    # authoritative flag for downstream UIs/exports.
    model: str = "none"
    simulated: bool = False


# --------------------------------------------------------------------------- #
# Phase 4.4 — Replay run foundation                                            #
# --------------------------------------------------------------------------- #
class RunSummary(BaseModel):
    """Aggregate facts about the leads contained in a replay run.

    All counts are non-negative. ``industries_represented`` and
    ``countries_represented`` are sorted lists of unique non-``None``
    values (empty list when no leads provide that field).
    """

    model_config = ConfigDict(extra="ignore")

    industries_represented: list[str] = Field(default_factory=list)
    countries_represented: list[str] = Field(default_factory=list)
    leads_with_company_research: int = Field(..., ge=0)
    leads_without_company_research: int = Field(..., ge=0)
    leads_with_contact: int = Field(..., ge=0)
    leads_without_contact: int = Field(..., ge=0)


class ReplayRunResponse(BaseModel):
    """Response body for ``GET /api/demo/run``.

    This is a *replay* run built from the static demo dataset. It does
    NOT represent execution of real agents or model calls and therefore
    intentionally omits fields such as ``fit_scores``, ``email_drafts``,
    ``reasoning_traces``, or ``model_responses``. Those belong to future
    phases that introduce real run execution.
    """

    model_config = ConfigDict(extra="ignore")

    run_id: str
    run_mode: Literal["replay"]
    status: Literal["completed"]
    data_source: Literal["demo"]
    source_name: str
    generated_at: datetime
    total_leads: int = Field(..., ge=0)
    valid_leads: int = Field(..., ge=0)
    failed_leads: int = Field(..., ge=0)
    rows_with_warnings: int = Field(..., ge=0)
    model_calls: int = Field(..., ge=0)
    estimated_cost: str
    warnings: list[str] = Field(default_factory=list)
    summary: RunSummary
    leads: list[LeadIn] | None = None
