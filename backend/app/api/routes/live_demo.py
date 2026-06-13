"""Controlled Groq Live Demo Mode HTTP routes."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request, status

from app.core.config import get_settings
from app.core.safety import client_ip
from app.schemas.live_demo import (
    LiveDemoRunRequest,
    LiveDemoRunResponse,
    LiveDemoStatusResponse,
    LiveDemoUnlockRequest,
    LiveDemoUnlockResponse,
)
from app.services.demo_live_mode_service import (
    LIVE_SESSION_HEADER,
    build_live_demo_status,
    demo_live_mode_store,
    run_live_demo,
    unlock_live_demo,
)

router = APIRouter(prefix="/api/demo/live", tags=["demo-live"])


@router.get("/status", response_model=LiveDemoStatusResponse)
def get_live_demo_status(request: Request) -> LiveDemoStatusResponse:
    session_token = request.headers.get(LIVE_SESSION_HEADER, "").strip() or None
    return build_live_demo_status(
        session_token=session_token,
        ip_address=client_ip(request),
    )


@router.post("/unlock", response_model=LiveDemoUnlockResponse)
def post_live_demo_unlock(body: LiveDemoUnlockRequest) -> LiveDemoUnlockResponse:
    response = unlock_live_demo(body.unlock_code)
    if not response.unlocked:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=response.message,
        )
    return response


@router.post("/run", response_model=LiveDemoRunResponse)
def post_live_demo_run(body: LiveDemoRunRequest, request: Request) -> LiveDemoRunResponse:
    settings = get_settings()
    if not body.lead_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one lead_id is required.",
        )
    if len(body.lead_ids) > settings.max_live_leads_per_run:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Too many leads for a live run. "
                f"Maximum is {settings.max_live_leads_per_run}."
            ),
        )
    if not settings.live_mode_enabled:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Live mode is disabled on this backend.",
        )
    if not settings.groq_api_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Groq is not configured on this backend.",
        )

    session_token = request.headers.get(LIVE_SESSION_HEADER, "").strip() or None
    if not demo_live_mode_store.is_valid_session(session_token):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Valid Groq Live demo session required.",
        )
    return run_live_demo(
        lead_ids=body.lead_ids,
        leads=body.leads,
        session_token=session_token,
        ip_address=client_ip(request),
    )
