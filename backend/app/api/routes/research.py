"""Block 10E — Live Web Research MVP HTTP route.

Single endpoint:

    POST /api/research/live-company

Always returns HTTP 200 with a structured ``LiveResearchResponse``.
Disabled / unavailable / rate-limited / timeout / no-evidence /
provider-error states are encoded in ``status`` and
``user_message`` fields so the frontend has a single, predictable
response shape to consume.

The route never accepts a free-form query — only the safe lead
fields whitelisted in :class:`LiveResearchRequest`. The Exa API key
is read backend-side only and never echoed back into responses or
logs.
"""

from __future__ import annotations

from fastapi import APIRouter

from app.core.logging import get_logger
from app.schemas.live_research import (
    LiveResearchRequest,
    LiveResearchResponse,
)
from app.services.live_research_service import run_live_research


router = APIRouter(prefix="/api/research", tags=["research"])
logger = get_logger(__name__)


@router.post("/live-company", response_model=LiveResearchResponse)
def post_live_company_research(
    request: LiveResearchRequest,
) -> LiveResearchResponse:
    """Manual, single-lead live web research.

    Always returns HTTP 200. The ``status`` field encodes whether
    the request was disabled, unavailable (no API key), rate-limited,
    timed out, returned no usable evidence, or succeeded with cited
    evidence cards. The frontend renders the matching state from
    ``status`` and ``user_message`` rather than from HTTP codes.
    """

    return run_live_research(request)
