"""Schemas for the Fase 4.3A smart lead intake preview endpoint."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.schemas.lead import LeadIn


class IntakeOptions(BaseModel):
    model_config = ConfigDict(extra="ignore")

    has_header: bool = True
    delimiter: Literal["auto", ",", "\t"] = "auto"
    generate_missing_lead_ids: bool = True

    @model_validator(mode="after")
    def validate_header_support(self) -> "IntakeOptions":
        if not self.has_header:
            raise ValueError("has_header=False is not supported in Fase 4.3A")
        return self


class IntakePreviewRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    input_type: Literal["csv_text", "pasted_table", "records_json", "raw_text"]
    source_name: str | None = None
    content: str | None = None
    records: list[dict[str, Any]] | None = None
    options: IntakeOptions = Field(default_factory=IntakeOptions)

    @model_validator(mode="after")
    def validate_payload_shape(self) -> "IntakePreviewRequest":
        if self.input_type in {"csv_text", "pasted_table", "raw_text"}:
            if self.content is None:
                raise ValueError("content is required for this input_type")
            if self.records is not None:
                raise ValueError("records must be absent for this input_type")
        if self.input_type == "records_json" and self.records is None:
            raise ValueError("records is required for records_json")
        return self


class IntakeIssue(BaseModel):
    severity: Literal["info", "warning", "error"]
    code: str
    message: str
    row_number: int | None = None
    field: str | None = None


class NormalizedLeadRow(BaseModel):
    row_number: int
    lead: LeadIn | None
    confidence: Literal["high", "medium", "low"] | None = None
    issues: list[IntakeIssue] = Field(default_factory=list)


class CapabilityMap(BaseModel):
    implemented_now: list[str] = Field(
        default_factory=lambda: ["csv_text", "pasted_table", "records_json", "raw_text"]
    )
    future_adapters: list[str] = Field(
        default_factory=lambda: [
            "csv_file",
            "excel_file",
            "pdf_file",
            "image_file",
            "screenshot",
        ]
    )


class IntakePreviewResponse(BaseModel):
    status: Literal["preview_ready", "preview_with_warnings", "preview_blocked"]
    input_type: str
    source_name: str | None
    total_rows: int
    valid_rows: int
    rows_with_warnings: int
    failed_rows: int
    mapped_columns: dict[str, str]
    unmapped_columns: list[str]
    normalized_leads: list[NormalizedLeadRow]
    global_issues: list[IntakeIssue]
    capabilities: CapabilityMap
