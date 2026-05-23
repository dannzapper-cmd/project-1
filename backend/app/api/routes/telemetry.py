"""Read-only telemetry endpoints for demo pipeline runs."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query, status

from app.schemas.telemetry import RunTelemetryDetail, RunTelemetrySummary
from app.services.telemetry_service import get_run_detail, recent_run_summaries

router = APIRouter(prefix="/api/demo/telemetry", tags=["demo-telemetry"])


@router.get("/runs", response_model=list[RunTelemetrySummary])
def get_recent_telemetry_runs(
    limit: int = Query(default=25, ge=1, le=100),
) -> list[RunTelemetrySummary]:
    """Return recent safe run-level telemetry summaries."""

    return recent_run_summaries(limit=limit)


@router.get("/runs/{run_id}", response_model=RunTelemetryDetail)
def get_telemetry_run_detail(run_id: str) -> RunTelemetryDetail:
    """Return safe agent-step telemetry for one recorded pipeline run."""

    detail = get_run_detail(run_id)
    if detail is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Telemetry run '{run_id}' not found",
        )
    return detail
