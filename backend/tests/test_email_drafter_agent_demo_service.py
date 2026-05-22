"""Unit tests for the Phase 5.8 Email Drafter Agent demo wiring."""

from __future__ import annotations

import pytest

from app.schemas.agents import EmailDrafterAgentOutput
from app.services.agent_demo_service import (
    build_all_demo_email_drafter_agent_outputs,
    build_demo_email_drafter_agent_output,
)
from app.services.demo_data_loader import load_demo_leads


def test_d01_returns_output_for_lead_001() -> None:
    """D-01: build_demo_email_drafter_agent_output("lead_001") returns lead_001."""

    output = build_demo_email_drafter_agent_output("lead_001")
    assert isinstance(output, EmailDrafterAgentOutput)
    assert output.lead_id == "lead_001"
    assert output.result.success is True


def test_d02_raises_value_error_for_missing_lead() -> None:
    """D-02: build_demo_email_drafter_agent_output("missing_lead") raises."""

    with pytest.raises(ValueError):
        build_demo_email_drafter_agent_output("missing_lead")


def test_d03_returns_one_output_per_demo_lead() -> None:
    """D-03: build_all_demo_email_drafter_agent_outputs returns one
    output per demo lead, in CSV row order."""

    outputs = build_all_demo_email_drafter_agent_outputs()
    leads = load_demo_leads()
    assert len(outputs) == len(leads)
    for output, lead in zip(outputs, leads):
        assert output.lead_id == lead.lead_id


def test_d04_every_output_has_email_drafter_metadata() -> None:
    """D-04: every output has agent_name == "email_drafter_agent"."""

    outputs = build_all_demo_email_drafter_agent_outputs()
    assert outputs, "expected at least one demo output"
    for output in outputs:
        assert output.result.metadata.agent_name == "email_drafter_agent"
        assert output.result.metadata.simulated is True
        assert output.result.metadata.run_mode.value == "simulation"


def test_d05_lead_010_is_handled_safely_with_conservative_draft() -> None:
    """D-05: lead_010 (degraded) is handled safely with a conservative
    / exploratory draft (LOW confidence; a limited-context note)."""

    output = build_demo_email_drafter_agent_output("lead_010")
    assert output.lead_id == "lead_010"
    assert output.result.success is True
    assert output.email_subject.strip() != ""
    assert output.email_body.strip() != ""
    # Sales draft for a degraded lead should not get HIGH confidence.
    assert output.confidence in {"Low", "Medium"} or output.confidence.value in {
        "Low",
        "Medium",
    }
    # The deterministic baseline appends the limited-context note when
    # the upstream context is thin.
    assert any(
        "exploratory" in note.lower() for note in output.personalization_notes
    )


def test_d06_draft_body_does_not_contain_live_research_claims() -> None:
    """D-06: every demo draft body avoids forbidden live-research phrases."""

    outputs = build_all_demo_email_drafter_agent_outputs()
    for output in outputs:
        body_lower = output.email_body.lower()
        for forbidden in (
            "we found on your website",
            "according to your website",
            "we saw online",
            "we noticed online",
            "according to news",
            "recent news about",
            "your recent funding",
            "we read that you",
            "we found online",
            "i found online",
        ):
            assert forbidden not in body_lower, (
                f"{output.lead_id}: forbidden phrase present: {forbidden!r}"
            )
