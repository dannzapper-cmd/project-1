"""Schemas for the Phase 5.9 structured QA-evaluator synthesis.

Leaf, schema-only module. Imports from ``app.schemas.common`` for the
existing ``HallucinationRisk`` and ``Recommendation`` enums and from
Pydantic. Imports nothing from the agent layer, the model service, or
any FastAPI route.

What this module is for:

* ``QAEvaluatorSynthesisPayload`` is the **strict JSON contract** the
  Groq path of :class:`app.agents.qa_evaluator_agent.QAEvaluatorAgentService`
  requires from a real LLM response before that response is allowed to
  influence agent output. The deterministic baseline always runs first;
  the LLM only refines it within the guardrails the agent enforces.
* Every score field is bounded ``0..100`` via explicit Pydantic v2
  ``Field`` constraints; ``strengths`` / ``risks`` / ``required_fixes``
  lists are bounded to keep reviewable size predictable.
* ``hallucination_risk`` and ``recommendation`` use the existing enums
  from ``app.schemas.common``. A ``field_validator`` (Phase 5.9 FIX 3)
  accepts lowercase short forms (``"low|medium|high"`` and
  ``"approve|review|regenerate"``) and maps them via a lookup table to
  the actual enum values (per FIX 2): ``HallucinationRisk`` uses
  title-cased strings (``"Low"``, ``"Medium"``, ``"High"``) and
  ``Recommendation`` uses multi-word values like
  ``"Recommended for approval"``, ``"Review carefully"``,
  ``"Regenerate suggested"``. A bare ``.lower()`` would never match
  either enum and would always fail validation.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas.common import HallucinationRisk, Recommendation

_LOWER_TO_HALLUCINATION_RISK: dict[str, HallucinationRisk] = {
    "low": HallucinationRisk.LOW,
    "medium": HallucinationRisk.MEDIUM,
    "high": HallucinationRisk.HIGH,
}

# Phase 5.9 FIX 2 — the actual Recommendation enum values are
# ``"Recommended for approval"`` / ``"Review carefully"`` /
# ``"Regenerate suggested"`` (NOT ``"approve"`` / ``"review"`` /
# ``"regenerate"``). This lookup maps the LLM-friendly short forms
# (which the system prompt asks for) to the real enum values. We also
# tolerate ``"approved"`` and ``"reject"`` aliases just in case.
_LOWER_TO_RECOMMENDATION: dict[str, Recommendation] = {
    "approve": Recommendation.APPROVE,
    "approved": Recommendation.APPROVE,
    "review": Recommendation.REVIEW,
    "regenerate": Recommendation.REGENERATE,
    "reject": Recommendation.REGENERATE,
}


class QAEvaluatorSynthesisPayload(BaseModel):
    """Strict JSON contract for the Groq QA-evaluator response."""

    model_config = ConfigDict(extra="ignore")

    qa_score: int = Field(..., ge=0, le=100)
    personalization: int = Field(..., ge=0, le=100)
    evidence_coverage: int = Field(..., ge=0, le=100)
    cta_quality: int = Field(..., ge=0, le=100)
    tone_match: int = Field(..., ge=0, le=100)
    hallucination_risk: HallucinationRisk
    recommendation: Recommendation
    strengths: list[str] = Field(default_factory=list, max_length=8)
    risks: list[str] = Field(default_factory=list, max_length=8)
    required_fixes: list[str] = Field(default_factory=list, max_length=8)

    @field_validator("hallucination_risk", mode="before")
    @classmethod
    def normalize_hallucination_risk(cls, v: Any) -> Any:
        """Phase 5.9 FIX 3: accept lowercase short forms and map to the
        actual ``HallucinationRisk`` enum values."""

        if isinstance(v, HallucinationRisk):
            return v
        if isinstance(v, str):
            lowered = v.strip().lower()
            if lowered in _LOWER_TO_HALLUCINATION_RISK:
                return _LOWER_TO_HALLUCINATION_RISK[lowered]
        return v

    @field_validator("recommendation", mode="before")
    @classmethod
    def normalize_recommendation(cls, v: Any) -> Any:
        """Phase 5.9 FIX 3 + FIX 2: accept lowercase short forms and map
        to the actual ``Recommendation`` enum values."""

        if isinstance(v, Recommendation):
            return v
        if isinstance(v, str):
            lowered = v.strip().lower()
            if lowered in _LOWER_TO_RECOMMENDATION:
                return _LOWER_TO_RECOMMENDATION[lowered]
        return v
