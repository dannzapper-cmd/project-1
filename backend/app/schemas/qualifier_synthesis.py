"""Schemas for the Phase 5.6B structured qualifier synthesis.

Leaf, schema-only module. Imports from ``app.schemas.common`` for the
existing ``Priority`` and ``Confidence`` enums and from Pydantic.
Imports nothing from the agent layer, the model service, or any
FastAPI route.

What this module is for:

* ``QualifierSynthesisPayload`` is the **strict JSON contract** the
  Groq path of :class:`app.agents.qualifier_agent.QualifierAgentService`
  requires from a real LLM response before that response is allowed to
  influence agent output. The deterministic ``icp_scoring`` baseline
  always runs first; the LLM only refines it within the guardrails the
  agent enforces.
* The list ``max_length`` caps and the bounded-integer
  ``Field(..., ge=0, le=100)`` on ``fit_score`` are explicit Pydantic
  v2 constraints — they bound model output to a reviewable size and
  reject obviously-out-of-range values at the schema layer.
* A ``field_validator`` normalises lowercase ``"high|medium|low"`` (the
  spelling requested in the qualifier system prompt) into the existing
  ``Priority`` / ``Confidence`` enum values without coupling the LLM
  contract to the title-case spelling used elsewhere in the codebase
  (Phase 5.6B FIX 2).
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas.common import Confidence, Priority


class QualifierSynthesisPayload(BaseModel):
    """Strict JSON contract for the Groq qualification-synthesis response."""

    model_config = ConfigDict(extra="ignore")

    fit_score: int = Field(..., ge=0, le=100)
    priority: Priority
    fit_reasons: list[str] = Field(default_factory=list, max_length=8)
    fit_risks: list[str] = Field(default_factory=list, max_length=8)
    confidence: Confidence = Confidence.MEDIUM

    @field_validator("priority", "confidence", mode="before")
    @classmethod
    def normalize_string_enums(cls, v: Any) -> Any:
        """Phase 5.6B FIX 2: normalise lowercase string variants from
        the LLM into the existing enum spellings.

        ``Priority.HIGH.value == "High"`` and
        ``Confidence.HIGH.value == "High"``; the qualifier system
        prompt asks for ``"high|medium|low"`` for ergonomic reasons.
        This pre-validator title-cases incoming strings so the enum
        constructor accepts them; any other shape (already-an-enum,
        ``None``, etc.) passes through unchanged so the regular
        Pydantic v2 enum validator can reject it.
        """

        if isinstance(v, str):
            stripped = v.strip()
            if stripped == "":
                return v
            return stripped[:1].upper() + stripped[1:].lower()
        return v
