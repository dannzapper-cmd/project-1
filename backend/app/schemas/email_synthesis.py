"""Schemas for the Phase 5.8 structured email-draft synthesis.

Leaf, schema-only module. Imports from ``app.schemas.common`` for the
existing ``Confidence`` enum and from Pydantic. Imports nothing from
the agent layer, the model service, or any FastAPI route.

What this module is for:

* ``EmailDraftSynthesisPayload`` is the **strict JSON contract** the
  Groq path of :class:`app.agents.email_drafter_agent.EmailDrafterAgentService`
  requires from a real LLM response before that response is allowed to
  influence agent output. The deterministic baseline always runs first;
  the LLM only refines it within the guardrails the agent enforces.
* Length bounds match the prompt: subject 1–120 chars; body 50–1800
  chars; ``personalization_notes`` 1–5 entries.
* A ``field_validator`` normalises lowercase ``"high|medium|low"`` (the
  spelling the email-drafter system prompt asks for) into the existing
  ``Confidence`` enum values (Phase 5.8 FIX 1). The validator follows
  FIX 1's ``.lower()`` intent and then maps via a small lookup table —
  returning a bare ``.lower()`` string would not match the title-cased
  enum values and would always fail validation.
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


class EmailDraftSynthesisPayload(BaseModel):
    """Strict JSON contract for the Groq email-drafter response."""

    model_config = ConfigDict(extra="ignore")

    email_subject: str = Field(..., min_length=1, max_length=120)
    email_body: str = Field(..., min_length=50, max_length=1800)
    personalization_notes: list[str] = Field(
        default_factory=list, min_length=1, max_length=5
    )
    confidence: Confidence = Confidence.MEDIUM

    @field_validator("confidence", mode="before")
    @classmethod
    def normalize_confidence(cls, v: Any) -> Any:
        """Phase 5.8 FIX 1: accept lowercase ``"high|medium|low"`` from
        the LLM and map it to the existing ``Confidence`` enum.

        FIX 1 specifies ``.lower()``; we apply ``.lower()`` and then
        look up the result in a small dict so the validator both
        respects the intent of the fix AND produces a value the
        ``Confidence`` enum constructor can accept (it expects the
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
