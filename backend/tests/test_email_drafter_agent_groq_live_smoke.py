"""Optional live Groq email-drafter smoke test (Phase 5.8).

Skipped by default. Runs ONLY when both of the following environment
variables are set::

    GROQ_API_KEY=<real-key>  RUN_GROQ_LIVE_TESTS=1

To run it::

    GROQ_API_KEY=... RUN_GROQ_LIVE_TESTS=1 \\
        pytest -q backend/tests/test_email_drafter_agent_groq_live_smoke.py

One cheap real Groq call against ``llama-3.1-8b-instant`` for the
single demo lead ``lead_001``. Accepts either the validated path
(``simulated=False``) or the deterministic fallback path
(``simulated=True``); both branches are accepted as ``success``. No
email is ever sent.
"""

from __future__ import annotations

import os

import pytest

from app.services.agent_demo_service import (
    build_demo_email_drafter_agent_groq_output,
)

_LIVE_ENABLED: bool = (
    os.environ.get("GROQ_API_KEY") is not None
    and os.environ.get("RUN_GROQ_LIVE_TESTS") == "1"
)


@pytest.mark.skipif(
    not _LIVE_ENABLED,
    reason="GROQ_API_KEY and RUN_GROQ_LIVE_TESTS=1 are both required to run the live smoke test.",
)
def test_email_drafter_agent_groq_live_smoke_succeeds() -> None:
    output = build_demo_email_drafter_agent_groq_output("lead_001")
    assert output.result.success is True
    assert output.result.metadata.agent_name == "email_drafter_agent"
    assert output.result.metadata.prompt_version in {
        "email_drafter_agent_groq_json_v1",
        "email_drafter_agent_groq_json_v1_fallback",
    }
    if output.result.metadata.prompt_version == "email_drafter_agent_groq_json_v1":
        assert output.result.metadata.simulated is False
    else:
        assert output.result.metadata.simulated is True

    assert output.email_subject.strip() != ""
    assert output.email_body.strip() != ""

    blob = " ".join(
        [output.email_subject, output.email_body, *output.personalization_notes]
    ).lower()
    for forbidden in (
        "live web research",
        "we found on your website",
        "according to your website",
        "we saw online",
        "we noticed online",
        "according to news",
        "recent news about",
        "your recent funding",
        "we read that you",
        "this email was sent",
        "delivered via",
        "unsubscribe",
    ):
        assert forbidden not in blob, f"forbidden phrase present: {forbidden!r}"
