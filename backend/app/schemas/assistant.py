"""Block 10G — Contextual LLM Lead Assistant schemas.

Public Pydantic v2 schemas for the manual, single-lead assistant
endpoint. The shapes are intentionally narrow:

- The request only accepts a small, structured subset of the lead /
  run context the dashboard already holds (selected lead, profile
  pack, evidence cards, email draft, QA notes, live research
  snippets). Free-form chat history, secrets, API keys, browser
  state, and unrelated leads are NOT accepted (and any extra keys
  are stripped by ``extra="ignore"``).
- The response always returns HTTP 200 with a structured body. The
  ``status`` field encodes whether the assistant ran a live LLM
  call, fell back to a deterministic answer, was disabled / rate
  limited / unavailable, timed out, or refused the request because
  the user's question lacked sufficient context.
- The response never exposes the system prompt, the assembled
  context blob, or any provider API key. ``grounding_summary`` is a
  short human-readable description of which context fields were
  used.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


# Status enum surfaced in ``status``. Frontend renders the matching
# state from this string instead of branching on HTTP codes.
AssistantStatus = Literal[
    "ok",
    "deterministic_fallback",
    "disabled",
    "unavailable",
    "rate_limited",
    "insufficient_context",
    "timeout",
    "provider_error",
    "invalid_question",
]


# Stable mode label surfaced on every response.
AssistantMode = Literal["deterministic", "live_llm", "off"]


class AssistantEvidenceCard(BaseModel):
    """One evidence card supplied as grounding context.

    Mirrors the small subset of fields the frontend already shows in
    the drawer's "Evidence" section. ``description`` may be longer
    than what is forwarded to the model — the service truncates
    aggressively (see ``app.services.assistant_service`` for the
    truncation order).
    """

    model_config = ConfigDict(extra="ignore", str_strip_whitespace=True)

    headline: str = Field(..., max_length=300)
    description: str | None = Field(default=None, max_length=2_000)
    confidence: str | None = Field(default=None, max_length=20)
    source_type: str | None = Field(default=None, max_length=80)


class AssistantLiveResearchSnippet(BaseModel):
    """One optional live-research snippet from Block 10E results.

    The assistant must NEVER trigger live research itself; this field
    is only populated by the frontend when Block 10E results are
    already cached in React state for the selected lead.
    """

    model_config = ConfigDict(extra="ignore", str_strip_whitespace=True)

    title: str | None = Field(default=None, max_length=300)
    source_domain: str | None = Field(default=None, max_length=200)
    snippet: str | None = Field(default=None, max_length=1_000)


class AssistantQAContext(BaseModel):
    """Compact QA score context."""

    model_config = ConfigDict(extra="ignore")

    qa_score: int | None = Field(default=None, ge=0, le=100)
    hallucination_risk: str | None = Field(default=None, max_length=20)
    recommendation: str | None = Field(default=None, max_length=80)
    notes: list[str] = Field(default_factory=list, max_length=10)


class AssistantLeadContext(BaseModel):
    """Selected-lead context the assistant is allowed to reason over.

    Only the small subset of fields already visible in the dashboard
    is accepted. Long free-form fields (email_body, QA notes,
    snippets, evidence descriptions) are truncated downstream by the
    service before any context is sent to the model.
    """

    model_config = ConfigDict(extra="ignore", str_strip_whitespace=True)

    company_name: str | None = Field(default=None, max_length=200)
    industry: str | None = Field(default=None, max_length=120)
    country: str | None = Field(default=None, max_length=120)
    website: str | None = Field(default=None, max_length=300)
    employees: str | None = Field(default=None, max_length=80)
    contact_role: str | None = Field(default=None, max_length=120)

    fit_score: int | None = Field(default=None, ge=0, le=100)
    priority: str | None = Field(default=None, max_length=20)
    fit_reasons: list[str] = Field(default_factory=list, max_length=10)
    fit_risks: list[str] = Field(default_factory=list, max_length=10)

    company_summary: str | None = Field(default=None, max_length=1_500)
    pain_hypothesis: str | None = Field(default=None, max_length=600)
    pain_confidence: str | None = Field(default=None, max_length=20)
    sales_angle: str | None = Field(default=None, max_length=600)
    core_message: str | None = Field(default=None, max_length=400)
    likely_objection: str | None = Field(default=None, max_length=400)

    email_subject: str | None = Field(default=None, max_length=300)
    email_body: str | None = Field(default=None, max_length=4_000)

    intake_warnings: list[str] = Field(default_factory=list, max_length=10)
    low_evidence: bool | None = None
    missing_fields: list[str] = Field(default_factory=list, max_length=20)

    evidence_cards: list[AssistantEvidenceCard] = Field(
        default_factory=list, max_length=12
    )
    qa: AssistantQAContext | None = None

    profile_pack_name: str | None = Field(default=None, max_length=120)
    profile_pack_focus: str | None = Field(default=None, max_length=400)


class AssistantRequest(BaseModel):
    """Request body for ``POST /api/assistant/lead-question``.

    ``question`` is required, capped, and trimmed. ``lead`` is
    required so the assistant always has at least minimal grounding
    context. ``live_research`` is optional and only forwarded when
    the frontend already has Block 10E results cached for the lead.
    """

    model_config = ConfigDict(extra="ignore", str_strip_whitespace=True)

    question: str = Field(..., min_length=1, max_length=2_000)
    lead: AssistantLeadContext
    live_research: list[AssistantLiveResearchSnippet] = Field(
        default_factory=list, max_length=5
    )
    run_mode: str | None = Field(default=None, max_length=60)


class AssistantResponse(BaseModel):
    """Structured response for one assistant request.

    Never exposes the system prompt or the full assembled context.
    ``grounding_summary`` is a short, human-readable description of
    which lead-context fields the answer was grounded in.
    """

    model_config = ConfigDict(extra="ignore")

    status: AssistantStatus
    mode: AssistantMode
    answer: str
    grounding_summary: str
    used_context_fields: list[str] = Field(default_factory=list)
    unsupported_claims_blocked: bool = False
    context_truncated: bool = False
    warnings: list[str] = Field(default_factory=list)
    provider: str | None = None
    model: str | None = None
    estimated_tokens: int | None = Field(default=None, ge=0)
    estimated_cost_usd: float | None = Field(default=None, ge=0.0)
    user_message: str


__all__ = [
    "AssistantStatus",
    "AssistantMode",
    "AssistantEvidenceCard",
    "AssistantLiveResearchSnippet",
    "AssistantQAContext",
    "AssistantLeadContext",
    "AssistantRequest",
    "AssistantResponse",
]
