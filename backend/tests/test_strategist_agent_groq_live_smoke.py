"""Optional live Groq strategist-agent smoke test (Phase 5.7).

Skipped by default. Runs ONLY when both of the following environment
variables are set::

    GROQ_API_KEY=<real-key>  RUN_GROQ_LIVE_TESTS=1

To run it::

    GROQ_API_KEY=... RUN_GROQ_LIVE_TESTS=1 \\
        pytest -q backend/tests/test_strategist_agent_groq_live_smoke.py

One cheap real Groq call against ``llama-3.1-8b-instant`` for the
single demo lead ``lead_001``. Accepts either the validated path
(``simulated=False``) or the deterministic fallback path
(``simulated=True``); both branches are accepted as ``success``.
"""

from __future__ import annotations

import os

import pytest

from app.services.agent_demo_service import (
    build_demo_strategist_agent_groq_output,
)

_LIVE_ENABLED: bool = (
    os.environ.get("GROQ_API_KEY") is not None
    and os.environ.get("RUN_GROQ_LIVE_TESTS") == "1"
)


@pytest.mark.skipif(
    not _LIVE_ENABLED,
    reason="GROQ_API_KEY and RUN_GROQ_LIVE_TESTS=1 are both required to run the live smoke test.",
)
def test_strategist_agent_groq_live_smoke_succeeds() -> None:
    output = build_demo_strategist_agent_groq_output("lead_001")
    assert output.result.success is True
    assert output.result.metadata.agent_name == "strategist_agent"
    assert output.result.metadata.prompt_version in {
        "strategist_agent_groq_json_v1",
        "strategist_agent_groq_json_v1_fallback",
    }
    if output.result.metadata.prompt_version == "strategist_agent_groq_json_v1":
        assert output.result.metadata.simulated is False
        assert output.result.metadata.model  # non-empty
    else:
        assert output.result.metadata.simulated is True

    assert output.pain_hypothesis.strip() != ""
    assert output.core_message.strip() != ""

    blob = " ".join(
        [
            output.pain_hypothesis,
            output.sales_angle,
            output.core_message,
            output.likely_objection,
            " ".join(output.personalization_notes),
        ]
    ).lower()
    for forbidden in (
        "live web research",
        "scraped",
        "we found online",
        "i found online",
        "according to your website",
        "recent news about",
        "your recent funding",
    ):
        assert forbidden not in blob, f"forbidden phrase present: {forbidden!r}"
