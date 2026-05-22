"""Optional live Groq smoke test (Phase 5.5B).

Skipped by default. Runs ONLY when both of the following environment
variables are set::

    GROQ_API_KEY=<real-key>  RUN_GROQ_LIVE_TESTS=1

To run it::

    GROQ_API_KEY=... RUN_GROQ_LIVE_TESTS=1 \\
        pytest -q backend/tests/test_groq_live_smoke.py

The test issues exactly one real Groq completion against
``llama-3.1-8b-instant`` with ``max_tokens=32`` so the call is cheap.
"""

from __future__ import annotations

import os

import pytest

from app.schemas.model import (
    ModelConfig,
    ModelMessage,
    ModelProvider,
    ModelRequest,
    ModelRole,
)
from app.services.model_service import GroqModelService

_LIVE_ENABLED: bool = (
    os.environ.get("GROQ_API_KEY") is not None
    and os.environ.get("RUN_GROQ_LIVE_TESTS") == "1"
)


@pytest.mark.skipif(
    not _LIVE_ENABLED,
    reason="GROQ_API_KEY and RUN_GROQ_LIVE_TESTS=1 are both required to run the live smoke test.",
)
def test_groq_live_smoke_returns_expected_phrase() -> None:
    """One real, cheap Groq call. Asserts the response content contains
    the expected phrase, normalised per Phase 5.5B FIX 2 to tolerate
    punctuation and casing variations the model may produce."""

    service = GroqModelService(default_model="llama-3.1-8b-instant")
    request = ModelRequest(
        request_id="groq_live_smoke",
        messages=[
            ModelMessage(
                role=ModelRole.USER,
                content="Return exactly: LeadForge Groq check OK",
            )
        ],
        config=ModelConfig(
            provider=ModelProvider.GROQ,
            model_name="llama-3.1-8b-instant",
            max_tokens=32,
        ),
    )

    response = service.complete(request)

    # FIX 2: normalise before asserting — the model may wrap the phrase
    # in quotes or add a trailing period.
    assert "leadforge groq check ok" in response.content.lower().strip()
    assert response.provider == ModelProvider.GROQ
    assert response.simulated is False
    assert response.latency.endswith("ms")
