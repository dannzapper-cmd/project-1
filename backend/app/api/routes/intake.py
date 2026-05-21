"""Smart lead intake preview endpoint (Fase 4.3A)."""

from __future__ import annotations

from fastapi import APIRouter

from app.schemas.intake import IntakePreviewRequest, IntakePreviewResponse
from app.services.intake_normalizer import build_intake_preview

router = APIRouter(tags=["intake"])


@router.post("/preview", response_model=IntakePreviewResponse)
def preview_intake(request: IntakePreviewRequest) -> IntakePreviewResponse:
    return build_intake_preview(request)
