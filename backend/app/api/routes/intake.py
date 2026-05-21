"""Smart lead intake endpoints (Fase 4.3A).

Currently exposes a single product endpoint, ``POST /api/intake/preview``,
which accepts imperfect lead input in several text/structured formats and
returns a normalized preview. This is *not* a demo endpoint; it lives
under ``/api/intake`` so the eventual production import flow can build on
the same contract.

The endpoint is preview-only: no DB writes, no agent invocation, no LLM
calls, no external I/O.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from app.core.logging import get_logger
from app.schemas.intake import IntakePreviewRequest, IntakePreviewResponse
from app.services.intake_normalizer import build_preview

router = APIRouter(prefix="/api/intake", tags=["intake"])
logger = get_logger(__name__)


@router.post("/preview", response_model=IntakePreviewResponse)
def preview_intake(request: IntakePreviewRequest) -> IntakePreviewResponse:
    """Return a normalized preview for the submitted intake payload."""

    if request.input_type in {"csv_text", "pasted_table", "raw_text"}:
        if request.content is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=(
                    f"'content' is required when input_type is '{request.input_type}'."
                ),
            )

    if request.input_type == "records_json":
        if request.records is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="'records' is required when input_type is 'records_json'.",
            )

    return build_preview(request)
