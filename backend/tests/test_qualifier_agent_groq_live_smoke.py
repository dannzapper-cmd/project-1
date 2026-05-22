"""Optional live Groq qualifier-agent smoke test (Phase 5.6B).

Skipped by default. Runs ONLY when both of the following environment
variables are set::

    GROQ_API_KEY=<real-key>  RUN_GROQ_LIVE_TESTS=1

To run it::

    GROQ_API_KEY=... RUN_GROQ_LIVE_TESTS=1 \\
        pytest -q backend/tests/test_qualifier_agent_groq_live_smoke.py

The test issues exactly one real Groq completion against
``llama-3.1-8b-instant`` for the single demo lead ``lead_001`` so the
call is cheap. The qualifier accepts either the validated path
(``simulated=False``) or the guardrail/fallback path
(``simulated=True``); both branches are accepted as ``success``.
"""

from __future__ import annotations

import os

import pytest

from app.agents.qualifier_agent import QualifierAgentService
from app.schemas.agents import QualifierAgentInput
from app.services.demo_data_loader import (
    load_demo_company_research,
    load_demo_leads,
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
def test_qualifier_agent_groq_live_smoke_succeeds() -> None:
    """One real, cheap Groq qualification call for ``lead_001``."""

    leads = load_demo_leads()
    research_records = load_demo_company_research()
    lead = next(lead for lead in leads if lead.lead_id == "lead_001")
    research = next(r for r in research_records if r.lead_id == "lead_001")

    groq = GroqModelService(default_model="llama-3.1-8b-instant")
    agent = QualifierAgentService(model_service=groq, use_model_synthesis=True)
    output = agent.run(
        QualifierAgentInput(
            lead=lead,
            research_summary=(
                research.recommended_research_summary or research.company_summary
            ),
            opportunity_signals=[s.signal for s in research.opportunity_signals],
            information_risks=list(research.information_risks),
            run_id="qualifier_agent_groq_live_smoke",
        )
    )

    assert output.result.success is True
    assert output.result.metadata.model
    assert output.result.metadata.agent_name == "qualifier_agent"
    assert output.result.metadata.prompt_version in {
        "qualifier_agent_groq_json_v1",
        "qualifier_agent_groq_json_v1_fallback",
    }
    if output.result.metadata.prompt_version == "qualifier_agent_groq_json_v1":
        assert output.result.metadata.simulated is False
    else:
        assert output.result.metadata.simulated is True

    assert 0 <= output.fit_score <= 100

    blob = " ".join(output.fit_reasons + output.fit_risks).lower()
    for forbidden in (
        "live web research",
        "scraped",
        "fetched from the web",
        "according to my training",
        "based on the internet",
    ):
        assert forbidden not in blob, f"output contains forbidden phrase: {forbidden!r}"
