"""Unit tests for the Phase 5.7 Strategist Agent demo wiring."""

from __future__ import annotations

import pytest

from app.schemas.agents import StrategistAgentOutput
from app.services.agent_demo_service import (
    build_all_demo_strategist_agent_outputs,
    build_demo_strategist_agent_output,
)
from app.services.demo_data_loader import load_demo_leads


def test_d01_returns_strategist_output_for_lead_001() -> None:
    """D-01: build_demo_strategist_agent_output("lead_001") returns lead_001."""

    output = build_demo_strategist_agent_output("lead_001")
    assert isinstance(output, StrategistAgentOutput)
    assert output.lead_id == "lead_001"
    assert output.result.success is True


def test_d02_raises_value_error_for_missing_lead() -> None:
    """D-02: build_demo_strategist_agent_output("missing_lead") raises ValueError."""

    with pytest.raises(ValueError):
        build_demo_strategist_agent_output("missing_lead")


def test_d03_returns_one_output_per_demo_lead() -> None:
    """D-03: build_all_demo_strategist_agent_outputs returns one output per
    demo lead, in CSV row order."""

    outputs = build_all_demo_strategist_agent_outputs()
    leads = load_demo_leads()
    assert len(outputs) == len(leads)
    for output, lead in zip(outputs, leads):
        assert output.lead_id == lead.lead_id


def test_d04_every_output_has_strategist_metadata() -> None:
    """D-04: every output has result.metadata.agent_name == "strategist_agent"."""

    outputs = build_all_demo_strategist_agent_outputs()
    assert outputs, "expected at least one demo output"
    for output in outputs:
        assert output.result.metadata.agent_name == "strategist_agent"
        assert output.result.metadata.simulated is True
        assert output.result.metadata.run_mode.value == "simulation"


def test_d05_lead_010_is_handled_safely_with_conservative_strategy() -> None:
    """D-05: lead_010 (degraded) is handled safely with a conservative
    discovery-oriented strategy."""

    output = build_demo_strategist_agent_output("lead_010")
    assert output.lead_id == "lead_010"
    assert output.result.success is True
    # LOW priority cautious angle on a degraded lead.
    lowered = output.sales_angle.lower()
    assert any(
        keyword in lowered
        for keyword in ("cautious", "discovery", "validate")
    )
    assert 2 <= len(output.personalization_notes) <= 5
