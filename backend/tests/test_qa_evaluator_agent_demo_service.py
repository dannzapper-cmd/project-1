"""Unit tests for the Phase 5.9 QA Evaluator Agent demo wiring."""

from __future__ import annotations

import pytest

from app.schemas.agents import QAEvaluatorAgentOutput
from app.services.agent_demo_service import (
    build_all_demo_qa_evaluator_agent_outputs,
    build_demo_qa_evaluator_agent_output,
)
from app.services.demo_data_loader import load_demo_leads


def test_d01_returns_output_for_lead_001() -> None:
    """D-01: build_demo_qa_evaluator_agent_output("lead_001") returns lead_001."""

    output = build_demo_qa_evaluator_agent_output("lead_001")
    assert isinstance(output, QAEvaluatorAgentOutput)
    assert output.lead_id == "lead_001"
    assert output.result.success is True


def test_d02_raises_value_error_for_missing_lead() -> None:
    """D-02: build_demo_qa_evaluator_agent_output("missing_lead") raises."""

    with pytest.raises(ValueError):
        build_demo_qa_evaluator_agent_output("missing_lead")


def test_d03_returns_one_output_per_demo_lead() -> None:
    """D-03: build_all_demo_qa_evaluator_agent_outputs returns one
    output per demo lead, in CSV row order."""

    outputs = build_all_demo_qa_evaluator_agent_outputs()
    leads = load_demo_leads()
    assert len(outputs) == len(leads)
    for output, lead in zip(outputs, leads):
        assert output.lead_id == lead.lead_id


def test_d04_every_output_has_qa_evaluator_metadata() -> None:
    """D-04: every output has agent_name == "qa_evaluator_agent"."""

    outputs = build_all_demo_qa_evaluator_agent_outputs()
    assert outputs, "expected at least one demo output"
    for output in outputs:
        assert output.result.metadata.agent_name == "qa_evaluator_agent"
        assert output.result.metadata.simulated is True
        assert output.result.metadata.run_mode.value == "simulation"


def test_d05_lead_010_is_handled_safely() -> None:
    """D-05: lead_010 (degraded) is handled safely (no exception,
    success=True, output is present)."""

    output = build_demo_qa_evaluator_agent_output("lead_010")
    assert output.lead_id == "lead_010"
    assert output.result.success is True
    # The downstream Email Drafter already produces a conservative draft
    # for lead_010, so the QA evaluator's hard-violation checks should
    # NOT fire and the recommendation should remain REVIEW.
    assert output.recommendation.value in {"Review carefully", "Regenerate suggested"}


def test_d06_qa_output_never_claims_live_research() -> None:
    """D-06: every demo QA output's notes avoid forbidden live-research
    phrases (the deterministic baseline only emits canned text + the
    detected-violation messages, so this is a regression check that
    those canned strings stay clean)."""

    outputs = build_all_demo_qa_evaluator_agent_outputs()
    for output in outputs:
        blob = " ".join(output.qa_notes).lower()
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
            # The deterministic baseline ITSELF uses these phrases as
            # detection targets, but only inside [RISK] / [FIX] notes
            # AFTER a violation has been detected. For the clean demo
            # corpus (the Email Drafter scrubs all of them), no such
            # notes should appear, so the blob should be empty of every
            # forbidden phrase. If any future drafter change leaks a
            # claim, this test will catch it.
            assert forbidden not in blob, (
                f"{output.lead_id}: forbidden phrase present in qa_notes: {forbidden!r}"
            )
