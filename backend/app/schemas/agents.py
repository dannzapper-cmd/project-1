"""Agent contract schemas (Phase 5.2).

Defines the Pydantic v2 input/output contracts that every future LeadForge
agent must obey. This module is **contracts only** — it contains no agent
runtime, no LLM/model calls, no orchestration, no LangGraph, no RAG, no
Chroma, no scraping, no DB writes, no live research, no external I/O.

Architecture rules (per Phase 5.2 FIX 3):

* ``agents.py`` is a **leaf schema module**. It imports from existing
  schemas (``common``, ``lead``, ``run``, ``qa``) but nothing in the
  existing schema package imports from it. This keeps the dependency
  graph acyclic and protects the existing ``model_rebuild()`` calls in
  ``run.py`` / ``run_service.py`` from being affected by anything added
  here.
* All bounded integers use ``Field(..., ge=0, le=100)`` (FIX 1).
* ``EvidenceCard`` is imported from ``app.schemas.qa`` and never
  redefined here (FIX 2).

The agents defined are:

1. Intake Agent          -- validates / normalizes a raw lead.
2. Research Agent        -- builds company context and evidence.
3. Qualifier Agent       -- scores ICP fit and assigns priority.
4. Strategist Agent      -- selects sales angle and message strategy.
5. Email Drafter Agent   -- produces reviewable email draft (never sends).
6. QA Evaluator Agent    -- scores quality, evidence, tone, CTA, hallucination.

Plus an optional, runtime-free container:

* :class:`LeadPipelineContractOutput` -- aggregates the six per-lead agent
  outputs and a structural trace. This is a contract container only; it
  does not imply orchestration.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.common import (
    Confidence,
    HallucinationRisk,
    Priority,
    Recommendation,
    RunMode,
)
from app.schemas.lead import LeadIn
from app.schemas.qa import EvidenceCard, QAScores
from app.schemas.run import TraceEntry

# --------------------------------------------------------------------------- #
# Shared envelope types                                                       #
# --------------------------------------------------------------------------- #


class AgentError(BaseModel):
    """Structured error surfaced by an agent.

    ``recoverable`` defaults to ``True`` so a caller's retry/fallback path
    is the explicit default behavior; agents must opt in to
    ``recoverable=False`` when they detect a fatal contract violation.
    """

    model_config = ConfigDict(extra="ignore")

    code: str
    message: str
    recoverable: bool = True
    details: dict[str, str] | None = None


class AgentExecutionMetadata(BaseModel):
    """Per-call execution metadata attached to every agent output.

    Default values are deliberately chosen so that a contract instantiated
    with no overrides represents a *non-executing* agent: no model is
    declared, no tokens consumed, no cost incurred, and ``simulated`` is
    ``False`` (i.e. the default is "real, but inert"). Phase 5.x layers
    that actually execute agents will override these explicitly.
    """

    model_config = ConfigDict(extra="ignore")

    agent_name: str
    run_mode: RunMode
    model: str = "none"
    prompt_version: str = "contract_v1"
    latency: str = "0ms"
    tokens: int = Field(default=0, ge=0)
    cost: str = "$0.00"
    simulated: bool = False


class AgentContractResult(BaseModel):
    """Outcome envelope shared by every agent output.

    ``error`` is required to be ``None`` when ``success`` is ``True``;
    callers must check ``success`` before reading the per-agent payload
    fields on the surrounding output model.
    """

    model_config = ConfigDict(extra="ignore")

    success: bool
    metadata: AgentExecutionMetadata
    error: AgentError | None = None


# --------------------------------------------------------------------------- #
# A) Intake Agent                                                             #
# --------------------------------------------------------------------------- #


class IntakeAgentInput(BaseModel):
    """Input contract for the Intake Agent.

    The Intake Agent receives a raw ``LeadIn`` row and is responsible for
    validating and normalizing it before the downstream pipeline sees it.
    """

    model_config = ConfigDict(extra="ignore")

    raw_lead: LeadIn
    run_id: str | None = None
    source: str = "demo"


class IntakeAgentOutput(BaseModel):
    """Output contract for the Intake Agent."""

    model_config = ConfigDict(extra="ignore")

    result: AgentContractResult
    normalized_lead: LeadIn
    validation_flags: list[str] = Field(default_factory=list)
    confidence: Confidence


# --------------------------------------------------------------------------- #
# B) Research Agent                                                           #
# --------------------------------------------------------------------------- #


class ResearchAgentInput(BaseModel):
    """Input contract for the Research Agent.

    ``available_context`` is a free-form bag the orchestrator can use to
    pass pre-fetched / cached context (e.g. the existing demo research
    JSON) without committing the contract to a specific shape. Real-time
    web research is explicitly out of scope for the contract.
    """

    model_config = ConfigDict(extra="ignore")

    lead: LeadIn
    run_id: str | None = None
    available_context: dict | None = None


class ResearchAgentOutput(BaseModel):
    """Output contract for the Research Agent."""

    model_config = ConfigDict(extra="ignore")

    result: AgentContractResult
    lead_id: str
    company_summary: str
    opportunity_signals: list[str] = Field(default_factory=list)
    pain_hypotheses: list[str] = Field(default_factory=list)
    evidence_cards: list[EvidenceCard] = Field(default_factory=list)
    information_risks: list[str] = Field(default_factory=list)
    confidence: Confidence


# --------------------------------------------------------------------------- #
# C) Qualifier Agent                                                          #
# --------------------------------------------------------------------------- #


class QualifierAgentInput(BaseModel):
    """Input contract for the Qualifier Agent."""

    model_config = ConfigDict(extra="ignore")

    lead: LeadIn
    research_summary: str | None = None
    opportunity_signals: list[str] = Field(default_factory=list)
    information_risks: list[str] = Field(default_factory=list)
    run_id: str | None = None


class QualifierAgentOutput(BaseModel):
    """Output contract for the Qualifier Agent.

    ``fit_score`` is bounded ``0..100`` (FIX 1). The Pydantic v2
    validator will reject out-of-range values at construction time.
    """

    model_config = ConfigDict(extra="ignore")

    result: AgentContractResult
    lead_id: str
    fit_score: int = Field(..., ge=0, le=100)
    priority: Priority
    fit_reasons: list[str] = Field(default_factory=list)
    fit_risks: list[str] = Field(default_factory=list)
    confidence: Confidence


# --------------------------------------------------------------------------- #
# D) Strategist Agent                                                         #
# --------------------------------------------------------------------------- #


class StrategistAgentInput(BaseModel):
    """Input contract for the Strategist Agent.

    ``fit_score`` is bounded ``0..100`` so the input contract cannot be
    instantiated with an out-of-range qualification score upstream.
    """

    model_config = ConfigDict(extra="ignore")

    lead: LeadIn
    company_summary: str
    opportunity_signals: list[str] = Field(default_factory=list)
    pain_hypotheses: list[str] = Field(default_factory=list)
    fit_score: int = Field(..., ge=0, le=100)
    priority: Priority
    run_id: str | None = None


class StrategistAgentOutput(BaseModel):
    """Output contract for the Strategist Agent."""

    model_config = ConfigDict(extra="ignore")

    result: AgentContractResult
    lead_id: str
    pain_hypothesis: str
    pain_confidence: Confidence
    sales_angle: str
    core_message: str
    likely_objection: str
    personalization_notes: list[str] = Field(default_factory=list)


# --------------------------------------------------------------------------- #
# E) Email Drafter Agent                                                      #
# --------------------------------------------------------------------------- #


class EmailDrafterAgentInput(BaseModel):
    """Input contract for the Email Drafter Agent.

    The agent's contract explicitly does not include any delivery /
    transport fields. Phase 5.2 prohibits any email-sending behavior,
    now and structurally.
    """

    model_config = ConfigDict(extra="ignore")

    lead: LeadIn
    company_summary: str
    pain_hypothesis: str
    sales_angle: str
    core_message: str
    personalization_notes: list[str] = Field(default_factory=list)
    run_id: str | None = None


class EmailDrafterAgentOutput(BaseModel):
    """Output contract for the Email Drafter Agent.

    Produces a reviewable draft only. The contract intentionally has no
    ``sent`` / ``delivered`` / ``recipient`` fields — those would imply
    side effects the project does not support in the portfolio version.
    """

    model_config = ConfigDict(extra="ignore")

    result: AgentContractResult
    lead_id: str
    email_subject: str
    email_body: str
    personalization_notes: list[str] = Field(default_factory=list)
    confidence: Confidence


# --------------------------------------------------------------------------- #
# F) QA Evaluator Agent                                                       #
# --------------------------------------------------------------------------- #


class QAEvaluatorAgentInput(BaseModel):
    """Input contract for the QA Evaluator Agent."""

    model_config = ConfigDict(extra="ignore")

    lead: LeadIn
    email_subject: str
    email_body: str
    evidence_cards: list[EvidenceCard] = Field(default_factory=list)
    personalization_notes: list[str] = Field(default_factory=list)
    run_id: str | None = None


class QAEvaluatorAgentOutput(BaseModel):
    """Output contract for the QA Evaluator Agent.

    ``qa_score`` is the top-level integer summary bounded ``0..100``
    (FIX 1). ``qa_scores`` carries the existing per-dimension breakdown
    from ``app.schemas.qa.QAScores``; the contract reuses that model
    verbatim so future agents and the existing simulation layer stay
    aligned on the QA shape.
    """

    model_config = ConfigDict(extra="ignore")

    result: AgentContractResult
    lead_id: str
    qa_score: int = Field(..., ge=0, le=100)
    qa_scores: QAScores
    hallucination_risk: HallucinationRisk
    recommendation: Recommendation
    qa_notes: list[str] = Field(default_factory=list)


# --------------------------------------------------------------------------- #
# Pipeline contract container (optional, runtime-free)                        #
# --------------------------------------------------------------------------- #


class LeadPipelineContractOutput(BaseModel):
    """Per-lead aggregation of the six agent outputs plus a structural trace.

    This is a **contract container only**. It does not orchestrate
    anything, define execution order, or imply state. Every agent slot
    is optional so callers can populate the container incrementally as
    each agent (or simulator) produces output. The ``trace`` field
    reuses the existing ``TraceEntry`` schema (which already carries the
    Phase 5.1 ``simulated`` and ``model`` flags) so the contract works
    identically for simulated and real runs.
    """

    model_config = ConfigDict(extra="ignore")

    run_id: str
    lead_id: str
    intake: IntakeAgentOutput | None = None
    research: ResearchAgentOutput | None = None
    qualification: QualifierAgentOutput | None = None
    strategy: StrategistAgentOutput | None = None
    email: EmailDrafterAgentOutput | None = None
    qa: QAEvaluatorAgentOutput | None = None
    trace: list[TraceEntry] = Field(default_factory=list)
