"""Optional live Groq research-agent smoke test (Phase 5.5C).

Skipped by default. Runs ONLY when both of the following environment
variables are set::

    GROQ_API_KEY=<real-key>  RUN_GROQ_LIVE_TESTS=1

To run it::

    GROQ_API_KEY=... RUN_GROQ_LIVE_TESTS=1 \\
        pytest -q backend/tests/test_research_agent_groq_live_smoke.py

The test issues exactly one real Groq completion against
``llama-3.1-8b-instant`` for the single demo lead ``lead_001`` so the
call is cheap. The Groq path falls back to the deterministic Phase 5.5A
output if validation fails — both branches are accepted as ``success``,
but the deterministic branch records a fallback risk note we still
assert ``no live web research`` claims in any text-bearing field.
"""

from __future__ import annotations

import os

import pytest

from app.agents.research_agent import ResearchAgentService
from app.schemas.agents import ResearchAgentInput
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
def test_research_agent_groq_live_smoke_succeeds() -> None:
    """One real, cheap Groq research synthesis call for ``lead_001``."""

    leads = load_demo_leads()
    research_records = load_demo_company_research()
    lead = next(lead for lead in leads if lead.lead_id == "lead_001")
    research = next(r for r in research_records if r.lead_id == "lead_001")

    groq = GroqModelService(default_model="llama-3.1-8b-instant")
    agent = ResearchAgentService(model_service=groq, use_model_synthesis=True)
    output = agent.run(
        ResearchAgentInput(
            lead=lead,
            run_id="research_agent_groq_live_smoke",
            available_context=research.model_dump(),
        )
    )

    assert output.result.success is True
    assert output.result.metadata.model  # non-empty
    assert output.result.metadata.agent_name == "research_agent"
    # The metadata.model must be the Groq model we configured; the
    # prompt_version is one of the two Groq paths (valid synthesis or
    # validation fallback).
    assert output.result.metadata.prompt_version in {
        "research_agent_groq_json_v1",
        "research_agent_groq_json_v1_fallback",
    }
    # If the JSON parsed cleanly, simulated must be False (real data).
    # If the fallback ran, simulated must be True (deterministic data
    # origin even though Groq was called) — per Phase 5.5C FIX 1.
    if output.result.metadata.prompt_version == "research_agent_groq_json_v1":
        assert output.result.metadata.simulated is False
    else:
        assert output.result.metadata.simulated is True

    assert output.company_summary.strip() != ""

    # Honesty: no claim of live web research anywhere in the text.
    blob = " ".join(
        [
            output.company_summary,
            " ".join(output.opportunity_signals),
            " ".join(output.pain_hypotheses),
            " ".join(output.information_risks),
            " ".join(card.description for card in output.evidence_cards),
            " ".join(card.headline for card in output.evidence_cards),
        ]
    ).lower()
    for forbidden in (
        "live web research",
        "scraped",
        "fetched from the web",
        "according to my training",
        "based on the internet",
    ):
        assert forbidden not in blob, f"output contains forbidden phrase: {forbidden!r}"
