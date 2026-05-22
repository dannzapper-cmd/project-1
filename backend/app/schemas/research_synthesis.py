"""Schemas for the Phase 5.5C structured research synthesis.

A leaf, schema-only module. Imports from ``app.schemas.common`` (for the
existing ``Confidence`` enum) and from Pydantic; nothing else. It must
NOT import ``app.agents.research_agent``, ``app.services.model_service``,
or any FastAPI route module.

What this module is for:

* ``ResearchSynthesisEvidence`` and ``ResearchSynthesisPayload`` describe
  the **strict JSON contract** that the Groq path of
  :class:`app.agents.research_agent.ResearchAgentService` requires from a
  real LLM response before that response is allowed to influence agent
  output.
* The constraints (``min_length=1`` on the summary; ``max_length`` caps
  on every list) are explicit Pydantic v2 ``Field`` constraints — they
  bound model output to a reviewable size and prevent the agent from
  silently consuming over-eager LLM completions.

No field requires live/public source URLs. The model is only ever
allowed to summarise and structure the demo context the agent already
holds; the agent layer enforces source-type honesty separately.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas.common import Confidence


def _normalize_confidence(value: Any) -> Any:
    """Map ``"low" / "medium" / "high"`` (case-insensitive) to the enum
    values used by :class:`app.schemas.common.Confidence`.

    The Phase 5.5C system prompt asks the model for ``"low|medium|high"``
    (lowercase) for ergonomics; ``Confidence`` itself uses ``"High" /
    "Medium" / "Low"`` (title-case). This pre-validator bridges the two
    so the LLM contract is not coupled to the internal enum spelling
    and Pydantic still rejects anything else.
    """

    if isinstance(value, Confidence):
        return value
    if isinstance(value, str):
        lookup = {
            "low": Confidence.LOW,
            "medium": Confidence.MEDIUM,
            "high": Confidence.HIGH,
        }
        candidate = lookup.get(value.strip().lower())
        if candidate is not None:
            return candidate
    return value


class ResearchSynthesisEvidence(BaseModel):
    """A single evidence entry inside a :class:`ResearchSynthesisPayload`."""

    model_config = ConfigDict(extra="ignore")

    headline: str = Field(..., min_length=1)
    description: str = Field(..., min_length=1)
    confidence: Confidence = Confidence.MEDIUM

    @field_validator("confidence", mode="before")
    @classmethod
    def _coerce_confidence(cls, value: Any) -> Any:
        return _normalize_confidence(value)


class ResearchSynthesisPayload(BaseModel):
    """Strict JSON contract for the Groq research-synthesis response.

    The list ``max_length`` caps are deliberately small (Phase 5.5C
    FIX 4) so a model that returns sprawling output is rejected at the
    schema layer rather than silently absorbed.
    """

    model_config = ConfigDict(extra="ignore")

    company_summary: str = Field(..., min_length=1)
    opportunity_signals: list[str] = Field(default_factory=list, max_length=5)
    pain_hypotheses: list[str] = Field(default_factory=list, max_length=5)
    evidence_cards: list[ResearchSynthesisEvidence] = Field(
        default_factory=list, max_length=5
    )
    information_risks: list[str] = Field(default_factory=list, max_length=10)
    # Default protects against omission by smaller models; the agent
    # still records the confidence the LLM chose if it supplied one.
    confidence: Confidence = Confidence.MEDIUM

    @field_validator("confidence", mode="before")
    @classmethod
    def _coerce_confidence(cls, value: Any) -> Any:
        return _normalize_confidence(value)
