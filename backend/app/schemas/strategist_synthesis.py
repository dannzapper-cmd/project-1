"""Schemas for the Phase 5.7 structured strategist synthesis.

Leaf, schema-only module. Imports from ``app.schemas.common`` for the
existing ``Confidence`` enum and from Pydantic. Imports nothing from the
agent layer, the model service, or any FastAPI route.

What this module is for:

* ``StrategistSynthesisPayload`` is the **strict JSON contract** the
  Groq path of :class:`app.agents.strategist_agent.StrategistAgentService`
  requires from a real LLM response before that response is allowed to
  influence agent output. The deterministic baseline always runs first;
  the LLM only refines it within the guardrails the agent enforces.
* All required text fields use ``Field(..., min_length=1)`` so an LLM
  that omits or empties a field is rejected at the schema layer.
* ``personalization_notes`` is bounded by both ``min_length=1`` (per
  Phase 5.7 FIX 4 — so an empty list is rejected, not silently
  accepted) and ``max_length=5`` (so verbose outputs are bounded).
* A ``field_validator`` normalises lowercase ``"high|medium|low"`` (the
  spelling the strategist system prompt asks for) into the existing
  ``Confidence`` enum values (Phase 5.7 FIX 1). The validator follows
  the FIX 1 ``.lower()`` intent and then maps via a lookup table —
  returning a bare ``.lower()`` string would not match the
  title-cased ``Confidence`` enum values and would always fail
  validation.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas.common import Confidence

_LOWER_TO_CONFIDENCE: dict[str, Confidence] = {
    "high": Confidence.HIGH,
    "medium": Confidence.MEDIUM,
    "low": Confidence.LOW,
}


class StrategistSynthesisPayload(BaseModel):
    """Strict JSON contract for the Groq strategist-synthesis response."""

    model_config = ConfigDict(extra="ignore")

    pain_hypothesis: str = Field(..., min_length=1)
    pain_confidence: Confidence = Confidence.MEDIUM
    sales_angle: str = Field(..., min_length=1)
    core_message: str = Field(..., min_length=1)
    likely_objection: str = Field(..., min_length=1)
    personalization_notes: list[str] = Field(
        default_factory=list, min_length=1, max_length=5
    )

    @field_validator("pain_confidence", mode="before")
    @classmethod
    def normalize_confidence(cls, v: Any) -> Any:
        """Phase 5.7 FIX 1: accept lowercase ``"high|medium|low"`` from
        the LLM and map it to the existing ``Confidence`` enum.

        FIX 1 specifies ``.lower()``; we apply ``.lower()`` and then
        look up the result in a small dict so the validator both
        respects the intent of the fix AND produces a value the
        Confidence enum constructor can accept (it expects the
        capitalised spellings ``"High"`` / ``"Medium"`` / ``"Low"``).
        Any other shape passes through so Pydantic's normal enum
        validator rejects it with the standard error.
        """

        if isinstance(v, Confidence):
            return v
        if isinstance(v, str):
            lowered = v.strip().lower()
            if lowered in _LOWER_TO_CONFIDENCE:
                return _LOWER_TO_CONFIDENCE[lowered]
        return v
