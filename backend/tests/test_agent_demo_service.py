"""Unit tests for the Phase 5.5A agent demo wiring service.

Test IDs map 1:1 to the Phase 5.5A spec (D-01 .. D-05).
"""

from __future__ import annotations

import pytest

from app.schemas.agents import ResearchAgentOutput
from app.services.agent_demo_service import (
    build_all_demo_research_agent_outputs,
    build_demo_research_agent_output,
)
from app.services.demo_data_loader import load_demo_leads


def test_d01_returns_research_agent_output_for_lead_001() -> None:
    """D-01: build_demo_research_agent_output("lead_001") returns lead_001."""

    output = build_demo_research_agent_output("lead_001")
    assert isinstance(output, ResearchAgentOutput)
    assert output.lead_id == "lead_001"
    assert output.result.success is True


def test_d02_raises_value_error_for_missing_lead() -> None:
    """D-02: build_demo_research_agent_output("missing_lead") raises ValueError."""

    with pytest.raises(ValueError):
        build_demo_research_agent_output("missing_lead")


def test_d03_returns_one_output_per_demo_lead() -> None:
    """D-03: build_all_demo_research_agent_outputs returns one output
    per demo lead, in the same order."""

    outputs = build_all_demo_research_agent_outputs()
    leads = load_demo_leads()
    assert len(outputs) == len(leads)
    for output, lead in zip(outputs, leads):
        assert output.lead_id == lead.lead_id


def test_d04_every_output_marked_simulated() -> None:
    """D-04: every output has result.metadata.simulated is True."""

    outputs = build_all_demo_research_agent_outputs()
    assert outputs, "expected at least one demo output"
    for output in outputs:
        assert output.result.metadata.simulated is True
        assert output.result.metadata.agent_name == "research_agent"
        assert output.result.metadata.run_mode.value == "simulation"


def test_d05_lead_010_is_handled_safely() -> None:
    """D-05: lead_010 (Orbis Solutions — degraded CSV row, low-evidence
    research) produces a safe ResearchAgentOutput with success=True,
    no exceptions, and a non-empty information_risks list."""

    output = build_demo_research_agent_output("lead_010")
    assert output.lead_id == "lead_010"
    assert output.result.success is True
    assert output.result.error is None
    assert len(output.information_risks) >= 1
    # The agent did not invent signals or pain hypotheses for the
    # degraded record.
    assert output.opportunity_signals == []
    assert output.pain_hypotheses == []
    # And the single demo evidence card was preserved with the
    # DEMO_CONTEXT source.
    assert len(output.evidence_cards) == 1
    assert output.evidence_cards[0].source_type.value == "Demo Context"
