"""Single-lead live email draft regeneration schemas.

The request is bounded selected-lead context only. The response carries one
reviewable draft and safe run metadata; it never represents sending email,
CRM updates, or durable state changes.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


EmailRegenerateStatus = Literal[
    "ok",
    "deterministic_fallback",
    "disabled",
    "unavailable",
    "provider_error",
]

EmailRegenerateMode = Literal["live_groq", "deterministic_fallback", "off"]


class EmailRegenerateLeadContext(BaseModel):
    """Bounded selected-lead context accepted by the regenerate endpoint."""

    model_config = ConfigDict(extra="ignore")

    company_name: str = Field(..., min_length=1, max_length=160)
    website: str | None = Field(default=None, max_length=240)
    industry: str | None = Field(default=None, max_length=120)
    country: str | None = Field(default=None, max_length=80)
    employee_count: int | None = Field(default=None, ge=0, le=1_000_000)
    contact_name: str | None = Field(default=None, max_length=120)
    contact_role: str | None = Field(default=None, max_length=160)

    company_summary: str = Field(default="", max_length=1200)
    pain_hypothesis: str = Field(default="", max_length=600)
    sales_angle: str = Field(default="", max_length=600)
    core_message: str = Field(default="", max_length=600)
    personalization_notes: list[str] = Field(default_factory=list, max_length=8)


class EmailRegenerateRequest(BaseModel):
    """Request body for one selected-lead draft regeneration."""

    model_config = ConfigDict(extra="ignore")

    lead: EmailRegenerateLeadContext


class EmailRegenerateResponse(BaseModel):
    """Structured response for one controlled draft regeneration."""

    model_config = ConfigDict(extra="ignore")

    status: EmailRegenerateStatus
    mode: EmailRegenerateMode
    lead_id: str
    draft_only: bool = True

    email_subject: str = ""
    email_body: str = ""
    personalization_notes: list[str] = Field(default_factory=list)

    provider: Literal["groq", "none"] = "none"
    model: str | None = None
    latency: str | None = None
    tokens: int | None = Field(default=None, ge=0)
    estimated_cost: str | None = None

    user_message: str
    warnings: list[str] = Field(default_factory=list)


__all__ = [
    "EmailRegenerateLeadContext",
    "EmailRegenerateRequest",
    "EmailRegenerateResponse",
    "EmailRegenerateStatus",
]
