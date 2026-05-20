"""QA / evaluation schemas."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.common import Confidence, EvidenceSource, HallucinationRisk, Recommendation


class QAScores(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    personalization: int = Field(..., ge=0, le=100)
    evidence_coverage: int = Field(..., ge=0, le=100)
    cta_quality: int = Field(..., ge=0, le=100)
    tone_match: int = Field(..., ge=0, le=100)
    hallucination_risk: HallucinationRisk
    recommendation: Recommendation


class EvidenceCard(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    headline: str
    source_type: EvidenceSource
    description: str
    confidence: Confidence
