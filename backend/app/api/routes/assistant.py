"""Block 10G — Contextual LLM Lead Assistant HTTP route.

Single endpoint:

    POST /api/assistant/lead-question

Always returns HTTP 200 with a structured :class:`AssistantResponse`.
Disabled / unavailable / rate-limited / timeout / insufficient-context
/ provider-error / invalid-question states are encoded in ``status``
so the frontend has a single, predictable response shape to consume.

The route never accepts API keys, secrets, browser cookies, or full
batch data. Only the small structured lead context allowed by
:class:`AssistantRequest` is forwarded.
"""

from __future__ import annotations

from fastapi import APIRouter, Request

from app.core.logging import get_logger
from app.schemas.assistant import AssistantRequest, AssistantResponse
from app.services.assistant_service import answer_lead_question


router = APIRouter(prefix="/api/assistant", tags=["assistant"])
logger = get_logger(__name__)


def _client_ip(request: Request) -> str:
    """Best-effort client IP for per-IP throttling.

    The deployment may sit behind a single reverse proxy (Render),
    so we prefer ``X-Forwarded-For`` when present (first hop only)
    and fall back to the direct client address. We never trust the
    value for anything security-critical — it is used only to
    cluster recent requests for the per-session throttle.
    """

    header = request.headers.get("x-forwarded-for")
    if header:
        first = header.split(",")[0].strip()
        if first:
            return first
    if request.client and request.client.host:
        return request.client.host
    return ""


@router.post("/lead-question", response_model=AssistantResponse)
def post_lead_question(
    payload: AssistantRequest, request: Request
) -> AssistantResponse:
    """Answer one grounded question about the selected lead.

    Always returns HTTP 200. ``status`` encodes whether the response
    came from the live LLM, the disabled / unavailable / rate-limited
    fallback, a timeout, or a refusal because the question was
    out of scope.
    """

    return answer_lead_question(payload, client_ip=_client_ip(request))
