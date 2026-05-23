"""Block 8.3 — Live Groq single-lead pipeline schemas.

Pydantic v2 contracts for the controlled live Groq pipeline path. The
shape is identical regardless of whether the live run succeeded, so
consumers (tests, future frontend, telemetry) always get a predictable
response.

Hard rules baked into this schema:

* No ``Any`` types in the comparison surface.
* ``LivePipelineComparison`` is importable and testable independently
  from the endpoint and the service.
* Every comparison delta field is ``... | None`` so the shape is valid
  even when the live path failed and there is nothing to compare.
* Text summary fields are short and sanitized at construction time —
  full email bodies, raw provider responses, and full lead payloads
  must never be placed here.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.agents import LeadPipelineContractOutput


class LivePipelineComparison(BaseModel):
    """Lightweight deterministic-vs-live comparison view.

    Every delta field is optional so the schema is valid when the live
    run failed and only the deterministic baseline is available. When
    the live run failed, the service constructs this model with all
    delta fields set to ``None`` and a clear ``comparison_notes``
    string.
    """

    model_config = ConfigDict(extra="ignore")

    fit_score_delta: int | None = None
    priority_changed: bool | None = None
    qa_score_delta: int | None = None
    email_subject_changed: bool | None = None
    risk_level_changed: bool | None = None
    live_summary: str | None = None
    deterministic_summary: str | None = None
    comparison_notes: str = Field(default="")


class LivePipelineResponse(BaseModel):
    """Top-level response shape for the live Groq single-lead endpoint.

    The response always carries:

    * ``run_mode`` — ``"live"`` only when ``live_success=True``;
      otherwise ``"live_failed"``.
    * ``live_success`` — ``True`` only when every agent step in the
      live chain ran via Groq successfully.
    * ``live_model_used`` — Groq model name attempted, regardless of
      whether the live run succeeded.
    * ``fallback_used`` / ``fallback_reason`` — explicit, never silent.
    * ``deterministic_baseline_available`` — ``True`` when the
      deterministic baseline ran in the same request.
    * ``failed_agent`` / ``failure_stage`` / ``error_code`` — set when
      the live path failed mid-pipeline; otherwise ``None``.

    The ``deterministic_result`` field is the deterministic baseline
    pipeline output; ``live_result`` is the live Groq pipeline output
    when (and only when) the live run succeeded.
    """

    model_config = ConfigDict(extra="ignore")

    run_id: str
    lead_id: str
    run_mode: str

    live_success: bool
    live_model_used: str
    fallback_used: bool = False
    fallback_reason: str | None = None
    deterministic_baseline_available: bool = False

    failed_agent: str | None = None
    failure_stage: str | None = None
    error_code: str | None = None

    deterministic_result: LeadPipelineContractOutput | None = None
    live_result: LeadPipelineContractOutput | None = None
    comparison: LivePipelineComparison


__all__ = [
    "LivePipelineComparison",
    "LivePipelineResponse",
]
