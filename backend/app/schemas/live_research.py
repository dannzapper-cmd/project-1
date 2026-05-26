"""Block 10E — Live Web Research MVP schemas.

Public Pydantic v2 schemas for the manual, single-lead live web
research endpoint. The shapes are intentionally narrow and explicit:

- The request only accepts the safe subset of lead fields that the
  backend uses to build a conservative search query. The frontend
  must never submit a free-form query.
- The response always includes ``run_mode="live_research"`` and an
  ``enabled`` flag so the UI can render disabled / unavailable /
  rate-limited / timed-out / no-evidence states without inferring
  state from HTTP error bodies.

Out of scope on purpose: no LLM summarization, no batch shape, no
follow-on actions. Evidence cards repackage Exa's structured
response and never paraphrase or synthesize.
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.common import Confidence


# Stable run-mode label for every response this endpoint produces.
# Pinned as a Literal so a future code path cannot accidentally tag
# a deterministic / Groq response with the same string.
RunModeLiteral = Literal["live_research"]


# Status enum surfaced in ``status``. Frontend renders the matching
# state from this string instead of branching on HTTP codes.
LiveResearchStatus = Literal[
    "ok",
    "disabled",
    "unavailable",
    "insufficient_input",
    "timeout",
    "rate_limited",
    "no_evidence",
    "provider_error",
]


class LiveResearchRequest(BaseModel):
    """Safe lead fields accepted by ``POST /api/research/live-company``.

    The endpoint refuses to construct a query when ``company_name`` is
    missing/empty (Guard C). All other fields are optional context.
    """

    model_config = ConfigDict(extra="ignore", str_strip_whitespace=True)

    company_name: str = Field(..., min_length=1, max_length=200)
    website: str | None = Field(default=None, max_length=300)
    industry: str | None = Field(default=None, max_length=120)
    country: str | None = Field(default=None, max_length=120)
    notes: str | None = Field(default=None, max_length=1_000)


class LiveResearchEvidenceCard(BaseModel):
    """One Exa search result, repackaged for safe display.

    No model-side synthesis: ``snippet`` is taken verbatim from Exa's
    ``highlights`` (or the truncated text it returned) and
    ``why_it_matters`` is a deterministic, template-built explanation
    derived only from the lead context — never from the snippet.
    """

    model_config = ConfigDict(extra="ignore")

    title: str
    url: str
    source_domain: str
    snippet: str
    source_type: Literal["live_web"] = "live_web"
    confidence: Confidence
    why_it_matters: str


class LiveResearchSource(BaseModel):
    """Compact source citation surfaced alongside ``evidence_cards``."""

    model_config = ConfigDict(extra="ignore")

    url: str
    domain: str
    title: str | None = None


class LiveResearchResponse(BaseModel):
    """Full Block 10E response for one manual live-research request."""

    model_config = ConfigDict(extra="ignore")

    provider: Literal["exa", "none"]
    run_mode: RunModeLiteral = "live_research"
    enabled: bool
    status: LiveResearchStatus
    company_name: str
    query_used: str | None
    evidence_cards: list[LiveResearchEvidenceCard] = Field(default_factory=list)
    information_risks: list[str] = Field(default_factory=list)
    confidence: Confidence | None = None
    sources: list[LiveResearchSource] = Field(default_factory=list)
    fetched_at: datetime
    warnings: list[str] = Field(default_factory=list)
    estimated_request_count: int = Field(..., ge=0)
    user_message: str


__all__ = [
    "LiveResearchRequest",
    "LiveResearchResponse",
    "LiveResearchEvidenceCard",
    "LiveResearchSource",
    "LiveResearchStatus",
    "RunModeLiteral",
]
