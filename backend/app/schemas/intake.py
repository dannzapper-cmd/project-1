"""Schemas for the Fase 4.3A smart lead intake preview endpoint.

These models describe the request/response contract for
`POST /api/intake/preview`. The endpoint is a *preview-only* layer: it does
not write to the database, call any agent or model, or perform any other
side effect. It accepts imperfect lead input in several text/structured
formats, maps columns to the existing `LeadIn` schema, normalizes values,
flags errors and warnings, assigns a coarse confidence label, and returns a
structured preview.
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.lead import LeadIn


class IntakeOptions(BaseModel):
    """Parser options for the preview pipeline.

    `has_header=False` is not supported in Fase 4.3A; the API layer rejects
    such requests with HTTP 422 via Pydantic validation.
    """

    model_config = ConfigDict(extra="ignore")

    has_header: Literal[True] = True
    delimiter: Literal["auto", ",", "\t"] = "auto"
    generate_missing_lead_ids: bool = True


class IntakePreviewRequest(BaseModel):
    """Request body for `POST /api/intake/preview`."""

    model_config = ConfigDict(extra="ignore")

    input_type: Literal["csv_text", "pasted_table", "records_json", "raw_text"]
    source_name: str | None = None
    content: str | None = None
    records: list[dict[str, Any]] | None = None
    options: IntakeOptions = Field(default_factory=IntakeOptions)


class IntakeIssue(BaseModel):
    """A single issue raised during intake preview."""

    model_config = ConfigDict(extra="ignore")

    severity: Literal["info", "warning", "error"]
    code: str
    message: str
    row_number: int | None = None
    field: str | None = None


class NormalizedLeadRow(BaseModel):
    """One row of the preview, with mapping/normalization applied."""

    model_config = ConfigDict(extra="ignore")

    row_number: int
    lead: LeadIn | None = None
    confidence: Literal["high", "medium", "low"] | None = None
    issues: list[IntakeIssue] = Field(default_factory=list)


class CapabilityMap(BaseModel):
    """Static map of supported and planned-future intake adapters."""

    model_config = ConfigDict(extra="ignore")

    implemented_now: list[str]
    future_adapters: list[str]


class IntakePreviewResponse(BaseModel):
    """Response body for `POST /api/intake/preview`."""

    model_config = ConfigDict(extra="ignore")

    status: Literal["preview_ready", "preview_with_warnings", "preview_blocked"]
    input_type: str
    source_name: str | None = None
    total_rows: int
    valid_rows: int
    rows_with_warnings: int
    failed_rows: int
    mapped_columns: dict[str, str]
    unmapped_columns: list[str]
    normalized_leads: list[NormalizedLeadRow]
    global_issues: list[IntakeIssue]
    capabilities: CapabilityMap
